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
  - q: "A pod has both `nodeSelector` and `nodeAffinity`. How does the scheduler evaluate them?"
    a: "Both must be satisfied simultaneously — they are ANDed. `nodeSelector` is functionally equivalent to a `requiredDuringSchedulingIgnoredDuringExecution` node affinity rule with an `In` operator. If you specify both, a node must match both the `nodeSelector` key-value AND all `nodeAffinity` expressions."
  - q: "What does `IgnoredDuringExecution` actually mean?"
    a: "It means that once a pod is running, changes to node labels do NOT trigger eviction. If node affinity requires `env=prod` and you later remove that label from the node, the pod keeps running. Kubernetes has a long-planned `RequiredDuringExecution` variant that would evict in this case — it reached beta in 1.32 but isn't production-standard yet."

  - q: "A node has two `NoSchedule` taints. A pod tolerates only one of them. What happens?"
    a: "The pod will not be scheduled on that node. After applying all tolerations, if there remains any un-tolerated `NoSchedule` taint, scheduling is blocked. All taints must be tolerated for the effect to be neutralized. Partial toleration has no effect."

  - q: "What does `operator: Exists with no `key` in a toleration do?"
    a: "It matches every taint on every node — regardless of key, value, or effect. The pod will tolerate any taint and can schedule anywhere. This is the standard pattern for cluster-wide DaemonSets (monitoring agents, security scanners) that must run on all nodes including specially-tainted ones."

  - q: "You deploy a StatefulSet with 3 replicas and `required` per-node anti-affinity. What happens if you scale to 4 replicas in a 3-node cluster?"
    a: "The 4th pod stays Pending indefinitely. The scheduler cannot place it because every node already has one pod matching the anti-affinity selector, and the hard `requiredDuringScheduling` constraint cannot be satisfied. With hard anti-affinity, `replicas` must not exceed the number of available topology domains."

  - q: "How does pod affinity interact with pod anti-affinity when both are set on the same pod?"
    a: "They are evaluated independently and ANDed. A node must satisfy ALL required affinity rules AND ALL required anti-affinity rules. For preferred rules, scores from both are summed. There's no inherent conflict — a pod can say \"prefer to be near Redis\" (affinity) and \"never be near another instance of myself\" (anti-affinity) simultaneously."
  - q: "What is the difference between `kubectl drain` and applying a `NoExecute` taint for node evacuation?"
    a: "`kubectl drain` uses the Eviction API, which respects PodDisruptionBudgets — it will not evict pods if doing so would violate `minAvailable`. It also cordons the node first. Applying a `NoExecute` taint directly evicts pods immediately without PDB checks, which can cause availability incidents for stateful workloads. Always use `kubectl drain` for planned maintenance."

  - q: "Why might topology spread constraints behave unexpectedly during a rolling update?"
    a: "Without `matchLabelKeys`, the scheduler counts pods from both the old and new ReplicaSets when calculating skew. Old-revision pods in some zones can make those zones appear \"full,\" blocking new-revision pods from scheduling there. Setting `matchLabelKeys: [pod-template-hash]` scopes the spread calculation to only pods with the same template hash — i.e., only the current revision."
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

Taints, tolerations, and affinity are Kubernetes's scheduling control plane. Taints **repel** pods from nodes; affinity **attracts** pods to specific nodes or co-locates them with related pods. In production, you always use them together — taint a node pool to keep strangers out, add affinity to ensure the right workloads actually target it — enabling workload isolation, GPU/spot cost optimization, and HA spreading across zones.

---

## Core concepts and architecture

### The repel/attract mental model

Three tools, one goal: precise workload placement.

1. **Taints & Tolerations (Repulsion):** Applied to **Nodes**. A "Keep Out" sign. Any pod without a matching toleration is blocked or evicted.
2. **Node Affinity (Attraction):** Applied to **Pods**. An "I want to go there" rule based on node labels. Required (hard) or Preferred (soft with weights).
3. **Pod Anti-Affinity (Isolation):** Applied to **Pods**. An "I don't want to be near them" rule using `topologyKey` to define the failure domain (node, zone, region).

**The fundamental production rule:** A taint alone prevents the wrong workloads from landing on a node. But it doesn't guarantee your workload lands there. You need affinity for that guarantee. Always pair them.

### How the scheduler decides

The `kube-scheduler` uses the **Scheduling Framework** (stable since 1.19), a pipeline of plugins with clearly defined extension points:

