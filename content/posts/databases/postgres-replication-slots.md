---
title: 'Understanding PostgreSQL Replication Slots in CloudNativePG'
date: 2026-01-04T10:42:55+07:00
slug: postgres-replication-slots-cloudnativepg
draft: false
categories:
  - databases
  - kubernetes
tags:
  - postgresql
  - cloudnativepg
  - high-availability
  - replication
---

When you configure `highAvailability.enabled: true` in your CloudNativePG cluster, what actually happens behind the scenes? If you've set up PostgreSQL high availability in Kubernetes, you might have seen this configuration option and wondered about the mechanics that make it work. This post dives deep into PostgreSQL replication slots, how CloudNativePG automates their management, and why they're critical for maintaining reliable database replication in Kubernetes environments.

This is a technical deep dive intended for readers who want to understand the internals beyond basic configuration. If you're looking for a broader overview of CloudNativePG features and setup, check out my [previous post on managing PostgreSQL with CloudNativePG](/posts/databases/db-operator).

## The problem: WAL segments and replication lag

PostgreSQL uses Write-Ahead Logging (WAL) to ensure data durability and enable replication. Every change to the database is first written to WAL segments before being applied to the actual data files. These WAL segments are stored in the `pg_wal` directory and serve two critical purposes: crash recovery and streaming replication to standby servers.

Here's where the challenge begins: PostgreSQL automatically recycles WAL segments to manage disk space. The database keeps WAL segments around for a certain period based on the `wal_keep_size` parameter (or `wal_keep_segments` in older versions), but once it determines they're no longer needed for crash recovery, it removes them.

This works fine for standalone databases, but introduces a serious problem for replication. Consider this scenario:

Your primary PostgreSQL server is running smoothly, streaming WAL changes to two standby replicas. One standby experiences a network partition and falls behind by an hour. During that hour, the primary generates 10GB of WAL segments. When the network recovers, the standby tries to catch up by requesting the WAL segments it missed. But the primary has already deleted them to free up disk space.

The result? Your standby can't catch up without a full re-sync from a base backup. In a Kubernetes environment where pods can restart, nodes can fail, and network issues are inevitable, this catch-up problem becomes a critical operational challenge. You need a mechanism that tells PostgreSQL: "Keep these WAL segments around because this standby still needs them."

## How replication slots solve the problem

Replication slots are PostgreSQL's solution to the WAL retention problem. They're a built-in PostgreSQL feature (introduced in version 9.4) that creates a "bookmark" for each standby server, tracking exactly which WAL position it has replayed up to.

When you create a replication slot, PostgreSQL tracks the Log Sequence Number (LSN) for that slot. The LSN is essentially a byte offset into the WAL stream—it uniquely identifies a position in the transaction log. Every time the standby consumes WAL data and advances its replay position, it updates the slot's LSN.

The crucial behavior: PostgreSQL will never delete WAL segments that are still needed by any active replication slot. Even if a standby falls hours behind, as long as its replication slot exists, the primary retains all the WAL segments required for it to catch up.

There are two types of replication slots:

**Physical replication slots** track byte-level replication (WAL streaming). The standby replays WAL records exactly as they were written on the primary. This is what CloudNativePG uses for high availability.

**Logical replication slots** track row-level changes for selective replication. These are used for different use cases like selective table replication or change data capture.

The trade-off with replication slots is storage consumption. If a standby is offline for an extended period, the primary must retain potentially gigabytes of WAL segments. This is why monitoring slot lag is critical—you need to know when a slot is preventing WAL cleanup and potentially filling your disk.

You can see replication slots in action by querying the `pg_replication_slots` system view:

```sql
SELECT slot_name, slot_type, active, restart_lsn,
       pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) AS lag_bytes
FROM pg_replication_slots;
```

This shows each slot's name, whether it's currently active, the LSN it's waiting for, and how far behind it is in bytes.

## What happens when highAvailability.enabled: true

