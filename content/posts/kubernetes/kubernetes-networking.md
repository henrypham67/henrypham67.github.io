†---
title: "Kubernetes networking: everything you need to know"
date: 2026-04-11T00:00:00+07:00
slug: kubernetes-networking
draft: true
tags: ["kubernetes", "networking", "cni"]
categories: ["Kubernetes"]
---

## TL;DR

Kubernetes networking is a layered system built on Linux primitives — network namespaces, veth pairs, iptables/eBPF — that guarantees every Pod gets a unique routable IP and can reach any other Pod without NAT. A CNI plugin owns the pod-level wiring; kube-proxy (or a CNI replacement) owns the Service-to-Pod translation; CoreDNS owns name resolution. Understanding which layer handles which concern is the key to diagnosing 90% of cluster network issues.

---

## Core concepts and architecture

### The four networking problems Kubernetes solves

Kubernetes defines a flat network model with four distinct communication planes, each handled differently:

```
1. Container-to-container   → shared Pod network namespace (localhost)
2. Pod-to-Pod               → CNI plugin (same node: bridge; cross-node: routes/tunnels)
3. Pod-to-Service           → kube-proxy NAT rules (iptables / IPVS / eBPF)
4. External-to-Service      → NodePort, LoadBalancer, or Ingress controller
```

The core guarantee: **every Pod IP is routable cluster-wide, no NAT**. This is what the CNI spec enforces.

### Pod networking: veth pairs and the node bridge

When a Pod is scheduled, the container runtime calls the CNI plugin, which:

1. Creates a **network namespace** for the Pod (`/var/run/netns/<id>`)
2. Creates a **veth pair** — one end (`eth0`) goes inside the Pod namespace, the other (`vethXXXX`) stays on the node
3. Attaches the node-side veth to a **bridge** (e.g., `cni0` for flannel, or directly routes it for Calico)
4. Assigns an IP from the node's Pod CIDR and sets up routes

```
Pod namespace          Node namespace
┌──────────────┐      ┌──────────────────────────────┐
│ eth0         │      │ vethXXXX ──── cni0 (bridge)   │
│ 10.244.1.5   │◄────►│                               │
│ /24 route    │      │  routes: 10.244.0.0/16 → eth0 │
└──────────────┘      └──────────────────────────────┘
```

Cross-node Pod-to-Pod traffic goes through either:
- **Overlay** (VXLAN/Geneve): CNI encapsulates the packet, tunnels it, decapsulates on the other node. Simple to set up, ~10% overhead.
- **Underlay (BGP)**: Calico distributes per-node Pod CIDR routes via BGP. No encapsulation, lower latency, requires the underlying network to carry Pod routes.

### Services and kube-proxy

A Service gets a **ClusterIP** — a virtual IP that exists only in iptables/IPVS rules, not on any interface. kube-proxy runs on every node and watches the API server; when Endpoints change, it updates the rules.

**iptables mode** (default pre-1.29 on many distros):

```
Packet to ClusterIP:port
  → iptables PREROUTING
  → KUBE-SERVICES chain
  → KUBE-SVC-XXXX (random selection via statistic match)
  → KUBE-SEP-YYYY (DNAT to Pod IP:targetPort)
```

The problem: rules are evaluated linearly. A cluster with 10,000 Services generates ~40,000 iptables rules. Each new connection traverses all of them.

**IPVS mode**: kube-proxy programs a kernel hash table instead. O(1) lookup regardless of Service count. Enable with `--proxy-mode=ipvs` on kube-proxy. Requires `ip_vs` kernel modules.

**eBPF mode (Cilium kube-proxy replacement)**: bypasses iptables entirely. Attaches BPF programs at the TC (traffic control) hook on each interface. Constant-time lookups, L7 visibility, no conntrack table pressure.

### CoreDNS and service discovery

CoreDNS runs as a Deployment in `kube-system` and is the cluster DNS. The `kubelet` configures each Pod's `/etc/resolv.conf` with:

```
nameserver 10.96.0.10        # CoreDNS ClusterIP
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

**FQDN resolution order for `my-service`:**
1. `my-service.default.svc.cluster.local` → hit (returns ClusterIP)

The `ndots:5` setting means any name with fewer than 5 dots gets the search list appended first — this causes extra DNS round-trips for external names like `api.stripe.com` (which gets tried as `api.stripe.com.default.svc.cluster.local` first). Fix: add a trailing dot or reduce `ndots`.

### Ingress and Gateway API

Ingress is a Layer-7 reverse proxy configuration that an **Ingress controller** (nginx, Traefik, AWS ALB controller) reads and implements. The controller runs as a Pod, watches Ingress objects, and reconfigures itself dynamically.

The **Gateway API** (GA in Kubernetes 1.31) is the successor to Ingress. It separates concerns:
- `GatewayClass` — infrastructure type (defined by cluster admin)
- `Gateway` — listener config (managed by network team)
- `HTTPRoute` — routing rules (managed by app teams)

This enables multi-team ownership of routing without giving everyone access to a monolithic Ingress.

---

## Key terms glossary

| Term | Definition |
|------|------------|
| **CNI** | Container Network Interface — a spec and plugin model for configuring Pod networking. kubelet calls the CNI binary on pod create/delete. |
| **Pod CIDR** | The IP range allocated to a node for Pod IPs (e.g., `10.244.1.0/24`). Each node gets a non-overlapping slice of the cluster CIDR. |
| **ClusterIP** | A virtual IP assigned to a Service. Exists only in iptables/IPVS/eBPF rules — not on any real interface. Routable only within the cluster. |
| **NodePort** | Exposes a Service on a static port on every node's IP. kube-proxy opens that port and forwards to the Service. Range: 30000–32767 by default. |
| **veth pair** | A virtual Ethernet pair — packets sent into one end come out the other. Used to connect a Pod namespace to the node namespace. |
| **Overlay network** | Encapsulates Pod traffic inside UDP/VXLAN packets to traverse the underlay. Avoids requiring the physical network to know Pod routes. |
| **IPVS** | IP Virtual Server — a Linux kernel load balancer using hash tables. kube-proxy can use it instead of iptables for O(1) Service lookups. |
| **Endpoint / EndpointSlice** | The list of Pod IPs backing a Service. EndpointSlices (default since 1.21) shard large endpoint lists for efficiency. |
| **NetworkPolicy** | A namespaced resource that controls ingress/egress traffic to Pods using label selectors. Enforced by the CNI plugin, not kube-proxy. |
| **CoreDNS** | The cluster DNS server. Resolves `<service>.<namespace>.svc.cluster.local` to ClusterIPs. Configured via a `Corefile` ConfigMap. |
| **Headless Service** | A Service with `clusterIP: None`. DNS returns Pod IPs directly instead of a VIP — used for StatefulSets and direct Pod addressing. |
| **kube-proxy** | A DaemonSet that programs iptables/IPVS rules on each node so traffic to ClusterIPs gets NATted to real Pod IPs. |
| **eBPF** | Extended Berkeley Packet Filter — kernel bytecode that runs at hook points in the network stack. Used by Cilium to replace iptables with faster, programmable data planes. |
| **MTU** | Maximum Transmission Unit — the largest packet size on a link. Overlay encapsulation adds headers, reducing effective MTU. Misconfigured MTU causes silent packet drops for large payloads. |

---

## Essential CLI and tools

### Inspect Service endpoints and routing

```bash
# Show all endpoints backing a Service — verify pods are selected
kubectl get endpointslices -l kubernetes.io/service-name=my-service -n my-ns

# Describe a Service to see selector, ports, and session affinity
kubectl describe svc my-service -n my-ns
```

### Debug DNS resolution

```bash
# Spin up a debug pod with DNS tools (no ephemeral container needed)
kubectl run dnsutils --image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.3 \
  --restart=Never -it --rm -- /bin/bash

# Inside: test FQDN resolution
nslookup my-service.my-ns.svc.cluster.local
nslookup kubernetes.default.svc.cluster.local

# Check CoreDNS is healthy
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=50
```

### Check iptables rules (kube-proxy in iptables mode)

```bash
# On the node — list all kube-proxy DNAT rules for a Service
iptables-save | grep <ClusterIP>

