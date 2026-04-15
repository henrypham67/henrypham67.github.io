---
title: 'Quality of Service - QoS'
date: 2026-04-04T16:59:46+07:00
draft: true
---

Quality of Service (QoS) is the mechanism Kubernetes uses to decide which Pods to keep running and which to kill when a Node runs out of resources (CPU, Memory, Disk).

## QoS Classes

| QoS Class  | Criteria (for CPU & Memory)                                                                                                                                      | Eviction Priority | Typical Use Case                  |
| :--------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------- | :-------------------------------- |
| **Guaranteed** | Every container (including init) has `requests == limits` for both CPU and Memory.                                                                              | Lowest (Last)     | Databases, critical stateful apps |
| **Burstable**  | At least one container has a request or limit, but it doesn't meet Guaranteed criteria.                                                                          | Medium            | Web servers, microservices        |
| **BestEffort** | No container has any CPU/Memory requests or limits.                                                                                                              | Highest (First)   | Batch jobs, dev/test workloads    |

## Myth vs. Reality: Does the Scheduler look at Limits?

**Myth:** "My node has free RAM, but I can't schedule pods because the existing pod limits take up all the space."
**Reality:** **False.** The `kube-scheduler` only subtracts **Requests** from the Node's capacity. It does not care if the sum of **Limits** exceeds the node's capacity (Overcommitment).

**The Exceptions:**
1. **Guaranteed Class:** If you only define limits, K8s sets `request = limit`. Here, the "limit" blocks scheduling only because it became a "request."
2. **ResourceQuotas:** A `ResourceQuota` on a **Namespace** can be configured to limit the sum of all *Limits*. In this case, the API server rejects the pod before the scheduler even sees it.

---

## The "Special Case": Limits without Requests

If you define a `limit` but omit the `request`, Kubernetes automatically sets `request = limit`.
- **Result:** The scheduler uses the limit's value for its calculations.
- **QoS Class:** This Pod automatically becomes **Guaranteed**.

---

## Deep Dive: How it works under the hood

### 1. The OOM Killer (`oom_score_adj`)

When a node is under memory pressure, the Linux kernel's Out-of-Memory (OOM) Killer looks at the `oom_score_adj` of processes to decide what to kill. Kubernetes sets these based on QoS:
- **Guaranteed:** `-997`. Almost impossible to kill unless the system itself is dying.
- **BestEffort:** `1000`. The first candidate for the OOM killer.
- **Burstable:** Scaled between `2` and `999`. 
    - *Critical Formula:* Your score is higher (more likely to die) if you use more memory relative to your **request**.

### 2. Compressible vs. Incompressible Resources

- **CPU (Compressible):** If you hit your limit, Kubernetes **throttles** you. Your app slows down but survives.
- **Memory (Incompressible):** If you hit your limit or the node is full, Kubernetes **terminates** (OOMKill) you. There is no "slowing down" memory.

## Real-World Gotchas

### The "Silent" Burstable Pod

If a Pod has two containers, and you only set limits for one, the entire Pod becomes **Burstable**. 
> **Risk:** The container with no limits can "leak" memory and cause the OOM killer to terminate the entire Pod, including your "critical" container.

### The Overcommitment Trap

Scheduling is based on **Requests**, not **Limits**. 
- If you have 10 pods requesting 100MB but limited to 2GB, the scheduler might put them all on a 2GB node.
- If they all spike at once, the node will crash. 
- **Rule of Thumb:** Keep your `limits` reasonably close to your `requests` for production workloads to avoid "flapping" pods.

### When to use what?

1. **Guaranteed:** Use for anything that holds state (DBs) or is extremely latency-sensitive.
2. **Burstable:** Use for most apps, but ensure `requests` represent your *actual* baseline usage.
3. **BestEffort:** Use for sidecars that aren't critical (like log collectors) or background cleanup jobs.