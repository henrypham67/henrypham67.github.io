---
title: 'ETCD'
date: 2024-10-26T16:00:33+07:00
draft: true
tags: ["kubernetes"]
flashcards:
  - q: "Why do etcd clusters use an odd number of members (3, 5, 7)?"
    a: "Raft requires a majority quorum to commit writes. With N members, the cluster tolerates floor((N-1)/2) failures. An even-numbered cluster gains no fault-tolerance over the odd one below it (4 tolerates 1, same as 3) while adding network/disk overhead and a higher chance of split votes."
  - q: "What is the role of the WAL (write-ahead log) in etcd?"
    a: "Every Raft proposal is appended to the WAL on disk before being applied to the in-memory state. On restart or crash, etcd replays the WAL to rebuild state. WAL fsync latency is the single biggest determinant of etcd write throughput."
  - q: "What does etcd compaction do, and why is it required?"
    a: "etcd keeps every revision of every key (MVCC) so watchers can stream history. Compaction discards revisions older than a chosen point so the keyspace doesn't grow unbounded. Without compaction, etcd hits its storage quota and goes read-only."
  - q: "What is the difference between compaction and defragmentation?"
    a: "Compaction logically deletes old revisions from the keyspace, but the freed space stays inside the boltdb file as fragmentation. Defragmentation rewrites the file to reclaim that space on disk. Defrag is per-member, blocks that member, and should be done one node at a time."
  - q: "How does the etcd quota (--quota-backend-bytes) protect the cluster?"
    a: "When the backend database file exceeds the quota (default 2 GiB), etcd raises a NOSPACE alarm and rejects writes cluster-wide until the operator compacts, defragments, and disarms the alarm. The quota prevents runaway growth from making the cluster unrecoverable."
  - q: "Why is etcd latency-sensitive to disk fsync rather than throughput?"
    a: "Raft must fsync each log entry before acknowledging a write — commit latency is bounded by the slowest fsync in the quorum. SSDs with low fsync latency outperform high-bandwidth HDDs. Recommended: p99 fsync < 10 ms (etcd's wal_fsync_duration_seconds metric)."
  - q: "What happens during a Raft leader election in etcd?"
    a: "If followers don't hear a heartbeat within the election timeout, one transitions to candidate, increments its term, and requests votes. A node grants its vote only if the candidate's log is at least as up-to-date as its own. The candidate with majority votes becomes leader and resumes serving writes."
quiz:
  title: "etcd Internals Quiz"
  questions:
    - q: "An etcd 5-node cluster has 2 members down. What is its state?"
      options:
        - "Read-only — quorum lost"
        - "Fully available — 3 members still form a majority"
        - "Read-only until the leader is re-elected"
        - "Unavailable — any failure breaks 5-node Raft"
      correct: 1
    - q: "Your etcd cluster keeps hitting the 2 GiB quota despite running periodic compaction. What's the missing step?"
      options:
        - "Restart the leader to flush memory"
        - "Run defragmentation — compaction alone doesn't reclaim disk space"
        - "Increase the WAL retention window"
        - "Disable MVCC watchers"
      correct: 1
    - q: "Which metric is the best single indicator of etcd write-path health?"
      options:
        - "etcd_server_proposals_committed_total"
        - "etcd_disk_wal_fsync_duration_seconds"
        - "etcd_network_peer_round_trip_time_seconds"
        - "etcd_mvcc_db_total_size_in_bytes"
      correct: 1
    - q: "Why should etcd members run on dedicated low-latency SSDs, not shared volumes?"
      options:
        - "etcd requires a specific filesystem block size"
        - "Raft commits block on fsync — slow or jittery disks cap cluster write latency"
        - "Shared volumes cannot expose enough IOPS"
        - "etcd refuses to start on network-attached storage"
      correct: 1
    - q: "You take a snapshot with `etcdctl snapshot save`. What does it contain?"
      options:
        - "Only the keys in the default namespace"
        - "A point-in-time copy of the boltdb backend, restorable to a new cluster"
        - "The WAL files only — state must be replayed"
        - "Encrypted secrets only"
      correct: 1
---

## Definition

```text
etcd is a consistent and highly-available key value store used as Kubernetes' backing store for all cluster data.
```

1. How is ETCD used in the Kubernetes' control plane?
   - It's used to store and manage the configuration data
2. How is ETCD used to store Kubernetes cluster data?
      - API server act as an interface to interact with the client and others components
3. How is ETCD crucial to Kubernetes?
   - Etcd allows clients to subscribe to changes to a particular key or set of key
