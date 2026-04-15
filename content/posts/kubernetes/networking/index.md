---
title: 'Networking'
date: 2026-03-04T12:28:07+07:00
draft: true
flashcards:
  - q: "What are the two network namespaces involved in Kubernetes ingress container networking?"
    a: "The node network namespace and the pod network namespace, connected via a veth pair."
  - q: "What is the complete iptables chain order for ingress traffic in the node network namespace?"
    a: "eth0 → PREROUTING mangle → PREROUTING nat → Linux Routing → FORWARD → POSTROUTING mangle → POSTROUTING nat → veth (node side)."
  - q: "What is the complete packet processing order inside the pod network namespace for ingress traffic?"
    a: "veth (pod side) → PREROUTING mangle → Linux Routing → INPUT → Socket → Process."
  - q: "What role does conntrack play in the node network namespace during ingress traffic?"
    a: "It monitors the FORWARD chain, Linux Routing, and PREROUTING nat to track connection state for stateful packet filtering."
  - q: "Why does ingress traffic pass through PREROUTING nat in the node namespace?"
    a: "To allow DNAT rules where kube-proxy rewrites the destination Service ClusterIP to the actual pod IP before routing."
  - q: "Why is the FORWARD chain used during ingress traffic in the node namespace?"
    a: "Because packets destined for the pod are not local to the node; they transit through the node, and the kernel applies FORWARD rules for network policy enforcement."
  - q: "What connects the node network namespace to the pod network namespace?"
    a: "A veth (virtual Ethernet) pair—one end in the node namespace and the other end inside the pod namespace."
  - q: "Which component typically programs the iptables PREROUTING nat rules for Service routing in Kubernetes?"
    a: "kube-proxy (in iptables mode) programs DNAT rules in PREROUTING nat to redirect Service ClusterIP traffic to backend pod IPs."
  - q: "In the pod namespace, what are the final steps of packet delivery for ingress traffic?"
    a: "INPUT chain → Socket → Application Process."
  - q: "What is POSTROUTING nat used for in the node namespace on the ingress path?"
    a: "It applies SNAT/MASQUERADE rules after routing decisions, often used for NodePort traffic or hairpin NAT."
quiz:
  title: "Kubernetes Ingress Networking Quiz"
  questions:
    - q: "Which iptables chain is responsible for performing the DNAT from a Service ClusterIP to a Pod IP?"
      options:
        - "FORWARD"
        - "INPUT"
        - "PREROUTING nat"
        - "POSTROUTING nat"
      correct: 2
    - q: "What virtual device connects a Pod's network namespace to the Node's network namespace?"
      options:
        - "tun/tap bridge"
        - "veth pair"
        - "overlay tunnel"
        - "loopback interface"
      correct: 1
    - q: "In the node namespace, why does traffic for a Pod pass through the FORWARD chain instead of the INPUT chain?"
      options:
        - "Because it is local traffic to the node"
        - "Because the Pod IP is not assigned to a node interface, making it transit traffic"
        - "Because the Pod is running in the host network namespace"
        - "Because the INPUT chain is disabled in Kubernetes"
      correct: 1
    - q: "Which component tracks the state of connections to allow return traffic through the firewall?"
      options:
        - "kube-proxy"
        - "CoreDNS"
        - "conntrack"
        - "etcd"
      correct: 2
    - q: "If you want to modify the TTL of a packet before any routing decisions are made, which chain would you use?"
      options:
        - "PREROUTING mangle"
        - "POSTROUTING mangle"
        - "FORWARD"
        - "INPUT"
      correct: 0
---
