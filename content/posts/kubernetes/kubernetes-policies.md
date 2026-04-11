---
title: 'Mastering Resource Management: A Guide to LimitRanges and ResourceQuotas'
date: 2026-04-10T10:58:21+07:00
slug: kubernetes-policies
description: "Learn how to stabilize multi-tenant Kubernetes clusters using ResourceQuotas and LimitRanges. This guide covers the strategy, implementation, and data-driven methods for finding optimal resource values."
draft: false
tags: ["kubernetes", "policy", "security", "gitops"]
categories: ["Kubernetes"]
---

Managing a multi-tenant Kubernetes cluster without resource policies is like running a hotel without a booking system: eventually, one guest will check into the penthouse and accidentally consume the entire building's electricity and water supply. 

In Kubernetes, "noisy neighbors" aren't just an annoyance—they are a stability risk. A single misconfigured microservice with an infinite loop or a memory leak can starve critical system components, trigger node-wide evictions, and bring down your entire production environment. 

To prevent this, we use two primary policy mechanisms: **ResourceQuotas** and **LimitRanges**. While they are often mentioned in the same breath, they serve distinct roles in your cluster's defense-in-depth strategy.

## The difference between budget and guardrails

Before diving into implementation, it is crucial to understand the hierarchy:

1.  **ResourceQuotas (The Budget):** Operates at the **Namespace level**. It defines the total aggregate resources a team or project can consume. Think of it as a credit limit on a corporate card.
2.  **LimitRanges (The Guardrails):** Operates at the **Pod/Container level**. It defines the constraints for individual workloads. Think of it as a per-transaction limit on that same corporate card.

If you set a ResourceQuota but omit LimitRanges, Kubernetes becomes "strict mode." It will reject any Pod that doesn't explicitly declare its `requests` and `limits`. LimitRanges solve this by providing sensible defaults, ensuring that even "lazy" deployments have a safety net.

---

## The Great Debate: Namespace Governance vs. Node-level Optimization

A common debate in platform engineering is whether to use strict `ResourceQuotas` (Namespace Governance) or rely entirely on container `requests`/`limits` combined with the Cluster Autoscaler (Node-level Optimization). 

While dropping ResourceQuotas entirely might seem like it improves the developer experience, it introduces significant risks. Here is a breakdown of the two approaches:

### The Governance Approach (ResourceQuotas + LimitRanges)

This approach creates a "fenced yard" for each team or namespace.

**Pros:**
*   **True Multi-Tenancy:** "Team A" is physically blocked from scaling up to 1000 pods and starving "Team B".
*   **Predictable Cloud Billing:** Because you cap the total `requests` in a namespace, you can mathematically prove the maximum possible cloud cost for that team.
*   **Forces Accountability:** Developers must optimize their resource footprint.

**Cons (The "Bad Dev Experience"):**
*   **The "Quota Wall" Friction:** Developers frequently hit `403 Forbidden` errors during deployments or Horizontal Pod Autoscaler (HPA) scale-up events, blocking them until an admin increases the quota.
*   **Wasted Capacity:** If Team A has a quota of 100 CPUs but uses 10, the remaining 90 are "locked" and unavailable to Team B, even if the cluster has free space.

### The Fleet Approach (Node Monitoring & Restricting Node Usage)

This approach drops namespace quotas. You rely purely on container `requests`/`limits` to pack nodes efficiently, and the Cluster Autoscaler simply adds more nodes when they get full.

**Pros (The "Great Dev Experience"):**
*   **Zero Deployment Friction:** Developers never get a `403 Quota Exceeded` error. The Cluster Autoscaler just spins up more EC2 instances to handle the load.
*   **Faster Iteration:** Teams can stress-test applications or scale infinitely without waiting for an admin ticket.
*   **Better Resource Utilization:** Resources are pooled globally. If a node has free space, any pod can use it.

**Cons:**
*   **The "Runaway Bill" Risk:** A developer introduces a memory leak, the HPA scales out to 500 pods, the Cluster Autoscaler spins up 100 new EC2 instances, and your cloud bill spikes drastically over the weekend.
*   **Eviction Cascades:** If developers don't set proper `limits` (which quotas force them to do), containers on the same node will fight for resources. The `kubelet` will start killing pods (OOMKilled) to survive, causing brief outages for apps that did nothing wrong.

