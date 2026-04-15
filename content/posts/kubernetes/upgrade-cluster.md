---
title: 'Upgrade cluster'
date: 2026-04-20T14:45:00+07:00
draft: true
tags: ["kubernetes", "cluster-management", "devops"]
categories: ["Kubernetes"]
---

application support or not?
thu tu upgrade
minimize downtime (replication, pdb, pod eviction order)

## TL;DR

Upgrading a Kubernetes cluster is a high-stakes operational task that involves moving the control plane and worker nodes to a newer version. It requires a strict "control-plane-first" sequence, careful API version audits, and the use of strategies like Rolling Updates or Blue-Green deployments to ensure zero or minimal downtime for workloads.

---

## Core concepts and architecture

A Kubernetes upgrade is never a single "click" operation in production. It follows a hierarchical dependency where the control plane must always be equal to or newer than the worker nodes.

### The Upgrade Sequence
1.  **Pre-flight:** Backup etcd, audit for deprecated APIs, and verify cluster health.
2.  **Control Plane:** Upgrade the API server, Controller Manager, and Scheduler. This is typically done one node at a time in HA setups.
3.  **Worker Nodes:** Upgrade the kubelet and container runtime on each node.

### The "Drain and Fill" Pattern
For worker nodes, the standard practice is the **Cordon, Drain, Upgrade, Uncordon** workflow:

```ascii
      [ Node ]
         |
         v
    +---------+       1. Cordon: Mark node unschedulable
    | Cordon  | -------------------------------------+
    +---------+                                      |
         |                                           |
         v                                           v
    +---------+       2. Drain: Evict pods to other nodes
    |  Drain  | -------------------------------------+
    +---------+                                      |
         |                                           |
         v                                           v
    +---------+       3. Upgrade: Update kubelet & OS
    | Upgrade | -------------------------------------+
    +---------+                                      |
         |                                           |
         v                                           v
    +---------+       4. Uncordon: Return to service
    |Uncordon | <------------------------------------+
    +---------+
```

---

## Key terms glossary

| Term | Definition |
|------|-----------|
| **Minor Version Upgrade** | Moving from 1.29 to 1.30. K8s only supports upgrading one minor version at a time. |
| **Patch Version Upgrade** | Moving from 1.30.1 to 1.30.2. Generally safer and can often skip patches. |
| **Cordon** | Marking a node as unschedulable so no new pods are placed on it. |
| **Drain** | Safely evicting all pods from a node so it can be taken down for maintenance. |
| **PDB (Pod Disruption Budget)** | A policy that limits the number of pods of a replicated application that are down simultaneously. |
| **etcd Snapshot** | A point-in-time backup of the cluster state. Essential before any upgrade. |
| **In-place Upgrade** | Upgrading components on existing nodes. |
| **Blue-Green Upgrade** | Creating a new cluster/node-pool and migrating traffic to it. |

---

## Essential CLI and tools

### 1. Planning the Upgrade (kubeadm)
If you manage your own cluster with `kubeadm`, this command checks for available versions and API compatibility.

```bash
# Check for upgrade versions
kubeadm upgrade plan
```

### 2. Applying the Upgrade
Upgrades the control plane components on the current node.

```bash
# Apply the upgrade to the control plane
sudo kubeadm upgrade apply v1.30.0
```

### 3. Node Maintenance
The standard sequence for worker nodes.

```bash
# 1. Stop new pods from landing
kubectl cordon node-01

# 2. Evict existing pods (ignoring DaemonSets)
kubectl drain node-01 --ignore-daemonsets --delete-emptydir-data

# 3. [Perform OS/Kubelet upgrade here]

# 4. Resume scheduling
kubectl uncordon node-01
```

---

## Best practices

### 1. Never Skip Minor Versions
Kubernetes does not support skipping versions (e.g., 1.28 -> 1.30). You must go 1.28 -> 1.29 -> 1.30. Skipping versions risks etcd data corruption and API breakage.

### 2. Use Pod Disruption Budgets (PDBs)
Draining a node without a PDB is dangerous. PDBs ensure that your application maintains a minimum number of available replicas during the drain process.

### 3. Audit Deprecated APIs
Before upgrading, use tools like `pluto` or `kubent` to find resources using APIs that will be removed in the target version. If you don't update your manifests, they will fail to deploy after the upgrade.

### 4. Backup etcd
For self-managed clusters, an etcd backup is your only safety net. If the control plane upgrade fails and the data becomes corrupted, you'll need this to restore the cluster.

### 5. Upgrade the Cluster Autoscaler
If you use a Cluster Autoscaler, ensure its version matches the Kubernetes minor version (e.g., Autoscaler 1.30.x for K8s 1.30.x).

---

## Common issues and troubleshooting

### Issue: Pods stuck in `Terminating` during Drain
- **Symptom:** `kubectl drain` hangs and pods never leave the node.
- **Root Cause:** Often due to finalizers (e.g., for volumes or specialized operators) that can't be resolved, or pods that ignore SIGTERM.
- **Fix:** Check pod logs. Use `--force` if necessary, but be careful with stateful workloads.

### Issue: Kubelet fails to start after upgrade
- **Symptom:** Node stays in `NotReady` status. `systemctl status kubelet` shows failure.
- **Root Cause:** Incompatible flags in `/var/lib/kubelet/config.yaml` or container runtime version mismatch.
- **Fix:** Check `journalctl -u kubelet`. Verify if the CNI or CRI needs an update to support the new K8s version.

### Issue: Deprecated API Deployment Failure
- **Symptom:** CI/CD pipelines fail to deploy manifests after upgrade.
- **Root Cause:** The target K8s version removed an API (e.g., `policy/v1beta1` PodSecurityPolicy removed in 1.25).
- **Fix:** Update manifests to the supported API version (e.g., use Pod Security Admission).

---

## Interview-ready knowledge

**Q: In what order should you upgrade a Kubernetes cluster?**
Control plane first (API server, then other components), then worker nodes. The API server must be the same version or newer than the other control plane components and the kubelets.

**Q: What is the "version skew" policy in Kubernetes?**
Kubernetes supports a skew of up to two minor versions between the API server and worker nodes (kubelets), but the API server must always be the newest component.

**Q: How do you handle a failed worker node upgrade?**
Since nodes are typically drained before upgrading, the workload is already running elsewhere. You can attempt to fix the node, or simply decommission it and provision a new node with the target version.

**Q: What happens if you don't drain a node before upgrading the kubelet?**
The pods might stay running, but the connection between the kubelet and the API server will be interrupted. If the upgrade requires a node reboot or a container runtime restart, all pods will be killed abruptly without a graceful shutdown.

---

## Further reading

1.  **[Kubernetes Official: Upgrading kubeadm clusters](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)** — The standard technical guide.
2.  **[Kubernetes Version Skew Policy](https://kubernetes.io/releases/version-skew-policy/)** — Understanding what versions can talk to each other.
3.  **[Karsajs: Kubernetes API Deprecation Guide](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)** — Essential for pre-upgrade audits.
4.  **[AWS EKS: Upgrading Cluster Version](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html)** — Best practices for managed Kubernetes.