```
New Pod enters queue
        |
        v
  [ PreEnqueue ]   -- gate: scheduling gates block here
        |
        v
  [ PreFilter  ]   -- compute affinity selectors, resource sums
        |
        v
  [   Filter   ]   -- ELIMINATE nodes (hard constraints)
  +--------------+
  | TaintToleration plugin  | removes nodes with un-tolerated taints
  | NodeAffinity plugin     | removes nodes not matching required affinity
  | InterPodAffinity plugin | removes nodes violating required pod anti-affinity
  | PodTopologySpread plugin| removes nodes that would violate maxSkew (DoNotSchedule)
  +--------------+
        |
        v
  [    Score    ]   -- RANK surviving nodes (0-100, soft preferences)
  +--------------+
  | TaintToleration  | prefers nodes with fewer PreferNoSchedule taints
  | NodeAffinity     | scores by preferred affinity weights
  | InterPodAffinity | scores by preferred pod affinity/anti-affinity weights
  | PodTopologySpread| scores for even distribution
  +--------------+
        |
        v
  [ NormalizeScore ]  -- each plugin normalized to 0-100, multiplied by weight
        |
        v
  [ Reserve / Bind ]  -- selected node, pod bound
```

A pod that fails the Filter phase stays **Pending** indefinitely until constraints are met. Preferred rules never cause pending — they only influence scoring.

### Taint effects compared

| Effect | Blocks new scheduling? | Evicts running pods? |
|--------|----------------------|---------------------|
| `PreferNoSchedule` | No — soft repulsion only | No |
| `NoSchedule` | Yes | No — existing pods stay |
| `NoExecute` | Yes | **Yes** — evicts pods lacking the toleration |

### Affinity types compared

| Type | Behavior |
|------|----------|
| `requiredDuringSchedulingIgnoredDuringExecution` | Hard constraint. Pod stays Pending if no matching node found. Label changes after scheduling are **ignored** — pod keeps running. |
| `preferredDuringSchedulingIgnoredDuringExecution` | Soft preference with `weight` (1-100). Scheduler tries but never blocks. |

---

## Key terms glossary

| Term | Definition |
|------|-----------|
| **Taint** | A node property (key, value, effect) that repels pods without a matching toleration. |
| **Toleration** | A pod property that allows it to be scheduled on a node with a matching taint. |
| **Node Affinity** | Pod rules that attract it to nodes with specific labels. Can be required or preferred. |
| **Pod Anti-Affinity** | Pod rules that prevent co-location with other pods in the same topology domain. |
| **topologyKey** | A node label key defining the failure domain for affinity/anti-affinity (e.g., `kubernetes.io/hostname` for node-level, `topology.kubernetes.io/zone` for zone-level). |
| **NoSchedule** | Taint effect that blocks new pods from scheduling but leaves existing pods running. |
| **NoExecute** | Strongest taint effect — blocks new pods AND evicts existing pods without the matching toleration. |
| **PreferNoSchedule** | Soft taint effect — scheduler avoids the node but doesn't block scheduling. |
| **tolerationSeconds** | Used with NoExecute tolerations; the number of seconds a pod may remain on a tainted node before being evicted. |
| **IgnoredDuringExecution** | Suffix on affinity types meaning: if node labels change after scheduling, the pod is NOT evicted. |
| **TopologySpreadConstraints** | An alternative to pod anti-affinity that enforces even distribution of pods across topology domains using a `maxSkew` limit. More scalable than anti-affinity at 50+ replicas. |
| **matchLabelKeys** | Field in topology spread constraints (GA in 1.31) that scopes the spread calculation to pods of the same ReplicaSet revision — critical for correct behavior during rolling updates. |
| **schedulingGates** | Alpha field (`.spec.schedulingGates`) that holds a pod in PreEnqueue until all gates are removed. Used for quota checks or resource pre-provisioning (stable in 1.30). |
| **PodDisruptionBudget (PDB)** | A separate resource that limits voluntary disruptions. `kubectl drain` respects PDBs, but manually applying `NoExecute` taints bypasses them. |

---

## Essential CLI and tools

### 1. Taint management

```bash
# Add a taint: key=value:effect
kubectl taint nodes node-01 dedicated=gpu:NoSchedule

# Add a taint with no value
kubectl taint nodes node-01 spot:NoSchedule

# Remove a taint (trailing minus sign)
kubectl taint nodes node-01 dedicated=gpu:NoSchedule-

# View all node taints — custom columns
kubectl get nodes -o custom-columns=\
  NAME:.metadata.name,\
  TAINTS:.spec.taints
```