### The Verdict: A Hybrid "Sweet Spot"

To balance developer velocity with financial safety, implement a hybrid approach:

1.  **Drop Quotas in Dev/Staging:** In non-production environments, don't use `ResourceQuotas`. Let developers deploy freely. Instead, set a hard cap on the *Cluster Autoscaler* (e.g., "Max 5 nodes in the Staging node group"). Let the nodes fill up; if they run out of space, pods simply stay `Pending`.
2.  **Use LimitRanges Everywhere:** Even without Quotas, you **must** use `LimitRanges` to inject default `requests` and `limits`. This ensures the Node-level scheduler can prevent "Noisy Neighbors" without forcing developers to manually write boilerplate YAML.
3.  **Generous Quotas in Prod:** In Production, `ResourceQuotas` are mandatory to prevent a rogue microservice from crashing the platform. However, set them at **150% to 200% of expected peak usage**. This gives the HPA plenty of room to burst without hitting the "Quota Wall," preserving the developer experience while maintaining a financial safety net.

---

## Finding optimal resource values

Finding optimal values for `ResourceQuotas` and `LimitRanges` is a data-driven process that moves from **observation** to **enforcement**. You should never "guess" these numbers, as setting them too low causes performance issues (throttling/evictions) and setting them too high wastes money.

### 1. Vertical Pod Autoscaler (VPA) in Recommendation Mode
The VPA is the gold standard for finding optimal values.
- **How it works:** Deploy a `VerticalPodAutoscaler` object for your application but set the `updateMode` to `"Off"`. 
- **The Result:** It won't restart your pods, but it will track their actual usage and provide a `Recommendation` field in its status.
- **Optimal Value:** Use the `target` recommendation for your `requests` and the `uncappedTarget` as a baseline for your `limits`.

### 2. The 90th Percentile Rule (Prometheus/Grafana)
If you already use Prometheus, run queries to see the resource patterns of your containers over a 7-day period.
- **For CPU Requests:** Aim for the **90th percentile** of actual usage. This ensures that 90% of the time, your app is guaranteed exactly what it needs.
- **For Memory Requests:** Aim for the **Maximum** usage observed. Unlike CPU, memory cannot be "throttled"—if an app hits its limit, it crashes (OOMKill).
- **PromQL Example (CPU):**
  ```promql
  quantile_over_time(0.9, pod:container_cpu_usage:sum{container="my-app"}[7d])
  ```

### 3. Sizing the "Burst" (The Limit-to-Request Ratio)
Once you have your `requests` (the floor), you need to set `limits` (the ceiling).
- **CPU:** Since CPU is a compressible resource, you can be generous. A ratio of **2:1 or 3:1** (Limit:Request) is common. This allows apps to "burst" during startup or traffic spikes without affecting the node's stability.
- **Memory:** Be conservative. A ratio of **1:1 or 1.2:1** is recommended. Because memory isn't compressible, if multiple pods burst their memory at once, the Node will start killing processes (OOM) to stay alive.

### 4. Setting the Namespace Quota
When calculating the aggregate `ResourceQuota` for a namespace:
1.  **Sum of Requests:** Total the `requests` of all expected pods.
2.  **Add a "Scaling Buffer":** Add 20-30% to that total. This allows for Horizontal Pod Autoscaling (HPA) to kick in during peaks and for "Rolling Updates" to succeed.
3.  **Object Counts:** If a team has 5 microservices, each with 3 replicas, that's 15 pods. Set the quota to **25-30 pods** to allow for scaling and updates.

---

## ResourceQuotas: Managing the namespace budget

ResourceQuotas are your primary tool for preventing one team from monopolizing the cluster's capacity. Beyond just CPU and Memory, they can control the total number of objects in the API server.

### Best practices for quotas

