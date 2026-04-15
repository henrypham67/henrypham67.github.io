---
title: "Kubernetes pod network namespace: why all containers share one"
date: 2026-04-12T10:00:00+07:00
slug: pod-network-namespace
draft: true
tags: ["kubernetes", "networking", "linux", "namespaces", "containers"]
categories: ["Kubernetes"]
---

## TL;DR

Every container in a Kubernetes pod shares a single Linux network namespace, which means they share one IP address, one loopback interface, and one port space. This is intentional: a pod models a "logical host" — the same way processes on a real host share `eth0`. The mechanism that makes this possible is the **pause container**, a near-empty container that Kubernetes spins up first to own the namespace that all other containers join.

---

## Core concepts and architecture

### Linux network namespaces

A Linux network namespace is a kernel construct that gives a process its own isolated view of the network stack: interfaces, routing tables, iptables rules, and sockets. Containers are just processes running inside namespaces. When you run two containers in separate namespaces, they each get their own `eth0`, their own IP, and they cannot see each other's sockets.

Kubernetes deliberately breaks this isolation *within* a pod. All containers in a pod are joined to a **single** network namespace. From the kernel's perspective, they look like sibling processes on the same host.

### The pause container (a.k.a. the infra/sandbox container)

The mechanism is the **pause container** — a tiny container (a few hundred bytes of compiled C) whose only job is to run `pause()` and sleep forever. Kubelet creates it first when starting any pod. Here's the sequence:

```
kubelet receives pod spec
  │
  ├─ 1. Pull & start pause container
  │       └─ Linux kernel creates a new network namespace for it
  │       └─ CNI plugin attaches veth pair: pod's eth0 ↔ node's vethXXXXXX
  │       └─ Pod IP is assigned to this namespace
  │
  ├─ 2. Start app container A
  │       └─ joined to pause container's net namespace (--network=container:<pause-id>)
  │
  └─ 3. Start app container B
          └─ joined to pause container's net namespace (same)
```

Because A and B join the namespace owned by pause, they share:
- The same IP address
- The same loopback (`lo`)
- The same port space (port conflicts between containers in a pod are possible and real)
- The same routing table and iptables rules

```
┌─────────────────────────────────────────────────────┐
│                       Pod                           │
│                                                     │
│  ┌─────────────┐   ┌─────────────┐  ┌───────────┐  │
│  │  pause      │   │  app-a      │  │  app-b    │  │
│  │  (sleeps)   │   │  :8080      │  │  :9090    │  │
│  └──────┬──────┘   └──────┬──────┘  └─────┬─────┘  │
│         │                 │               │         │
│         └─────────────────┴───────────────┘         │
│                    shared netns                      │
│               IP: 10.244.1.42                       │
│               lo: 127.0.0.1                         │
│               eth0 ──────────────── veth pair ────► │
└─────────────────────────────────────────────────────┘
                                    node eth0
```

### Why pause owns the namespace

If app-a owned the namespace and crashed, the namespace would be destroyed — taking app-b's network stack with it. The pause container decouples namespace lifetime from app container lifetime. Pause almost never crashes. When app-a restarts, it simply re-joins the existing namespace without disrupting app-b or changing the pod IP.

### Which namespaces are shared vs. isolated

| Namespace | Shared within pod? | Notes |
|-----------|-------------------|-------|
| net       | Yes               | same IP, ports, routes |
| ipc       | Yes               | shared memory, semaphores |
| uts       | Yes               | same hostname |
| pid       | No (default)      | can be enabled with `shareProcessNamespace: true` |
| mnt       | No                | each container has its own filesystem |
| user      | No                | separate UIDs |

---

## Key terms glossary

| Term | Definition |
|------|-----------|
| Network namespace | Linux kernel feature giving a process an isolated network stack (interfaces, routes, iptables) |
| Pause container | Kubernetes infra container that owns the pod's namespaces; runs only `pause()` |
| veth pair | Virtual ethernet device connecting a pod namespace to the node's network bridge |
| CNI (Container Network Interface) | Plugin standard (Calico, Cilium, Flannel) responsible for setting up pod networking |
| Pod IP | Single IP address assigned to the shared network namespace, visible to all containers in the pod |
| `hostNetwork: true` | Pod spec flag that makes the pod join the *node's* network namespace instead of its own |
| `shareProcessNamespace` | Pod spec flag to also share the PID namespace among containers |
| Sandbox | CRI term for the pause container + its namespaces; what kubelet creates before app containers |
| ipc namespace | Isolates (or shares) System V IPC objects and POSIX shared memory |
| UTS namespace | Controls hostname and NIS domain name seen by a process |

---

## Essential CLI and tools