### 2. Label inspection (required before writing affinity rules)

```bash
# Show all labels — always do this before writing nodeAffinity
kubectl get nodes --show-labels

# Filter nodes by a label — verify your affinity selector will match
kubectl get nodes -l topology.kubernetes.io/zone=us-east-1a

# Describe a node to see both taints and labels
kubectl describe node node-01 | grep -E "(Taints|Labels)" -A 10
```

### 3. Debugging pending pods

```bash
# First stop — always check pod events
kubectl describe pod <pod-name> | grep -A 20 Events

# Common messages to recognize:
# "0/5 nodes: 3 node(s) had untolerated taint {dedicated: gpu}, 
#  2 node(s) didn't match pod affinity/anti-affinity"

# Read the pod's actual toleration and affinity spec
kubectl get pod <pod-name> -o jsonpath='{.spec.tolerations}' | jq .
kubectl get pod <pod-name> -o jsonpath='{.spec.affinity}' | jq .

# Check if any node matches your affinity label expression
kubectl get nodes -l node-role=database
```

### 4. Node drain (PDB-safe eviction)

```bash
# Safe drain — respects PodDisruptionBudgets
kubectl drain node-01 --ignore-daemonsets --delete-emptydir-data

# Drain only specific workloads — useful for partial evacuation
kubectl drain node-01 --pod-selector=app=my-app \
  --ignore-daemonsets --delete-emptydir-data

# Cordon without eviction (adds NoSchedule, doesn't evict)
kubectl cordon node-01

# Uncordon to restore scheduling
kubectl uncordon node-01
```

### 5. Topology spread verification

```bash
# After deploying, check actual distribution across zones
kubectl get pods -l app=web-frontend -o wide \
  | awk '{print $7}' | sort | uniq -c

# Cross-reference with node zones
kubectl get pods -l app=web-frontend -o json \
  | jq -r '.items[].spec.nodeName' \
  | xargs -I{} kubectl get node {} \
      -o jsonpath='{.metadata.name}: {.metadata.labels.topology\.kubernetes\.io/zone}{"\n"}'
```

---

## Best practices

### 1. Always pair taints with node affinity for strict isolation

A taint is a **one-way repulsion**. It prevents pods *without* the matching toleration from landing on the node. But it says nothing about where pods *with* the toleration should go. A pod that tolerates `dedicated=ml:NoSchedule` can still schedule onto any shared node that has no taints at all — the scheduler simply picks whatever fits. Without node affinity, your ML pods silently land on shared CPU nodes during capacity pressure and your expensive GPU nodes sit idle.

**What goes wrong with taint-only isolation:**

| Scenario | Taint only | Taint + Affinity |
|---|---|---|
| Non-GPU pod tries GPU node | Blocked | Blocked |
| GPU pod during cluster pressure | Lands on any available node (shared!) | Stays Pending until GPU node has capacity |
| GPU node utilization after rollout | Unpredictable — depends on bin-packing | Guaranteed — all GPU pods land on GPU nodes |
| Cost attribution per node pool | Breaks — workloads bleed across pools | Clean — each pool hosts exactly its workloads |

**The two-way lock pattern:**

```
Taint  →  keeps non-GPU pods OUT of GPU nodes
Affinity →  keeps GPU pods FROM landing on shared nodes

  [ shared nodes ]          [ GPU node pool ]
  ┌────────────┐            ┌──────────────┐
  │  app pods  │            │  ml-training │
  │  api pods  │            │  ml-training │
  │            │            │  ml-training │
  └────────────┘            └──────────────┘
   no taint needed           taint: dedicated=ml:NoSchedule
                             label: node-role=ml

  ml-training pod spec:
    toleration: dedicated=ml:NoSchedule  ← can enter the pool
    nodeAffinity: node-role In [ml]      ← MUST enter the pool
```

**Node setup — always apply both label and taint together:**

```bash
# Label first — affinity rules match on this
kubectl label nodes <node> node-role=ml

# Then taint — repels pods without the toleration
kubectl taint nodes <node> dedicated=ml:NoSchedule
```

When using cloud-managed node pools (GKE, EKS, AKS), set both the label and taint at pool creation time in the node pool config — not post-hoc with kubectl. Manually applied taints are lost when nodes are replaced by the autoscaler.

**Pod spec — the minimum required fields for both directions:**

