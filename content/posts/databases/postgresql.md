---
title: "PostgreSQL"
date: 2026-03-24T00:00:00+07:00
draft: true
tags: ["databases", "postgresql", "storage", "dbms"]
categories: ["Databases"]
---

## Least Recently Used - LRU

strong temporal locality

### Approach

```text
Hash Map: { page_id → node pointer }     ← O(1) lookup
Doubly Linked List: [MRU] ←→ ... ←→ [LRU]  ← O(1) move to front
```

### Disadvantages

- frequent used pages could be evicted - sequential scan floods pages into the buffer pool and evict your actually-hot working set, even though each scan page will never be needed again. Working set (hot): [customers: freq=500] [orders: freq=300]
- no frequency awareness
- lock contention

## Least Frequently Used - LFU

stable, long-term popularity

### Approach

**Naive — Min-Heap:**

```text
key_map (hashmap):
    key → pointer/index to heap node

Heap sorted by frequency count
          [freq=1: page_7]
         /                \
  [freq=3: page_2]   [freq=5: page_9]
```

- Access a page → increment its count → re-heapify → O(log n)
- Evict → always pop the min → O(log n)

**Better — Frequency Buckets (O(1) LFU):**

```text
freq_map: { page_id → frequency }

Bucket List (doubly linked by frequency):
[freq=1] <-> [freq=2] <-> [freq=5]
   |               |           |
   v               v           v
[page_3]       [page_1]    [page_9]   ← each bucket's own DLL
[page_7]

min_freq pointer: 1
```

### Disadvantages

- frequent used pages which are no longer use now
- new page starts at freq=1 and could get immediately evicted on the next miss
- Higher implementation cost - Every access touches 3 data structures (freq_map, bucket[f], bucket[f+1]) and requires a lock on each to prevent race conditions. At thousands of queries/second, threads are constantly contending for these locks.

## Clock-sweep cache

- pages are organized in a circle, each page will have `usage_count` (0-5)
- whenever clock hand go through a page, its `usage_count` will be decreased and increased when accessed
- in case of page is pinned (in the middle of a transaction), its `usage_count` will not be decreased if clock hand go through

<iframe
  src="/demos/postgres_clock_sweep_interactive_1.html"
  width="100%"
  height="950"
  style="border: 1px solid #ccc; border-radius: 4px;"
  loading="lazy">
</iframe>

## PostgreSQL Statistics System

- Activity statistics
  - db performance
- Planner statistics
  - written in `pg_statistic` for Query Planner to come up with optimized plan
  - trigger manually or via auto-vacuum

how to scale up down, in out
back up (full, PIT)
monitoring
HA






- Each bucket is itself an LRU list (tie-break by recency)
- Access page → move from `bucket[f]` to `bucket[f+1]`
- Evict → look at `bucket[min_freq]`, remove tail

**Real-world use:** Redis supports both `allkeys-lru` and `allkeys-lfu` eviction modes. PostgreSQL uses **clock-sweep** — a hardware-inspired approximation of LRU that avoids the overhead of a full linked list.

---

### 4. Show It in Action

```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.cache = OrderedDict()  # preserves insertion order

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1  # cache miss → go to disk
        self.cache.move_to_end(key)  # mark as recently used
        return self.cache[key]

    def put(self, key: int, value: int):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.cap:
            self.cache.popitem(last=False)  # evict LRU (front)

cache = LRUCache(3)
cache.put(1, "page_1")
cache.put(2, "page_2")
cache.put(3, "page_3")
cache.get(1)           # access page_1 → moves to front
cache.put(4, "page_4") # evicts page_2 (now the LRU)
```

---

### 5. Common Beginner Traps

**Trap 1:** "LFU is always better because frequent pages stay in cache."  
Actually, LFU suffers from **cache pollution** — a page accessed 1000 times last week but never again will sit in cache forever, blocking fresh hot pages. LRU handles workload shifts better.

**Trap 2:** "Databases use pure LRU."  
No major database uses textbook LRU. They use approximations (clock-sweep, two-queue, ARC) because exact LRU requires a lock on every single page access — catastrophic at scale.

**Trap 3:** "The buffer pool is just a cache."  
The buffer pool is more critical than a regular cache — a **dirty page** (modified but not yet written to disk) *must* be flushed before eviction, or you lose data. Eviction isn't free.

---

### 6. The Mental Model

> The buffer pool is a bouncer at a club with a fixed guest list: LRU throws out whoever has been standing at the back the longest; LFU throws out whoever visited the fewest times — but both policies only matter when the club is *full*.

---

### 7. How to Apply It

**Mini-project (10 min):** Implement both LRU and LFU caches in Python and test with the same access pattern — try a repeated scan (1,2,3,4,1,2,3,4...) and a hot-spot pattern (1,1,1,2,2,3). Which evicts better for each?

**Real-world scenario:** You're debugging why a Postgres query suddenly got slow. Run:
```sql
SELECT buffers_hit, buffers_read FROM pg_stat_statements WHERE query LIKE '%your_table%';
```
A high `buffers_read` / low `buffers_hit` ratio means your working set no longer fits in `shared_buffers` — the clock-sweep eviction is kicking out pages you need. The fix: increase `shared_buffers` or partition the hot data.

**How it connects:** This ties directly to **B-tree page management** — when a B-tree traversal needs to read an inner node, it first checks the buffer pool. Understanding eviction explains why sequential scans can thrash the cache (a known issue called the **buffer pool pollution** problem).

---

### 8. Next Steps

1. **Read:** PostgreSQL docs on [shared_buffers and clock-sweep](https://www.postgresql.org/docs/current/runtime-config-resource.html) — see how a real system tunes this
2. **Implement:** Solve [LeetCode #460 LFU Cache](https://leetcode.com/problems/lfu-cache/) using the frequency-bucket approach — it forces you to handle the O(1) constraint
3. **Deep dive:** Study **ARC (Adaptive Replacement Cache)** — used in ZFS and some databases — which combines LRU and LFU dynamically based on workload patterns