```bash
# List all containers in a pod, including the pause container
crictl pods --name <pod-name>
crictl ps --pod <pod-id>

# Inspect which Linux namespaces a container is using
# (find the pause container PID first)
crictl inspect <pause-container-id> | jq '.info.pid'
ls -la /proc/<pid>/ns/

# Enter the network namespace of a running pod
# Useful for running tcpdump or ip commands from inside
kubectl debug -it <pod-name> --image=nicolaka/netshoot --target=<container>

# Check pod IP and interface from inside the pod
kubectl exec -it <pod-name> -c <container> -- ip addr show
kubectl exec -it <pod-name> -c <container> -- ip route

# Confirm two containers in the same pod share the same namespace inode
# Run this on the node; namespace inode should be identical
lsns -t net | grep <pod-network-pattern>

# Capture traffic on a pod's veth interface from the node side
# Find the veth peer index inside the pod, then match on the node
kubectl exec -it <pod> -- cat /sys/class/net/eth0/iflink
ip link | grep <iflink-index>
tcpdump -i veth<XXXX> -nn

# hostNetwork pod debugging — these pods share the node's netns
kubectl get pod <pod-name> -o jsonpath='{.spec.hostNetwork}'
```

---

## Best practices

**1. Never assume port isolation between sidecar containers.**
Containers in the same pod share a port space. If your app container binds `:8080` and your sidecar also tries to bind `:8080`, one will fail. Map ports carefully in multi-container pod specs.

**2. Use `localhost` for intra-pod communication, not pod IPs.**
Containers in the same pod communicate via loopback. Using the pod IP for self-calls adds unnecessary latency and breaks if the IP changes. Wire sidecars (e.g., Envoy, Fluent Bit) to `127.0.0.1:<port>`.

**3. Treat `hostNetwork: true` as a privileged escalation.**
A pod with `hostNetwork: true` joins the node's network namespace — it can see all host interfaces and bind host ports. Restrict this with `PodSecurity` admission (restricted or baseline policy) and audit its usage.

**4. Do not conflate Kubernetes namespaces with Linux network namespaces.**
Kubernetes namespaces (`kubectl get ns`) are API-level organizational boundaries. They do not create Linux network namespaces. Pod isolation is at the pod level, not the Kubernetes namespace level — pods in different Kubernetes namespaces can still talk to each other by default.

**5. Use Network Policies to enforce actual network isolation.**
Because pods share a flat network, any pod can reach any other pod IP by default. NetworkPolicy objects (enforced by CNI plugins like Calico, Cilium) add iptables/eBPF rules to restrict ingress/egress. Without them, your Kubernetes namespace boundary is meaningless for network security.

**6. Pin the pause image version in production.**
Kubelet has a `--pod-infra-container-image` flag (or `pauseImage` in containerd config). In air-gapped clusters or strict registry environments, explicitly pin this to avoid surprise pulls or version drift.

**7. Be aware of pause container resource consumption.**
Each pod has a pause container. At scale (thousands of pods per node), pause containers are memory-visible. They consume minimal CPU but do occupy a PID and file descriptors. They are counted in node's pod capacity.

---

## Common issues and troubleshooting

**Issue 1: Port conflict between sidecar and app container**
- **Symptom:** One container fails to start with `bind: address already in use`; `kubectl describe pod` shows `CrashLoopBackOff` on one container
- **Root cause:** Two containers in the same pod attempted to bind the same port; because they share a network namespace, there is only one port space
- **Fix:** Change one container's port. If using Envoy as a sidecar, check that its admin port (default 9901) doesn't conflict with app ports

**Issue 2: DNS resolution works from one container but not another**
- **Symptom:** `curl service-name` works in container A, fails in container B (both in the same pod)
- **Root cause:** The containers share the network namespace (same `/etc/resolv.conf`) but have separate mount namespaces — if container B overrides `/etc/resolv.conf` via a volume mount, it won't use the pod's DNS config
- **Fix:** Inspect `kubectl exec -c <container-b> -- cat /etc/resolv.conf`; remove any volume mounts overriding it

**Issue 3: Pod IP changes unexpectedly**
- **Symptom:** External systems lose connection to a pod after it restarts; pod IP changed
- **Root cause:** The pause container was also restarted (pod deletion + recreation, or node eviction). The pause container owns the namespace and the IP — a new pause = a new IP
- **Fix:** Never target pod IPs directly. Use Services for stable endpoints. If you need stable IPs, use StatefulSets with headless Services

**Issue 4: `tcpdump` on node captures unexpected pod traffic**
- **Symptom:** Traffic destined for pod A is visible on pod B's veth
- **Root cause:** Misconfigured CNI or ARP table corruption causing packets to be delivered to the wrong veth pair
- **Fix:** Inspect ARP tables (`ip neigh`), flush stale entries, check CNI plugin logs. On Calico, `calicoctl node status` reveals BGP/route sync issues

