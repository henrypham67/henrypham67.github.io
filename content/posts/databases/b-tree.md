---
title: 'B-Tree'
date: 2026-03-08T09:10:01+07:00
draft: true
---

## BST

### Tree Balancing

insertion, update could imbalance the tree
-> rotate the middle node after 2 consecutive insertion

### Trees on-disk storage issues

- low fan-out (maximum number of children nodes)
- high tree height create high seek time during traversal

#### HDD

- transfer unit *sector* (512 bytes - 4 Kb)
- head positioning (the read/write head physically moves to the location on the spinning disk where data is stored) is the most expensive operation

#### SSD

- Memory cell: a physical unit stores 1-3 bits
- String: 32-64 cells chained
- Array: combination of strings
- Plane: a group of blocks that share read/write circuits. Multiple planes can operate in parallel within the same chip
- Die: 

```text
- Cell → String (32-64 cells) → Array → Page (2-16 KB) → Block (64-512 pages) → Plane → Die
- Database page (8-16 KB)
  └── OS page (4 KB)
      └── SSD page (2-16 KB)  ← hardware
      └── HDD sector (512 B – 4 KB)  ← hardware
```

- Can only write to empty cells
- Can only erase blocks

### why don't we store BST nodes in the same page to reduce disk seeks?

- each level per page, we still have to load multiple pages because it follows a root-to-leaf path
- 1 path per node, we either duplicate nodes or have the same disk seeks (in worst case scenario)
- all level in 1 page, we have B-Tree (without balancing, ordered keys, split logic)

## Paged Binary Tree

- reduce locality problem
- BUT have ordering, balancing, page reorganize issues

## B-Tree

Opposite to BST, B-Tree is built bottom up. It contains 3 types:

- Root node
- Internal nodes
- Leaf nodes

higher fan-out
-> amortize structural changes when balancing (splits, merges) - triggered when node are full or nearly empty
-> reduce disk seeks

### How many internal nodes level are there in B-Tree?

The number of internal node levels depends on the **tree height**, which is determined by the **branching factor** (degree, fan-out) and the number of keys stored.

**Key concept:**
- **Internal nodes** = all nodes except leaf nodes
- If a B-Tree has height `h`, there are **`h-1` internal node levels** and **1 leaf level**

**Example:**
A B-Tree of height 3:

```text
Level 0: Root (internal node)        ← internal level
Level 1: Internal nodes               ← internal level
Level 2: Leaf nodes                   ← leaf level (not internal)
```

Total internal levels = 3 - 1 = **2 levels**

**Why this matters:**

- More internal levels = deeper tree = more disk seeks
- B-Trees are designed to minimize height by maximizing branching factor
- With large fan-out (N), a B-Tree stays shallow even with millions of keys
  - Example: B-Tree with degree 100 and 1 million keys has height ≈ 3-4, so only 2-3 internal levels

### Which factor decide the a node occupancy (number of keys & node capacity)?

Disk block (page) size, because 1 node per page

## B+-Tree

a B-Tree which data is stored at leaf, keys store at internal nodes

### Compare to B-Tree

data is only at leaf, benefits:

- simple for range scan, after locate the starting leaf you only need to follow the next pointers until the range predicate is exhausted
- internal nodes can store more keys -> shallower tree, less disk seeks

### N keys and N+1 pointers

Keys divide the search range into (N+1) partitions. Each partition needs a pointer to a child subtree.

Example: 3 keys (10, 20, 30) create 4 zones:
- < 10 (Ptr₀)
- 10-20 (Ptr₁)
- 20-30 (Ptr₂)
- ≥ 30 (Ptr₃)

**Factors influencing N:**
- **Page size** (larger page → more keys fit)
- **Key size** (smaller keys → more keys per node)
- **Pointer size** (typically 8 bytes)
- **Overhead** (metadata, headers)

Formula: `N ≈ (Page Size - Overhead) / (Key Size + Pointer Size)`

Without the extra pointer, one zone would be unreachable.

## Summary

- How B-Tree solves low fan-out and random location on disk of BST
- B-Tree's techniques to balance the tree

## Notice

- 1,2,3: Learn about Page Caching and I/O amplification. If you’re configuring a Kubernetes Persistent Volume for a database, knowing how the database writes to disk helps you choose the right IOPS tier.
- 5: WAL is what makes replication and point-in-time recovery possible. If a database pod crashes, the WAL is what the system uses to restore consistency. Focus on Checkpointing—it's the secret to reducing database startup times after a failure.
- 4, 6: Understand Indexes. For a Platform Engineer, an index isn't just a query tool; it's a trade-off between Read Performance and Write Latency/Disk Space.
- 8, 9, 11: Focus on Leader-Follower Replication and Consensus. If you are setting up a High Availability (HA) Postgres or MySQL cluster using tools like Patroni or Orchestrator, these chapters explain the logic those tools use to elect a new leader

| Course Topic             | Petrov Chapter | DevOps Relevance                      | Priority |
| :----------------------- | :------------- | :------------------------------------ | :------- |
| Physical Design          | Ch 1-3         | Storage Config, IOPS, Page Sizing     | High     |
| Transactions/ACID        | Ch 5           | Backup/Restore, WAL, Crash Recovery   | Critical |
| Indexing                 | Ch 4 & 6       | Solving CPU Spikes, Capacity Planning | High     |
| Query Optimization       | N/A            | Observability, Slow Query Logs        | Medium   |
| Big Data / Dist. Systems | Ch 8-14        | Sharding, Replication, HA Clusters    | Critical |
| Data Modelling / ER      | N/A            | Schema Migrations (CI/CD)             | Low      |