In traditional PostgreSQL setups, managing replication slots is a manual process. You create slots using `pg_create_physical_replication_slot()`, monitor them, and clean them up when standby servers are permanently removed. In a Kubernetes environment where pods are ephemeral and can be rescheduled at any time, manual slot management becomes operationally complex and error-prone.

This is where CloudNativePG's automation shines. When you set `replicationSlots.highAvailability.enabled: true` in your cluster spec, the operator takes over complete lifecycle management of replication slots.

Here's a typical CloudNativePG configuration:

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: gitea-pg-ha
  namespace: gitea
spec:
  instances: 3
  replicationSlots:
    highAvailability:
      enabled: true
  minSyncReplicas: 1
```

When the operator processes this configuration, it automatically:

**Creates physical replication slots on the primary**: For a 3-instance cluster like our Gitea example, CloudNativePG creates slots named `_cnpg_gitea-pg-ha-2` and `_cnpg_gitea-pg-ha-3` on the primary pod (`gitea-pg-ha-1`). The `_cnpg_` prefix identifies these as operator-managed slots, distinguishing them from any user-created slots.

**Associates each slot with a standby pod**: The slot naming convention ties directly to the pod name. When `gitea-pg-ha-2` starts streaming replication, it uses the `_cnpg_gitea-pg-ha-2` slot automatically. This connection is established through the `primary_slot_name` parameter in the standby's `recovery.conf` (or `postgresql.auto.conf` in PostgreSQL 12+).

**Monitors slot status**: The operator continuously monitors slot activity through the PostgreSQL stats views. It tracks whether slots are active, how much WAL lag they have, and whether they're preventing WAL cleanup.

**Handles pod lifecycle events**: When a standby pod is deleted (for example, during a rolling update), CloudNativePG doesn't immediately remove the slot. This is intentional—the pod might be rescheduled, and keeping the slot around means it can resume replication from where it left off rather than needing to re-sync from scratch.

**Cleans up stale slots**: If a pod is permanently removed (like when you scale down from 3 to 2 instances), the operator detects the change and drops the corresponding replication slot. This prevents abandoned slots from consuming disk space indefinitely.

The automation extends to slot recreation during failover. If the primary pod fails, CloudNativePG promotes one of the standbys (say, `gitea-pg-ha-2`) to become the new primary. As part of the promotion process, the operator creates new replication slots on the new primary for all remaining standbys. This ensures continuous protection even after topology changes.

What makes this particularly elegant is the integration with Kubernetes native concepts. The operator watches Pod resources, responds to lifecycle events, and uses the Kubernetes control loop to maintain the desired state. You declare what you want (3 instances with HA enabled), and the operator ensures slots exist and are maintained regardless of pod churn.

## How failover works with replication slots

Understanding failover mechanics helps clarify why replication slots are critical for high availability. Let's walk through what happens when a primary pod fails in our 3-instance Gitea cluster.

**Failure detection**: CloudNativePG uses PostgreSQL's built-in health checks combined with Kubernetes liveness probes. When the primary pod (`gitea-pg-ha-1`) becomes unresponsive—whether due to a process crash, node failure, or network partition—the operator detects this within seconds.

**Standby selection**: The operator examines both remaining standbys (`gitea-pg-ha-2` and `gitea-pg-ha-3`) to determine which one is most up-to-date. It compares their WAL replay positions using `pg_last_wal_replay_lsn()`. The standby with the highest LSN (meaning it has replayed more WAL records) becomes the promotion candidate.

In our configuration with `minSyncReplicas: 1`, at least one standby is guaranteed to have all committed transactions. This standby is typically chosen for promotion, ensuring zero data loss.

**Promotion process**: CloudNativePG executes the promotion by running `pg_ctl promote` on the selected standby. This transitions it from recovery mode to normal operation. The promoted server creates a new timeline—a PostgreSQL concept that tracks the history of the cluster. Timeline IDs increment with each failover, allowing PostgreSQL to track branching histories.

**Replication slot recreation**: This is where slots become crucial. As soon as the new primary is promoted, the operator creates fresh replication slots for all remaining standbys. For our Gitea cluster, if `gitea-pg-ha-2` becomes the new primary, the operator creates:
- `_cnpg_gitea-pg-ha-1` (for the former primary, now a standby)
- `_cnpg_gitea-pg-ha-3` (for the other standby)

Without slots, there's a dangerous window during failover where the new primary might delete WAL segments before the other standbys catch up. Slots eliminate this risk.

**Standby reconfiguration**: The operator updates all standby pods to point to the new primary. It modifies their replication configuration to stream from `gitea-pg-ha-2` and use their designated replication slots. The former primary (`gitea-pg-ha-1`), once it recovers, is automatically reconfigured as a standby and begins streaming from the new primary using its slot.

**Service endpoint updates**: CloudNativePG manages Kubernetes Service resources that provide stable endpoints for your application. The read-write service (typically named `<cluster-name>-rw`) automatically updates to point to the new primary pod. Your application connections experience brief interruptions but automatically reconnect to the correct primary without requiring manual intervention.

The entire failover process typically completes within 30-60 seconds for small to medium databases. During this window, replication slots ensure that no WAL data is lost, and all standbys can seamlessly continue replication from the new primary.

One subtle but important detail: CloudNativePG uses physical replication slots, which means standbys follow the new timeline automatically. They don't need special timeline-following configuration—they simply continue consuming WAL records from where they left off.

## Replication slots + synchronous replication

A common point of confusion is the relationship between replication slots and synchronous replication. They address different aspects of high availability and work together to provide comprehensive data protection.

**Replication slots solve the WAL retention problem**. They ensure that standby servers can always catch up after falling behind by preventing the primary from deleting needed WAL segments. Slots are about availability—keeping your standby servers functional even after network issues or extended downtime.

**Synchronous replication (configured with `minSyncReplicas`) solves the durability problem**. It ensures that transactions aren't committed until at least one standby has acknowledged receiving the WAL data. This is about consistency—guaranteeing zero data loss during failover.

Here's a practical example using our Gitea cluster configuration:

```yaml
spec:
  instances: 3
  replicationSlots:
    highAvailability:
      enabled: true
  minSyncReplicas: 1
