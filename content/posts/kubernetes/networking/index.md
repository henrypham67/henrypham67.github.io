---
title: 'Networking'
date: 2026-03-04T12:28:07+07:00
draft: true
---

<!-- anki
Q: What are the two network namespaces involved in Kubernetes ingress container networking?
A: The node network namespace and the pod network namespace. They are connected via a veth pair.
tags: kubernetes::networking::namespaces

Q: What is the complete iptables chain order for ingress traffic in the node network namespace?
A: eth0 → PREROUTING mangle → PREROUTING nat → Linux Routing → FORWARD → POSTROUTING mangle → POSTROUTING nat → veth (node side)
tags: kubernetes::networking::iptables

Q: What is the complete packet processing order inside the pod network namespace for ingress traffic?
A: veth (pod side) → PREROUTING mangle → Linux Routing → INPUT → Socket → Process
tags: kubernetes::networking::iptables

Q: What role does conntrack play in the node network namespace during ingress traffic?
A: It monitors the FORWARD chain, Linux Routing, and PREROUTING nat to track connection state for stateful packet filtering.
tags: kubernetes::networking::conntrack

Q: What role does conntrack play in the pod network namespace during ingress traffic?
A: It monitors the INPUT chain, Linux Routing, and PREROUTING mangle to track connection state within the pod.
tags: kubernetes::networking::conntrack

Q: Why does ingress traffic pass through PREROUTING nat in the node namespace?
A: PREROUTING nat allows DNAT rules — e.g., kube-proxy rewrites the destination ClusterIP:port to the actual pod IP:port before routing.
tags: kubernetes::networking::nat

Q: Why is the FORWARD chain used during ingress traffic in the node namespace?
A: Packets destined for the pod are not local to the node; they transit through the node, so the kernel applies FORWARD chain rules (e.g., network policy enforcement).
tags: kubernetes::networking::iptables

Q: What is POSTROUTING nat used for in the node namespace on the ingress path?
A: It applies SNAT/MASQUERADE rules after routing decisions — used to rewrite the source address when needed (e.g., for hairpin NAT or NodePort traffic).
tags: kubernetes::networking::nat

Q: What connects the node network namespace to the pod network namespace?
A: A veth (virtual Ethernet) pair — one end in the node namespace, the other end inside the pod namespace.
tags: kubernetes::networking::veth

Q: In Kubernetes, what component typically programs the iptables PREROUTING nat rules for Service routing?
A: kube-proxy (in iptables mode) programs DNAT rules in PREROUTING nat to redirect Service ClusterIP traffic to the backend pod IP.
tags: kubernetes::networking::kube-proxy

C: In the node network namespace, ingress traffic enters via {{c1::eth0}} and first hits the {{c2::PREROUTING mangle}} chain.
C: Kubernetes uses a {{c1::veth pair}} to connect the node network namespace to the pod network namespace.
C: Connection tracking (conntrack) in the node namespace monitors {{c1::FORWARD}}, {{c2::Linux Routing}}, and {{c3::PREROUTING nat}}.
C: Connection tracking (conntrack) in the pod namespace monitors {{c1::INPUT}}, {{c2::Linux Routing}}, and {{c3::PREROUTING mangle}}.
C: In the pod namespace, the final packet delivery order ends with: Socket → {{c1::Process}}.
C: The iptables chain responsible for DNAT (rewriting ClusterIP to pod IP) on ingress is {{c1::PREROUTING nat}}.
C: After the FORWARD chain in the node namespace, traffic passes through {{c1::POSTROUTING mangle}} then {{c2::POSTROUTING nat}} before reaching the veth.
C: The PREROUTING mangle chain runs {{c1::before}} routing decisions and is used for packet marking or TTL modification.
C: In Kubernetes pod networking, each pod lives in its own {{c1::network namespace}}, isolated from the node and other pods.
C: kube-proxy programs iptables rules in {{c1::PREROUTING nat}} to implement Kubernetes Service load balancing.
-->