# Count total kube-proxy rules (indicator of scale problem)
iptables-save | grep -c KUBE
```

### Network Policy debugging

```bash
# List all NetworkPolicies in a namespace
kubectl get networkpolicies -n my-ns -o wide

# Check if a policy is blocking traffic — use Cilium's editor
# or test with a temporary allow-all policy and narrow it down
kubectl exec -it debug-pod -- curl -v http://my-service:8080
```

### Packet capture on a Pod

```bash
# Find the veth interface on the node for a given Pod
NODE=$(kubectl get pod my-pod -o jsonpath='{.spec.nodeName}')
POD_IP=$(kubectl get pod my-pod -o jsonpath='{.status.podIP}')

# SSH to node, then:
ip route get $POD_IP          # shows which veth it uses
tcpdump -i vethXXXXX -n      # capture pod traffic from node side

# Or use kubectl debug for a quick ephemeral packet capture
kubectl debug node/$NODE -it --image=nicolaka/netshoot -- bash
```

### Cilium-specific (if Cilium is your CNI)

```bash
# Check Cilium agent health on a node
kubectl exec -n kube-system ds/cilium -- cilium status

# Show policy enforcement for a specific endpoint
kubectl exec -n kube-system ds/cilium -- cilium endpoint list

# Real-time flow visibility (requires Hubble)
hubble observe --namespace my-ns --follow
hubble observe --to-pod my-ns/my-pod --verdict DROPPED
```

---

## Best practices

**1. Replace kube-proxy with a CNI eBPF data plane at scale.**
Above ~500 Services, iptables rule churn causes measurable connection setup latency and high CPU on kube-proxy. Switch to Cilium's kube-proxy replacement (`kubeProxyReplacement: true`) or Calico's eBPF mode. Both provide O(1) lookups and eliminate conntrack table pressure.

**2. Default-deny NetworkPolicy in every namespace.**
Without a NetworkPolicy, all Pods can reach all other Pods cluster-wide. Start with a deny-all and whitelist explicitly:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: my-ns
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
```

**3. Size CoreDNS replicas to traffic, not cluster size.**
The default 2 CoreDNS replicas will saturate under high DNS load (e.g., a Java app doing DNS per connection). Monitor `coredns_dns_requests_total` in Prometheus. Rule of thumb: 1 CoreDNS core per 1,000 Pods.

**4. Set `ndots: 2` for workloads making external DNS calls.**
The default `ndots:5` causes 5 failed local search lookups before resolving `api.stripe.com`. Set `dnsConfig.options: [{name: ndots, value: "2"}]` per-Pod or cluster-wide via CoreDNS `rewrite`.

**5. Avoid NodePort for production traffic.**
NodePort ties you to node IP stability and requires external load balancers to know all node IPs. Use a LoadBalancer Service (cloud LB) or Ingress/Gateway API for external traffic. Reserve NodePort for debugging.

**6. Pick your CNI before day one — migration is painful.**
Changing CNI post-install requires re-creating all Pods (the entire cluster if you want zero downtime). Evaluate on: cluster size, required features (L7 policy, encryption, observability), and operational complexity. In 2025–2026 the default choice for new production clusters is Cilium.

**7. Configure MTU explicitly for overlay networks.**
VXLAN adds 50 bytes of overhead. If your underlay MTU is 1500, set CNI MTU to 1450. Misconfigured MTU causes silent packet drops on large requests (e.g., 1MB API responses succeed but 2MB ones time out). Verify with: `kubectl exec <pod> -- ping -M do -s 1450 <other-pod-ip>`.

**8. Use Headless Services for StatefulSets.**
StatefulSets need stable per-Pod DNS (`pod-0.my-svc.ns.svc.cluster.local`). A regular ClusterIP Service load-balances randomly — you lose the ability to address specific replicas. Headless Services (`clusterIP: None`) make DNS return individual Pod IPs.

---

## Common issues and troubleshooting

### 1. Pod can't reach another Pod across nodes

