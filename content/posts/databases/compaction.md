---
title: "Compaction"
date: 2026-03-22T09:42:59+07:00
draft: true
tags: ["databases", "storage", "compaction", "vacuum"]
categories: ["Databases"]
---

## 1. The headline

**Vacuum and maintenance** is the database's janitorial crew — background processes that clean up dead data, reclaim wasted space, and keep B-Tree pages organized so reads and writes stay fast.

## 2. The analogy

Think of a B-Tree page like a **bookshelf in a library**. When you remove a book (delete a record), you don't immediately slide all the other books over to close the gap — that would be too slow during a busy day. Instead, you just pull the book out and leave the gap. Over time, your shelf is full of gaps: there's technically enough space for new books, but the empty spots are scattered everywhere, so you can't fit a thick new book in any single gap.

**Vacuum is the librarian who comes in after hours**, consolidates all the books to one side of the shelf, and reclaims that fragmented space into one clean, usable block. That's page defragmentation.

## 3. How it actually works (step by step)

Here's what happens inside a B-Tree page as data changes over time:

```
BEFORE cleanup:

 Cell offsets   Free space       Live cells      Dead cells (garbage)
 ┌──┬──┬──┐   ┌──────────┐   ┌──┬──┬──┐      ┌──┬──┐
 │ •│ •│ •│   │          │   │  │  │  │      │xx│xx│
 └──┴──┴──┘   └──────────┘   └──┴──┴──┘      └──┴──┘
  ↓  ↓  ↓                     ↑  ↑  ↑
  (point to live cells only — dead cells are unreachable)
```

1. **A delete happens.** The database removes the cell's offset pointer from the header, but the actual cell data stays on the page. It's now **garbage** — nonaddressable, unreachable from the root.

2. **An update happens.** At the leaf level, the old version of the cell stays on the page (it may be needed for MVCC — multiversion concurrency control). A new version is written. Now you have two copies, only one addressable.

3. **A page split happens.** Cells whose offsets were truncated become unreachable — more garbage.

4. **Fragmentation builds up.** The page has enough *logical* free space but not enough *contiguous* free space to fit a new cell.

5. **Vacuum kicks in.** The process walks the page, identifies live vs. dead cells, then **rewrites the page**: live cells are copied in logical (sorted) order, dead cells are discarded, and free space becomes one contiguous block.

6. **Freed pages go to the free page list** (a.k.a. *freelist*). When pages are rewritten, unused in-memory pages return to the page cache. On-disk freed pages get tracked in the freelist so they can be reused. This freelist must be persisted to survive crashes.

## 4. Show it in action

PostgreSQL exposes vacuum directly:

```sql
-- See dead tuples (garbage) in a table
SELECT relname, n_dead_tup, n_live_tup, last_vacuum, last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY n_dead_tup DESC;

-- Manually trigger vacuum on a specific table
VACUUM VERBOSE my_table;

-- VACUUM FULL rewrites the entire table (reclaims disk space, but locks the table)
VACUUM FULL my_table;

-- In SQLite, the equivalent is:
-- PRAGMA freelist_count;  -- shows number of free pages
-- VACUUM;                 -- rebuilds the entire database file
```

## 5. Common beginner traps

**"Deleting rows frees disk space."** Nope. A `DELETE` removes the pointer (cell offset), but the data stays on the page as garbage. You need vacuum/compaction to actually reclaim that space. In PostgreSQL, even `VACUUM` only marks space as reusable internally — you need `VACUUM FULL` to shrink the file on disk.

**"Vacuum is only about deletes."** Updates cause fragmentation too. In MVCC databases like PostgreSQL, an `UPDATE` creates a new tuple version while the old one becomes a dead tuple. Heavy-update workloads can fragment pages faster than heavy-delete workloads.

**"I should run VACUUM FULL all the time."** `VACUUM FULL` rewrites the entire table and takes an exclusive lock — it blocks all reads and writes. Regular `VACUUM` (or autovacuum) is non-blocking and usually sufficient. Reserve `VACUUM FULL` for extreme bloat situations.

## 6. The mental model

> Think of vacuum as the database's garbage collector: deletes and updates leave behind dead data on pages, and vacuum is the background process that sweeps it up and makes the space usable again — just like a GC in a programming language reclaims memory from objects no longer referenced.

## 7. How to apply it (right now)

**Mini-project (10 min):** Spin up a PostgreSQL container and watch fragmentation happen live:

```bash
docker run -d --name pg-vacuum -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16

psql -h localhost -U postgres -c "
  CREATE TABLE bloat_test (id serial PRIMARY KEY, data text);
  INSERT INTO bloat_test (data) SELECT md5(random()::text) FROM generate_series(1,10000);
"

# Check initial state
psql -h localhost -U postgres -c "SELECT pg_size_pretty(pg_total_relation_size('bloat_test'));"
psql -h localhost -U postgres -c "SELECT n_dead_tup, n_live_tup FROM pg_stat_user_tables WHERE relname='bloat_test';"

# Delete half the rows — creates dead tuples
psql -h localhost -U postgres -c "DELETE FROM bloat_test WHERE id % 2 = 0;"

# Check again: dead tuples appeared, but table size didn't shrink!
psql -h localhost -U postgres -c "SELECT n_dead_tup, n_live_tup FROM pg_stat_user_tables WHERE relname='bloat_test';"

# Run vacuum and see the cleanup
psql -h localhost -U postgres -c "VACUUM VERBOSE bloat_test;"
```

**Real-world scenario:** You're on-call and get alerted that a PostgreSQL database's disk usage keeps growing even though the app isn't storing more data. You run `SELECT n_dead_tup FROM pg_stat_user_tables ORDER BY n_dead_tup DESC` and discover millions of dead tuples — autovacuum is falling behind on a high-churn table. The fix: tune `autovacuum_vacuum_scale_factor` and `autovacuum_vacuum_cost_delay` for that specific table so autovacuum runs more aggressively.

**How it connects:** This ties directly to **MVCC** (Chapter 5 of this book) — the reason dead tuples exist at all is because old versions are kept around for concurrent transactions. It also connects to **B-Tree page structure** (the slotted pages from Chapter 3) — vacuum is what maintains those pages. If you've worked with **LSM-trees** (like in RocksDB or Cassandra), compaction serves the same purpose but works differently: instead of rewriting pages in-place, it merges sorted files.

## 8. Next steps

1. **Read about autovacuum tuning** — understand `autovacuum_vacuum_threshold`, `scale_factor`, and `cost_delay` in PostgreSQL. These are the knobs you'll actually tune in production.
2. **Explore MVCC** (pages 98-99 of this same book) — understanding *why* dead tuples exist gives you the full picture of when vacuum matters most.
3. **Compare with LSM-tree compaction** — read about how databases like RocksDB handle the same problem with a fundamentally different strategy (merging sorted runs instead of rewriting pages in-place).