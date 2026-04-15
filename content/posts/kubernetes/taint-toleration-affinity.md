---
title: "Kubernetes Taints, Tolerations, and Affinity: Everything You Need to Know"
date: 2026-04-20T14:30:00+07:00
slug: taint-toleration-affinity
draft: true
tags: ["kubernetes", "scheduling", "high-availability"]
categories: ["Kubernetes"]
flashcards:
  - q: "What is the key difference between nodeSelector and Node Affinity?"
    a: "Node Affinity is more expressive, supporting operators (In, NotIn, Exists) and 'Preferred' rules with weights, while nodeSelector is a simple, mandatory key-value match."
  - q: "How do NoSchedule and NoExecute taints differ in their treatment of existing pods?"
    a: "NoSchedule allows existing pods to stay running on the node, whereas NoExecute evicts any existing pods that do not have a matching toleration."
  - q: "If a node has multiple taints, what must a pod have to be scheduled there?"
    a: "The pod must have a matching toleration for every single taint on the node."
  - q: "What is the purpose of the 'tolerationSeconds' field in a pod specification?"
    a: "It is used with the NoExecute effect to specify how many seconds a pod can stay on a tainted node (e.g., during a network blip) before being evicted."
  - q: "Why is Pod Anti-Affinity critical for stateful clusters like databases?"
    a: "It guarantees that replicas are spread across different nodes or zones, ensuring a single failure doesn't take down multiple members of a quorum."
quiz:
  title: "Kubernetes Scheduling Constraints Quiz"
  questions:
    - q: "Which affinity type will keep a pod in 'Pending' if no matching nodes are found?"
      options:
        - "preferredDuringSchedulingIgnoredDuringExecution"
        - "requiredDuringSchedulingIgnoredDuringExecution"
        - "requiredDuringSchedulingRequiredDuringExecution"
        - "preferredDuringExecutionIgnoredDuringScheduling"
      correct: 1
    - q: "Which taint effect is the most aggressive, affecting both new and running pods?"
      options:
        - "NoSchedule"
        - "PreferNoSchedule"
        - "NoExecute"
        - "EvictAll"
      correct: 2
    - q: "What happens if a pod only tolerates 1 out of 2 'NoSchedule' taints on a node?"
      options:
        - "It will be scheduled normally"
        - "It will be scheduled but with lower priority"
        - "It will not be scheduled on that node"
        - "It will be scheduled only if no other nodes are available"
      correct: 2
    - q: "Which topologyKey is commonly used to ensure pods are spread across different Availability Zones?"
      options:
        - "kubernetes.io/hostname"
        - "topology.kubernetes.io/region"
        - "topology.kubernetes.io/zone"
        - "node.kubernetes.io/instance-type"
      correct: 2
---

## TL;DR

Kubernetes scheduling constraints (Taints, Tolerations, and Affinity) allow you to control pod placement across your cluster. Taints **repel** pods from nodes, while Affinity **attracts** them, providing the granular control needed for workload isolation, specialized hardware utilization, and high availability.

---

## Core concepts and architecture

Pod scheduling in Kubernetes isn't just about finding a node with enough CPU and memory. In real-world projects, you need to ensure that database pods land on SSD-backed nodes, machine learning jobs use GPU-equipped instances, and production workloads don't share physical hardware with development tasks.

### The Repel/Attract Mental Model

1.  **Taints & Tolerations (Repulsion):** Applied to **Nodes**. They define a "Keep Out" policy. A node with a taint will not accept any pod unless that pod has a matching **Toleration**.
2.  **Node Affinity (Attraction):** Applied to **Pods**. They define a "I want to go there" policy based on node labels.
3.  **Pod Anti-Affinity (Isolation):** Applied to **Pods**. They define a "I don't want to be near them" policy, ensuring replicas are spread across different nodes or zones for high availability.

### Internals: How the Scheduler Decides

When the `kube-scheduler` sees a new pod, it goes through a filtering and scoring process:
- **Filtering:** It removes nodes that don't satisfy the pod's requirements (e.g., Taints without matching Tolerations, or Required Node Affinity).
- **Scoring:** It ranks the remaining nodes based on "Preferred" rules (e.g., Preferred Node Affinity weights). The node with the highest score wins.

```ascii
+-------------+      1. Filtering      +-----------------+
|   New Pod   | ----------------------> | Candidate Nodes |
+-------------+   (Taints, Required    +-----------------+
                  Affinity/Selectors)          |
                                               | 2. Scoring
                                               | (Preferred Affinity,
                                               | Resource Balance)
                                               v
                                       +-----------------+
                                       |  Selected Node  |
                                       +-----------------+
```

---

## Key terms glossary