- **Symptom:** `curl` from Pod A to Pod B IP succeeds on same node, fails cross-node. No error in NetworkPolicy.
- **Root cause:** CNI route or tunnel is broken. Common causes: VXLAN UDP port 8472 blocked by a firewall/security group; BGP peering dropped (Calico); MTU mismatch causing silent drops.
- **Fix:**
  ```bash
  # From node, check if VXLAN traffic is being dropped
  tcpdump -i eth0 udp port 8472

  # For Calico BGP: check peer status
  kubectl exec -n kube-system ds/calico-node -- calicoctl node status

  # Verify routes exist on the node
  ip route | grep 10.244
  ```

### 2. DNS lookup returning SERVFAIL intermittently

- **Symptom:** Pods see sporadic DNS failures, especially under load. `nslookup` sometimes times out.
- **Root cause A:** CoreDNS CPU throttled — check Pod resource limits. CoreDNS uses a lot of CPU under high QPS and will drop queries if throttled.
- **Root cause B:** conntrack table exhaustion. UDP DNS queries create conntrack entries; a saturated table causes new UDP packets to be silently dropped.
- **Fix:**
  ```bash
  # Check CoreDNS CPU usage
  kubectl top pod -n kube-system -l k8s-app=kube-dns

  # Check conntrack table on the node
  cat /proc/sys/net/netfilter/nf_conntrack_count
  cat /proc/sys/net/netfilter/nf_conntrack_max

  # Increase table size (temporary, apply via sysctl DaemonSet for permanence)
  sysctl -w net.netfilter.nf_conntrack_max=524288
  ```

### 3. Service ClusterIP unreachable from within the cluster

- **Symptom:** `curl http://<ClusterIP>:<port>` hangs or connection refused, but `curl http://<PodIP>:<port>` works.
- **Root cause:** kube-proxy is not running or crashed on the node, so iptables DNAT rules are missing.
- **Fix:**
  ```bash
  kubectl get pods -n kube-system -l k8s-app=kube-proxy
  kubectl logs -n kube-system <kube-proxy-pod>

  # On the node, verify the DNAT rule exists
  iptables-save | grep <ClusterIP>
  ```

### 4. Ingress 503 / upstream not found

- **Symptom:** Ingress returns 503. The Service and Pods are healthy.
- **Root cause A:** Ingress `serviceName` references a non-existent Service or wrong port name.
- **Root cause B:** Ingress controller Pods can't reach the backend Pods due to a NetworkPolicy blocking traffic from the `ingress-nginx` namespace.
- **Fix:**
  ```bash
  # Check Ingress controller logs
  kubectl logs -n ingress-nginx deploy/ingress-nginx-controller --tail=100

  # Verify endpoints are populated
  kubectl get endpoints <service-name> -n <namespace>

  # Add a NetworkPolicy allowing ingress from the ingress-nginx namespace
  ```

### 5. Subtle: SNAT masking the real client IP behind NodePort

- **Symptom:** Application logs show node IP as the client IP instead of the real client IP for NodePort traffic.
- **Root cause:** kube-proxy SNATs traffic when it hairpins across nodes (to ensure return packets can route back). `externalTrafficPolicy: Cluster` (the default) always SNATs.
- **Fix:** Set `externalTrafficPolicy: Local` on the Service. This routes traffic only to Pods running on the receiving node (no SNAT, real client IP preserved), at the cost of potentially uneven load distribution.

---

## Interview-ready knowledge

**Q: Walk me through what happens when a Pod sends a packet to a ClusterIP.**

The Pod's `eth0` sends the packet to its default gateway (the node-side bridge). Before the packet is routed, iptables PREROUTING hits the `KUBE-SERVICES` chain, which matches the ClusterIP:port. A probabilistic rule selects one of the backend Pods and DNATs the destination to that Pod's IP:targetPort. The packet then routes normally to the selected Pod — on the same node via the bridge, or cross-node via CNI routes/tunnels. The response is SNATed back by conntrack tracking.

**Q: What's the difference between iptables mode and IPVS mode in kube-proxy?**

In iptables mode, kube-proxy writes one rule per Service-Endpoint combination into the kernel's netfilter tables. Rules are evaluated linearly — O(n) per packet. At 10,000 Services, every new connection traverses tens of thousands of rules. IPVS mode replaces this with a kernel-space load balancer using hash tables, giving O(1) lookups regardless of Service count. IPVS also supports more load balancing algorithms (round-robin, least-conn, etc.) and reduces CPU on kube-proxy. The trade-off: IPVS requires `ip_vs` kernel modules and the `ipset` tool.