```yaml
spec:
  tolerations:
  - key: "dedicated"
    operator: "Equal"        # strict: only matches value "ml", not other dedicated= taints
    value: "ml"
    effect: "NoSchedule"
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: node-role
            operator: In
            values: ["ml"]   # must be present on the node — pod stays Pending otherwise
```

**Production tips:**
- Use `operator: Equal` (not `Exists`) in tolerations when you have multiple pools with the same taint key (e.g., `dedicated=ml`, `dedicated=gpu`, `dedicated=database`). `Exists` would tolerate all of them, breaking pool-level isolation.
- The taint key in the toleration and the label key in the affinity are independent — they don't have to match. Taint keys enforce the repulsion mechanism; label keys drive the affinity selector. Keeping them consistent (same value, different keys) reduces operational confusion.
- See [Pattern 1: GPU workload isolation](#pattern-1-gpu-workload-isolation) and [Pattern 6: Multi-tenant node isolation](#pattern-6-multi-tenant-node-isolation) for full production-ready YAML templates using this pattern.

### 2. Use `NoSchedule` for reservations, `NoExecute` only for emergencies

`NoExecute` evicts running pods immediately (subject to `tolerationSeconds`), bypassing PodDisruptionBudgets. Use it deliberately — for urgent security patches or hardware failures. For normal workload isolation or planned maintenance, use `NoSchedule` + `kubectl drain` to respect PDBs.

### 3. Don't over-constrain with `required` affinity

If you require pods to spread across 3 zones but only have 2 zones, the 3rd replica stays Pending forever. Use `preferredDuringSchedulingIgnoredDuringExecution` with a high weight (80-100) for zone spreading. Reserve `required` for hard HA guarantees like "never two database replicas on the same node."

### 4. Set `topologyKey` strategically

- `kubernetes.io/hostname` — node-level spreading (failure domain: one node)
- `topology.kubernetes.io/zone` — zone-level spreading (failure domain: one AZ)
- `topology.kubernetes.io/region` — region-level (rarely needed, very coarse)

For stateful databases: required per-node + preferred per-zone is the standard pattern. For stateless frontends: preferred per-zone is usually sufficient.

### 5. Use topology spread constraints over pod anti-affinity at scale

Pod anti-affinity is O(n×p) — for every new pod, the scheduler checks every existing pod on every node. Beyond ~50 replicas, this degrades scheduling throughput noticeably. `topologySpreadConstraints` is significantly more efficient and gives you numeric control over the skew tolerance.

### 6. Add `matchLabelKeys` to topology spread constraints (K8s 1.31+)

Without `matchLabelKeys`, during a rolling update the scheduler counts pods from both old and new ReplicaSets when calculating skew. This can block new pods because old pods already fill certain zones.

```yaml
topologySpreadConstraints:
- maxSkew: 1
  topologyKey: topology.kubernetes.io/zone
  whenUnsatisfiable: DoNotSchedule
  labelSelector:
    matchLabels:
      app: web
  matchLabelKeys:
  - pod-template-hash  # auto-added by Deployment — scopes spread to this revision
```

### 7. Give DaemonSets explicit tolerations for custom taints

DaemonSets auto-tolerate all built-in Kubernetes taints (not-ready, disk-pressure, etc.) but do NOT auto-tolerate custom taints. If you add `dedicated=gpu:NoSchedule` to a node pool, your Prometheus node exporter DaemonSet won't schedule there unless you add the toleration. For cluster-wide agents, use `operator: Exists` with no `key`:

```yaml
tolerations:
- operator: "Exists"  # tolerates every taint on every node
```

### 8. Tune `tolerationSeconds` for spot instances

Cloud providers apply `NoExecute` taints on preemption. The grace window before eviction should be: `tolerationSeconds` < cloud preemption warning time, and `terminationGracePeriodSeconds` < `tolerationSeconds`.

For GKE spot (120-second warning): set `tolerationSeconds: 60`, `terminationGracePeriodSeconds: 45`. This gives the pod time to checkpoint work before the node is yanked.

---

## Real-world patterns

### Pattern 1: GPU workload isolation

GPU nodes are expensive. The taint prevents non-GPU workloads from wasting them. The node affinity ensures GPU workloads target the right GPU model (A100 vs T4 vs L4).

```bash
# Node setup
kubectl taint nodes gpu-node-1 nvidia.com/gpu=present:NoSchedule
kubectl label nodes gpu-node-1 accelerator=nvidia-a100
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-training
spec:
  replicas: 4
  selector:
    matchLabels:
      app: ml-training
  template:
    metadata:
      labels:
        app: ml-training
    spec:
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Equal"
        value: "present"
        effect: "NoSchedule"
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: accelerator
                operator: In
                values:
                - nvidia-a100
      containers:
      - name: trainer
        image: my-training:latest
        resources:
          limits:
            nvidia.com/gpu: 1
```

### Pattern 2: Spot instance cost optimization

Cloud providers auto-taint spot nodes. Set `tolerationSeconds` to handle the preemption window gracefully. Using `preferredDuringScheduling` for spot preference lets pods fall back to on-demand if spot capacity is unavailable.

```yaml
spec:
  tolerations:
  # GKE Spot
  - key: "cloud.google.com/gke-spot"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
  # EKS with Karpenter
  - key: "karpenter.sh/capacity-type"
    operator: "Equal"
    value: "spot"
    effect: "NoSchedule"
  # Handle preemption eviction — 60s grace before eviction
  - key: "cloud.google.com/gke-spot"
    operator: "Equal"
    value: "true"
    effect: "NoExecute"
    tolerationSeconds: 60
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 90
        preference:
          matchExpressions:
          - key: "node.kubernetes.io/instance-type"
            operator: In
            values: ["spot"]
      - weight: 10
        preference:
          matchExpressions:
          - key: "node.kubernetes.io/instance-type"
            operator: In
            values: ["on-demand"]
  terminationGracePeriodSeconds: 45
```

### Pattern 3: Database HA StatefulSet

Hard per-node anti-affinity prevents two replicas on the same machine. Soft per-zone spreading is `preferred` because if you only have 2 zones and need 3 replicas, a `required` zone constraint would leave the third pod Pending forever.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
spec:
  replicas: 3
  serviceName: postgresql
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      tolerations:
      - key: "dedicated"
        operator: "Equal"
        value: "database"
        effect: "NoSchedule"
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: node-role
                operator: In
                values: ["database"]
        podAntiAffinity:
          # Hard: never two postgres pods on the same node
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values: ["postgresql"]
            topologyKey: "kubernetes.io/hostname"
          # Soft: try to spread across zones
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values: ["postgresql"]
              topologyKey: "topology.kubernetes.io/zone"
      containers:
      - name: postgresql
        image: postgres:16
        resources:
          requests:
            cpu: "2"
            memory: "8Gi"
          limits:
            cpu: "4"
            memory: "16Gi"
```

### Pattern 4: Topology spread constraints for stateless workloads

For 12+ replicas, prefer topology spread constraints over pod anti-affinity. The `matchLabelKeys` field (GA in 1.31) prevents cross-revision skew during rolling updates.

```yaml
spec:
  topologySpreadConstraints:
  # Hard: max 1 pod difference between any two zones
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: web-frontend
    matchLabelKeys:
    - pod-template-hash
  # Soft: try to spread within each zone across nodes
  - maxSkew: 2
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels:
        app: web-frontend
```

### Pattern 5: DaemonSet tolerate-all for cluster-wide agents

Monitoring and logging agents must run on every node, including GPU nodes, spot nodes, and any custom-tainted pool.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      tolerations:
      - operator: "Exists"  # matches every taint, key and effect are optional
      containers:
      - name: exporter
        image: prom/node-exporter:v1.8.0
```

### Pattern 6: Multi-tenant node isolation

Taint prevents other tenants' pods from landing on tenant-a's nodes. Node affinity ensures tenant-a's pods only land on their dedicated nodes — not on shared capacity.

```bash
# Node setup per tenant pool
kubectl taint nodes <pool-node> dedicated=tenant-a:NoSchedule
kubectl label nodes <pool-node> tenant=a
```

```yaml
# In every tenant-a Deployment/StatefulSet
spec:
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "tenant-a"
    effect: "NoSchedule"
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: tenant
            operator: In
            values: ["a"]
```

---

## Common issues and troubleshooting

### Issue 1: Pods stuck in `Pending` — full diagnosis flow

```bash
# 1. Read the scheduling failure reason
kubectl describe pod <pod-name> | grep -A 20 Events
# Message: "0/5 nodes: 3 node(s) had untolerated taint {dedicated: gpu}, 
#  2 node(s) didn't match node affinity/selector"

# 2. Check if any node has your target label
kubectl get nodes -l node-role=database  # empty = your affinity label doesn't exist

# 3. Check taints on candidate nodes
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints

# 4. Verify the pod's actual tolerations
kubectl get pod <pod-name> -o jsonpath='{.spec.tolerations}' | jq .
```

The failure message is usually explicit about which constraint failed and how many nodes were eliminated at each step.

### Issue 2: Unexpected pod eviction after `NoExecute` taint

- **Symptom:** Pods suddenly terminate and reschedule when nothing changed in their spec.
- **Root cause:** A `NoExecute` taint was applied to the node — either manually, or automatically by Kubernetes when the node enters `NotReady`/`Unreachable` state.
- **Fix:** Check `kubectl describe node <node>` for taints and node conditions. For planned node work, use `kubectl drain` instead of `NoExecute` taints — drain respects PodDisruptionBudgets.

**Built-in auto-applied `NoExecute` taints with default tolerations:**

| Auto-taint | Applied when | Kubernetes default tolerance |
|---|---|---|
| `node.kubernetes.io/not-ready` | Node NotReady | 300 seconds |
| `node.kubernetes.io/unreachable` | Node unreachable | 300 seconds |

You can reduce these for critical services that need faster failover:

```yaml
tolerations:
- key: "node.kubernetes.io/not-ready"
  operator: "Exists"
  effect: "NoExecute"
  tolerationSeconds: 30  # evict after 30s instead of default 300s
- key: "node.kubernetes.io/unreachable"
  operator: "Exists"
  effect: "NoExecute"
  tolerationSeconds: 30
```

### Issue 3: DaemonSet not scheduling on custom-tainted nodes

- **Symptom:** DaemonSet pods exist on most nodes but are absent from certain node pools (GPU, spot, dedicated).
- **Root cause:** DaemonSets auto-tolerate all built-in Kubernetes taints but NOT custom taints. Any custom taint will block DaemonSet pods.
- **Fix:** Add explicit tolerations for every custom taint. For cluster-wide agents, use `operator: Exists` with no `key` to tolerate everything.

### Issue 4: `NoExecute` bypasses PodDisruptionBudgets

- **Symptom:** Multiple replicas of a stateful application are evicted simultaneously, violating your PDB's `minAvailable`.
- **Root cause:** `NoExecute` taints do not check PodDisruptionBudgets. PDBs are only enforced by the Eviction API (used by `kubectl drain`).
- **Fix:** For controlled maintenance, always use `kubectl drain --ignore-daemonsets --delete-emptydir-data`. Reserve `NoExecute` taints for genuine node failures.

### Issue 5: Scheduler performance degrades with large-scale anti-affinity

- **Symptom:** Pod scheduling takes seconds instead of milliseconds in clusters with 500+ nodes and large deployments (50+ replicas) using pod anti-affinity.
- **Root cause:** Pod anti-affinity evaluation is O(n × p): for each candidate node, the scheduler iterates all existing pods matching the anti-affinity selector.
- **Fix:** Migrate to `topologySpreadConstraints` for deployments with many replicas. If anti-affinity is required, scope it to a namespace with `namespaceSelector` to reduce the search space.

### Issue 6: PersistentVolume zone conflicts with pod anti-affinity

- **Symptom:** StatefulSet pods schedule correctly on first deploy but get stuck Pending on rescheduling after a node failure.
- **Root cause:** A PV was provisioned in zone A. After a node failure, anti-affinity rules push the pod to zone B, but the PV can't follow.
- **Fix:** For StatefulSets with zone-level anti-affinity, use a `StorageClass` with `volumeBindingMode: WaitForFirstConsumer`. This delays PV provisioning until the pod is scheduled, so the PV is created in the same zone as the pod — not before.

## Further reading

1. **[Kubernetes docs: Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)** — Definitive reference for taint effects, built-in taints, and toleration syntax.
2. **[Kubernetes docs: Assigning Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)** — Covers node affinity, pod affinity/anti-affinity, and topology spread constraints with the full API spec.
3. **[Kubernetes docs: Pod Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)** — Deep dive on `maxSkew`, `minDomains`, `matchLabelKeys`, and when to prefer this over anti-affinity.
4. **[Kubernetes Scheduling Framework KEP](https://github.com/kubernetes/enhancements/tree/master/keps/sig-scheduling/624-scheduling-framework)** — The design doc for the Filter/Score pipeline — essential reading if you're debugging scheduler behavior or writing custom plugins.
5. **[EKS Best Practices: Reliability](https://aws.github.io/aws-eks-best-practices/reliability/docs/dataplane/)** — Practical patterns for spot instance tolerations, multi-AZ spreading, and PDB configuration in production EKS clusters.