- **Implement environment-based tiering:** Don't apply the same quota to every namespace. A `production` namespace should have a generous budget with high-priority classes, while a `sandbox` namespace should be strictly limited to prevent runaway experiments from costing thousands in cloud spend.
- **Limit object counts to prevent API bloat:** CPU and RAM aren't the only resources. Use quotas to limit `count/services.loadbalancer` (to control cloud costs) and `count/pods` or `count/configmaps` to protect `etcd` from being overwhelmed by object bloat.
- **Use Quota Scopes:** You can apply quotas based on the priority of the workload. For example, you might allow unlimited `BestEffort` pods (which are the first to be killed during contention) but strictly limit `Guaranteed` pods that require reserved capacity.

### Example ResourceQuota

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-alpha-quota
  namespace: app-team-alpha
spec:
  hard:
    # Compute Limits (Aggregate)
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    # Object Limits (Preventing Bloat)
    count/pods: "50"
    count/services.loadbalancer: "2"
    count/persistentvolumeclaims: "10"
```

---

## LimitRanges: Setting the container guardrails

LimitRanges ensure that every container stays within a "sane" operational envelope. They are enforced at the admission stage; if a Pod violates a LimitRange, it is rejected before it even reaches the scheduler.

### Best practices for LimitRanges

- **Set "Sane" Defaults:** This is the most powerful feature of LimitRanges. By setting `defaultRequest` and `default` (limits), you provide a safety net for developers. If they forget to specify resources, Kubernetes injects these values automatically.
- **Enforce boundaries with Min/Max:** 
    - **Max:** Prevents "mega-containers" that are too large to fit on your standard nodes.
    - **Min:** Prevents "micro-containers" that request so little (e.g., 1m CPU) that the overhead of scheduling them isn't worth the resource fragmentation.
- **Control overcommit with `maxLimitRequestRatio`:** This is an advanced but essential tool. It prevents a container from requesting 100m CPU but setting a limit of 10 CPUs. A high ratio allows for massive "bursting," which can lead to node instability if too many containers burst at once. A ratio of `2` or `3` is usually a safe starting point.

### Example LimitRange

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: team-alpha-limits
  namespace: app-team-alpha
spec:
  limits:
  - type: Container
    defaultRequest:       # Injected if missing
      cpu: 100m
      memory: 256Mi
    default:              # Injected if missing
      cpu: 500m
      memory: 512Mi
    min:                  # Lower bound
      cpu: 50m
      memory: 64Mi
    max:                  # Upper bound
      cpu: "2"
      memory: 2Gi
    maxLimitRequestRatio: 
      cpu: "4"            # Limit cannot exceed 4x the Request
```

---

## A framework for implementation

Setting these values shouldn't be a guessing game. Follow this four-step framework to roll out resource policies safely:

### 1. The Audit Phase
Do not enforce policies on day one. Use the **Vertical Pod Autoscaler (VPA)** in `Recommendation` mode to observe your applications' actual consumption over a full business cycle (usually 7 days). This gives you the "Ground Truth" of what your apps need.

### 2. The Baseline Phase
Apply `LimitRanges` first. Start with generous defaults that match the VPA recommendations for 90% of your workloads. This ensures that the majority of deployments continue to work while you catch the "outliers" that need manual tuning.

### 3. The Enforcement Phase
Apply `ResourceQuotas` via your GitOps pipeline (FluxCD or ArgoCD). Since these policies are namespace-scoped, managing them in Git alongside your `Namespace` definitions ensures that every new team gets a standardized "starter pack" of resource limits.

### 4. The Monitoring Phase
Enforcement is not the end. Use Prometheus and `kube-state-metrics` to monitor quota utilization. Set alerts at **80% utilization**. This gives your platform team (or the developers) enough lead time to request a quota increase or optimize their apps before the next deployment fails due to "insufficient quota."

## Conclusion

ResourceQuotas and LimitRanges are not just about restriction—they are about **predictability**. By defining a budget for your namespaces and guardrails for your containers, you create a stable environment where one team's mistake doesn't become everyone's outage.

If you are using FluxCD (as we do in this repo), ensure these manifests are part of your bootstrap process. Stability is a feature, and resource policies are the foundation that feature is built on.