```

With this configuration:

- Replication slots ensure all three instances can stay in sync even if one falls behind temporarily
- `minSyncReplicas: 1` ensures every committed transaction has been received by at least one standby before the primary acknowledges the commit to the client

Both are necessary for true high availability:

- Without slots, a laggy standby might never catch up
- Without synchronous replication, a failover could lose recently committed transactions

The configuration value you choose for `minSyncReplicas` involves trade-offs:

**minSyncReplicas: 0** (asynchronous replication): Maximum availability and performance. The primary doesn't wait for standby acknowledgments. However, failover could lose transactions that were committed but not yet replicated. Acceptable for development or scenarios where some data loss is tolerable.

**minSyncReplicas: 1** (recommended for 3-instance clusters): Balanced approach. Every transaction is guaranteed on at least two nodes (primary + one standby). Failover is safe with zero data loss. This is what we use for the Gitea production cluster—one standby must confirm each transaction while the other can lag without blocking commits.

**minSyncReplicas: 2** (maximum safety for 3+ instance clusters): Every transaction must be confirmed by two standbys before commit. This provides maximum durability but reduces availability—if one standby is down or slow, writes block. Typically used only for critical data where absolutely no loss is acceptable and you can tolerate occasional write unavailability.

For our 3-instance Gitea cluster, `minSyncReplicas: 1` provides the sweet spot: we get zero data loss during failover while still maintaining high availability even if one standby is temporarily unreachable.

## Monitoring replication health

Production PostgreSQL clusters require active monitoring of replication status. CloudNativePG provides metrics and logs, but direct PostgreSQL queries give you the most detailed real-time view of slot and replication health.

**Check replication slots status**:

```bash
kubectl exec -n gitea gitea-pg-ha-1 -- \
  psql -U postgres -c "
    SELECT slot_name,
           active,
           pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) as lag_size,
           restart_lsn
    FROM pg_replication_slots;"