| Term | Definition |
|------|-----------|
| **Taint** | A node property that discourages or prevents pods from being scheduled on it. |
| **Toleration** | A pod property that allows it to "tolerate" a specific taint and be scheduled on a tainted node. |
| **Node Affinity** | A set of rules that defines which nodes a pod is eligible to be scheduled on based on node labels. |
| **Pod Anti-Affinity** | Rules that prevent pods from being scheduled on the same node or in the same topology domain (e.g., zone) as other pods. |
| **NoSchedule** | A taint effect that prevents new pods from being scheduled but allows existing pods to stay. |
| **NoExecute** | The strongest taint effect; prevents new pods and evicts existing pods that don't have the toleration. |
| **topologyKey** | A node label key (e.g., `kubernetes.io/hostname`) used to define the domain for pod affinity/anti-affinity. |
| **IgnoredDuringExecution** | Specifies that if node labels change after scheduling, the pod will not be evicted (standard for most affinity rules). |

---

## Essential CLI and tools

### 1. Tainting a Node
Use this to reserve a node for specific workloads or prepare it for maintenance.

```bash
# Add a taint: key=value:effect
kubectl taint nodes node-01 dedicated=special-user:NoSchedule

# Remove a taint (note the minus sign)
kubectl taint nodes node-01 dedicated=special-user:NoSchedule-
```

### 2. Inspecting Taints and Labels
Before setting up affinity, you must know what you're working with.

```bash
# Describe node to see current taints
kubectl describe node node-01 | grep Taints

# List node labels to use in affinity rules
kubectl get nodes --show-labels
```

### 3. Debugging Scheduling Failures
If a pod is stuck in `Pending`, check the events.

```bash
# Look for 'FailedScheduling' events
kubectl describe pod <pod-name>
```

---

## Best practices

### 1. The "Strict Isolation" Pattern (Taint + Affinity)
To ensure a node pool is **exclusive** to a specific team or environment, use both:
- **Taint the nodes:** Prevents random pods from landing there.
- **Node Affinity on pods:** Ensures the intended pods actually target these nodes and don't land elsewhere.

### 2. Prefer `NoSchedule` for Reservations
Unless you need to immediately kick pods off a node (e.g., for urgent security patching), use `NoSchedule`. `NoExecute` can cause unexpected cascading failures if many pods are evicted simultaneously.

### 3. Use `Preferred` Affinity for General Spreading
Don't over-constrain your cluster with `Required` affinity. If you have 3 zones but require 4 replicas to be in different zones, one pod will stay `Pending` forever. Use `Preferred` with a high weight instead.

### 4. Strategic `topologyKey`
For High Availability:
- Use `kubernetes.io/hostname` to spread pods across **nodes**.
- Use `topology.kubernetes.io/zone` to spread pods across **availability zones**.

### 5. Standardize Labels
Establish a cluster-wide labeling convention (e.g., `env=prod`, `tier=frontend`, `hardware=gpu`). Without consistent labels, affinity rules become unmanageable.

---

## Common issues and troubleshooting

### Issue: Pods stuck in `Pending` after adding Node Affinity
- **Symptom:** `kubectl get pods` shows `Pending`. `kubectl describe pod` shows `0/N nodes are available: N node(s) didn't match pod affinity/anti-affinity`.
- **Root Cause:** A `requiredDuringSchedulingIgnoredDuringExecution` rule cannot be satisfied (e.g., typo in label key/value, or no nodes have that label).
- **Fix:** Verify node labels with `kubectl get nodes --show-labels`. If using `matchExpressions`, ensure the `operator` is correct.

### Issue: Unexpected pod eviction
- **Symptom:** Pods are suddenly terminated and rescheduled.
- **Root Cause:** A `NoExecute` taint was added to the node. This often happens automatically if a node becomes `Unreachable` or has `DiskPressure`.
- **Fix:** Check node conditions with `kubectl describe node`. If manually tainting, use `NoSchedule` instead.

### Issue: Pod Anti-Affinity causing high CPU on Scheduler
- **Symptom:** Slow scheduling in large clusters (>500 nodes).
- **Root Cause:** Pod anti-affinity is computationally expensive as the scheduler must check every pod on every node.
- **Fix:** Limit the scope of anti-affinity or use `TopologySpreadConstraints` which are often more efficient in newer Kubernetes versions (1.19+).

---

## Further reading

1.  **[Kubernetes Official Docs: Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)** — The definitive guide on the mechanism and effects.
2.  **[Kubernetes Official Docs: Assigning Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)** — Covers Node Affinity, Pod Affinity, and Pod Anti-Affinity in detail.
3.  **[Google Cloud Blog: Exploring Kubernetes Scheduling](https://cloud.google.com/blog/products/containers-kubernetes/kubernetes-scheduling-101)** — A great high-level overview of how these pieces fit together in production.
4.  **[Architecting for High Availability on Kubernetes](https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/containers/aks/guide-aks-high-availability)** — Practical patterns for using scheduling constraints for HA.