**Issue 5: Shared IPC namespace causing subtle memory bugs**
- **Symptom:** POSIX shared memory or System V semaphores from one container are visible in another; unexpected cross-container state
- **Root cause:** IPC namespace is shared by default in a pod, just like net. Containers can access each other's shared memory segments
- **Fix:** If this is unintended, move containers to separate pods. If intentional (high-throughput IPC), document it explicitly

**Issue 6 (subtle): `hostNetwork` pod interfering with node-level networking**
- **Symptom:** A `hostNetwork: true` pod's process binds a port that conflicts with a node daemon (e.g., `kube-proxy`, `kubelet`, or `node-exporter`)
- **Root cause:** The pod shares the node's network namespace and has full access to all host interfaces and ports
- **Fix:** Audit all `hostNetwork: true` pods; use PodSecurity policies/admission to restrict; validate port ranges

---

## Interview-ready knowledge

**Q: Why do containers in a pod share a network namespace instead of each having their own?**
The pod is designed as a "co-located host" abstraction — think of it like a VM where multiple processes share an IP. Shared networking enables tight coupling for sidecar patterns (app + proxy, app + log shipper) without requiring any service discovery or external IPs. It matches how processes actually communicate on a traditional host.

**Q: What is the pause container and why does it exist?**
The pause container is a minimal infra container that Kubernetes starts first in every pod. Its only job is to run `pause()` (a syscall that puts a process to sleep until a signal) and hold the Linux namespaces (net, ipc, uts) that app containers join. It decouples namespace lifetime from app container lifetime — if an app container crashes and restarts, the network namespace (and pod IP) persists because pause is still running.

**Q: What happens to the pod IP when a container in the pod crashes?**
Nothing — the pod IP survives. The IP is tied to the network namespace owned by the pause container. As long as the pause container is running (which it almost always is, since it's trivially simple), the namespace and IP persist across app container restarts.

**Q: Can two containers in the same pod communicate via `localhost`? What about two pods?**
Yes for intra-pod: shared network namespace means `127.0.0.1` is the same loopback for all containers. No for inter-pod: different pods have different network namespaces and different IPs. They communicate via the cluster network using pod IPs or Service ClusterIPs, not localhost.

**Q: A new engineer deploys a sidecar that crashes immediately. `kubectl logs` shows "address already in use". What happened?**
The sidecar is trying to bind a port already occupied by the main container (or another sidecar). Since all containers in a pod share one network namespace, there is a single port space — the same constraint as two processes on the same Linux host.

**Q: How would you capture HTTP traffic between a sidecar and the main container inside a pod?**
Since they share a network namespace, all their traffic goes over the loopback interface. From the node, you can't tap this with a veth capture (veth only sees traffic leaving the namespace). Instead: `kubectl exec -c <container> -- tcpdump -i lo -nn port 8080` or use `kubectl debug` with a netshoot image and `--target` flag to enter the namespace.

**Q: What is `hostNetwork: true` and when would you use it?**
It makes the pod join the node's network namespace instead of creating its own. The pod gets the node's IP and can bind node-level ports. Legitimate uses: node monitoring agents that need to see host network interfaces (e.g., `node-exporter`, `Cilium` agent), or performance-sensitive workloads that can't afford the veth overhead. It's a privileged escalation and should be restricted to trusted workloads.

**Q: How does a CNI plugin know when to set up pod networking?**
Kubelet calls the CRI (e.g., containerd) to create the sandbox (pause container). Containerd invokes the configured CNI plugin, passing the pod's network namespace path (e.g., `/var/run/netns/cni-XXXX`). The CNI plugin then creates the veth pair, moves one end into the pod namespace, assigns the IP via IPAM, and sets up routes. This all happens before app containers start.

---

## Further reading

1. **[The Almighty Pause Container — Ian Lewis](https://www.ianlewis.org/en/almighty-pause-container)** — The canonical deep dive on why the pause container exists, written by a Kubernetes contributor. Essential reading.

2. **[Kubernetes network stack fundamentals — Red Hat](https://www.redhat.com/en/blog/kubernetes-pod-network-communications)** — How containers inside a pod communicate, with diagrams covering veth pairs, bridges, and iptables.

3. **[Understanding Kubernetes Networking: Pods — Mark Betz (Google Cloud)](https://medium.com/google-cloud/understanding-kubernetes-networking-pods-7117dd28727)** — Thorough walkthrough of pod networking internals with Linux namespace mechanics explained clearly.

4. **[Kubernetes Docs: Pods](https://kubernetes.io/docs/concepts/workloads/pods/)** — Official spec on pod semantics, shared namespaces, and the pod networking model.

5. **[Linux namespaces man page](https://man7.org/linux/man-pages/man7/namespaces.7.html)** — Ground truth for all seven Linux namespace types; understand these and Kubernetes networking clicks into place.