**Q: Why would you choose Cilium over Calico for a new production cluster?**

Cilium's eBPF data plane replaces iptables entirely, giving O(1) Service routing, no conntrack table pressure, and built-in L7 visibility without a sidecar proxy. At scale (>500 Services, >1,000 nodes) the performance and operational advantages are significant. Cilium also ships with Hubble for real-time network flow observability — something you'd otherwise need a service mesh for. Calico is still the right choice for simpler clusters where BGP routing is already established and eBPF operational overhead is undesirable.

**Q: What does `ndots:5` mean and why does it cause problems?**

`ndots:5` instructs the resolver to treat any name with fewer than 5 dots as "unqualified" and append the search domains before trying it as an absolute name. So `api.stripe.com` (2 dots) gets tried as `api.stripe.com.default.svc.cluster.local`, `api.stripe.com.svc.cluster.local`, and `api.stripe.com.cluster.local` — all failing — before it's tried as-is. This adds 3–5 extra DNS round-trips to every external call. Fix by setting `ndots: 2` in Pod `dnsConfig`, or appending a trailing dot to FQDNs in application config (`api.stripe.com.`).

**Q: A deployment has 3 replicas, the Service looks healthy, but one Pod never receives traffic. What do you check?**

First check `kubectl get endpoints <svc>` to confirm all 3 Pod IPs are listed. If an IP is missing, the Pod's readiness probe is failing — check `kubectl describe pod`. If all 3 are in endpoints, check for a NetworkPolicy blocking ingress to that specific Pod (maybe a label mismatch). Then check if the Pod is on a node with a broken CNI route — test with a direct `curl <pod-ip>` from another Pod. Finally, check if `sessionAffinity: ClientIP` is set on the Service, which would pin clients to specific Pods.

**Q: What is a Headless Service and when do you need one?**

A Headless Service has `clusterIP: None`. Instead of returning a VIP, DNS returns A records for all backing Pod IPs directly. This lets clients do their own load balancing or address specific Pods. StatefulSets require Headless Services because each Pod needs a stable DNS name (`pod-0.my-headless-svc.ns.svc.cluster.local`). Also used with client-side load balancing (gRPC, database clients) where the app needs to know all replica IPs, not just one VIP.

**Q: How does Gateway API differ from Ingress, and why should you care?**

Ingress is a single resource that mixes infrastructure config (what listener to create) with routing rules (what traffic goes where). In practice this forces cluster admins and app developers to share the same resource, causing either over-permission or toil. Gateway API splits this into `GatewayClass` (infra type, cluster-admin), `Gateway` (listener config, network team), and `HTTPRoute`/`GRPCRoute` (routing rules, app team). This matches real org structures. Gateway API also supports TCP/UDP routes, traffic splitting with weights, header manipulation, and TLS passthrough natively — things that required vendor annotations in Ingress.

---

## Further reading

1. **[Kubernetes Networking Docs — Cluster Networking](https://kubernetes.io/docs/concepts/cluster-administration/networking/)** — The canonical spec for the network model. Start here to understand what guarantees Kubernetes actually makes vs. what it delegates to the CNI.

2. **[Cilium Network Reference Documentation](https://docs.cilium.io/en/stable/)** — The most comprehensive practical guide to eBPF-based Kubernetes networking. Even if you don't run Cilium, the conceptual sections on eBPF, conntrack, and the data plane are worth reading.

3. **[Saifeddine Rajhi — Kube-Proxy and CNI internals](https://seifrajhi.github.io/blog/kubernetes-networking/)** — Goes deep on how CNI and kube-proxy interact at the packet level, with iptables trace examples.

4. **[Gateway API docs](https://gateway-api.sigs.k8s.io/)** — The SIG-Network site for the Ingress successor. Includes migration guides from Ingress and conformance test results per controller.

5. **[Brendan Gregg — Linux Performance Tools](https://www.brendangregg.com/linuxperf.html)** — Not Kubernetes-specific, but understanding `perf`, `bpftrace`, and `tcpdump` at the Linux layer is essential when CNI-level tools don't give you enough signal.