```

This query shows:
- `slot_name`: The slot identifier (e.g., `_cnpg_gitea-pg-ha-2`)
- `active`: Whether a standby is currently using this slot
- `lag_size`: How much WAL data the standby is behind (in human-readable format)
- `restart_lsn`: The LSN from which the standby needs to resume

Red flags to watch for:
- Inactive slots with increasing lag_size indicate a standby that's offline but accumulating WAL backlog
- Lag sizes exceeding your disk capacity could lead to full disks
- Slots that remain inactive for extended periods might indicate permanently failed standbys

**Verify synchronous replication status**:

```bash
kubectl exec -n gitea gitea-pg-ha-1 -- \
  psql -U postgres -c "
    SELECT application_name,
           client_addr,
           state,
           sync_state,
           sent_lsn,
           write_lsn,
           flush_lsn,
           replay_lsn,
           replay_lag
    FROM pg_stat_replication;"
```

Key metrics:
- `sync_state`: Shows `sync` for synchronous standbys, `async` for asynchronous ones. With `minSyncReplicas: 1`, you should see one standby marked as `sync`
- `state`: Should be `streaming` for active replication
- `replay_lag`: Time delay between primary and standby replay (ideally milliseconds to seconds)
- LSN columns (`sent_lsn`, `write_lsn`, `flush_lsn`, `replay_lsn`): Show progression through the WAL pipeline. For sync replicas, these should be very close to each other

**Check standby receiver status** (run on standby pods):

```bash
kubectl exec -n gitea gitea-pg-ha-2 -- \
  psql -U postgres -c "
    SELECT status,
           received_lsn,
           received_tli,
           last_msg_receipt_time
    FROM pg_stat_wal_receiver;"
```

This confirms the standby is actively receiving WAL:
- `status`: Should be `streaming`
- `last_msg_receipt_time`: Should be recent (within seconds)
- `received_tli`: The timeline ID—this increments after each failover

**CloudNativePG operator logs** provide high-level HA events:

```bash
kubectl logs -n cnpg-system deployment/cnpg-controller-manager | grep gitea-pg-ha
```

Look for log entries about:
- Slot creation/deletion
- Failover events
- Cluster topology changes
- Reconciliation errors

Set up alerts for critical conditions:
- Any inactive replication slot for more than 5 minutes
- Replication lag exceeding your RTO (Recovery Time Objective)
- Synchronous standby count below `minSyncReplicas`
- Disk space on primary dropping below 20% (WAL accumulation risk)

Regular monitoring of these metrics ensures you catch replication issues before they cause outages or data loss.

## Key takeaways

Replication slots are a fundamental building block for reliable PostgreSQL high availability in Kubernetes. They solve the critical problem of WAL retention, ensuring standbys can always catch up after falling behind due to network issues, pod restarts, or other failures common in containerized environments.

CloudNativePG's automation around replication slots eliminates the operational burden of manual slot management. When you enable `highAvailability.enabled: true`, the operator:

- Automatically creates physical replication slots for all standbys
- Maintains slots through pod lifecycle events
- Recreates slots during failover
- Cleans up stale slots when you scale down

The combination of replication slots and synchronous replication (configured via `minSyncReplicas`) provides comprehensive protection:

- Slots ensure availability by preventing WAL gaps
- Synchronous replication ensures durability by guaranteeing transaction acknowledgment

For production deployments, monitor your replication health actively using PostgreSQL's built-in views (`pg_replication_slots`, `pg_stat_replication`, `pg_stat_wal_receiver`). Watch for inactive slots, growing lag, and mismatches between expected and actual sync replicas.

If you're setting up PostgreSQL in Kubernetes, understanding these internals helps you make informed configuration decisions and troubleshoot issues when they arise. For a complete guide to CloudNativePG setup including backup configuration, WAL archiving, and cost optimization, see my [comprehensive CloudNativePG post](/posts/databases/db-operator).
