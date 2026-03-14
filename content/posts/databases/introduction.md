---
title: 'Databases Management System'
date: 2026-03-05T10:37:04+07:00
draft: true
---

## Components

- transport layer (handle requests)
- query processor
- execution engine
- storage engine
  - Transaction Manager
  - Lock Manager: combine with TM to handle concurrency control
  - Access Methods: manage access and organizing data on disk
  - Buffer Manager: cache data pages
  - Recovery Manager

## Things to consider when comparing databases

- Schema and record sizes
- Number of clients
- Rates of read and write queries
- Types of queries and access pattern
- Expected changes in any of these variables

Knowing these variables can help to answer the following questions:

- Does the database support the required queries?
- Is this database able to handle the amount of data we’re planning to store?
- How many read and write operations can a single node handle?
- How many nodes should the system have?
- How do we expand the cluster given the expected growth rate?
- What is the maintenance process?

## Column- Versus Row-Oriented DBMS

- reading data with same type saves CPU & Mem - better compression
- use access pattern to decide: if scans span many rows, or compute aggregate over a subset of columns, it is worth considering a column-oriented approach.

## Wide Column Stores

data is represented as **multidimensional map**

![Example](images/wide-column-db.png)

## Data Files

### Implementation types

- heap organized tables (heap files): records stored randomly
- hashed organized tables (hashed files): records are hashed and stored in bucket according to the hash value
- index organized tables (IOT): stored in key order, range scans work by sequential scanning

read record speed increase but write decrease

## Index Files

Index Files contain data structure which act as a map to point out locations of records

an index of a record are primary key(index) which create a properties or a set of properties, and secondary index which can point directly to data record or store its primary index

data which is sort following the index order is call **clustering** while the one is not sorted call **non-clustering**

## Primary index as an indirection

secondary indexes point:

- directly to file offset (location where record is stored in a file)
- to primary index, increase disk seeks - pointer jump but reduce update cost
- hybrid: stores both file offset and primary key. On read, checks if the offset is still valid (1 disk seek); if stale, falls back to the primary key index and updates the cached offset. Cheaper than pure indirection on the happy path, but pays extra when records have moved — best suited for read-heavy workloads where records are rarely relocated.

![Illustration](images/primary-index-as-an-indirection.png)

## Buffering, Immutability, Ordering

distinctions and optimizations of storage data structure are based on these 3 concepts

### some implementations decide to avoid it to reduce

- complexity
- memory overhead
- data loss

## Glossary

### What is a transaction?

a sequence of database operations where all changes are either committed (success) or rolled back (fail), ensuring data consistency

### What is buffer?

a temporary storage area in memory

### what is a page?

the smallest unit of data that a database reads from/writes to disk or memory. a page contains multiple rows

### write-ahead log (WAL)

a durability mechanism to ensure **data consistency** even after crashes. There are 2 types: redo log, undo log

### Types

- OLTP - Online Transaction Processing: high-concurrency, short-lived read/write queries on individual records; ACID-compliant
- OLAP - Online Analytic Processing: data warehouse
- HTAP - Hybrid Transaction and Analytic Processing

## Q&A

### Why client/cluster communication do not share the same protocol?

node-to-node uses low-level language to communicate for speed, human requires a readable language (SQL)

## Why does a system need to implement a memory cache while it already has a buffer manager?

**Buffer manager** optimizes for general-purpose database workloads but still incurs overhead: query parsing, transaction locks, ACID logging. **Memory database** optimizes purely for speed with simple access patterns.

Examples:

- User session lookup: Database needs `SELECT * FROM sessions WHERE id=?` (parsing + planning). Cache does `GET session:123` (O(1) hash).
- Buffer manager caches what *fits*, but you can't control it. Memory database lets you explicitly cache hot data (trending posts, real-time counters).
- Database guarantees consistency (costs: locks, WAL logging). Cache trades consistency for speed—acceptable for data that doesn't need durability (session tokens, rate limits).

**Pattern**: Hot data → Redis (key-value, no ACID overhead) | Warm data → Database buffer manager | Cold data → Disk only

## Does a single node db cluster implement WAL?

## How does an application respond when the database crashes mid-processing? Does it keep the user waiting?

vacum
cost query
ACID
LOG
Aura share nothing
index (cluster, second, ...)
metric
detect deadlock, slow query
EVCC
transaction manager

<!-- anki
Q: What are the four main layers of a DBMS?
A: Transport layer (handles requests), Query Processor, Execution Engine, Storage Engine

Q: What are the five components of the Storage Engine in a DBMS?
A: Transaction Manager, Lock Manager, Access Methods, Buffer Manager, Recovery Manager

Q: What is the role of the Lock Manager in a DBMS?
A: Combines with the Transaction Manager to handle concurrency control

Q: What is the role of the Buffer Manager in a DBMS?
A: Caches data pages in memory to reduce disk I/O

Q: What is the role of Access Methods in a DBMS?
A: Manages access and organizes data on disk (e.g. B-trees, hash indexes)

Q: What 5 variables should you evaluate when comparing databases?
A: 1. Schema and record sizes 2. Number of clients 3. Rates of read and write queries 4. Types of queries and access pattern 5. Expected changes in any of these variables

Q: When should you choose a column-oriented database over row-oriented?
A: When queries scan many rows or compute aggregates over a subset of columns — column storage groups same-type data, improving compression and CPU/memory efficiency

Q: Why use an in-memory cache (e.g. Redis) when the database already has a Buffer Manager?
A: The buffer manager still incurs overhead: query parsing, transaction locks, ACID logging. A memory cache uses simple O(1) access patterns, explicit control over hot data, and no durability overhead — trading consistency for speed.

Q: Why do client-to-server and node-to-node communications in a database cluster use different protocols?
A: Node-to-node uses low-level protocols optimized for speed; client communication requires a human-readable language like SQL

Q: What is a database transaction?
A: A sequence of database operations where all changes are either committed (success) or rolled back (fail), ensuring data consistency

Q: What is a WAL and what two log types does it have?
A: Write-Ahead Log — a durability mechanism ensuring data consistency after crashes. Types: redo log (replay committed changes) and undo log (revert uncommitted changes)

C: The four main layers of a DBMS are {{c1::Transport Layer}}, {{c2::Query Processor}}, {{c3::Execution Engine}}, and {{c4::Storage Engine}}
tags: databases::dbms

C: The Storage Engine contains: {{c1::Transaction Manager}}, {{c2::Lock Manager}}, {{c3::Access Methods}}, {{c4::Buffer Manager}}, {{c5::Recovery Manager}}
tags: databases::dbms

C: A database {{c1::page}} is the smallest unit of data that a database reads from/writes to disk or memory; it contains multiple rows
tags: databases::storage

C: A database {{c1::buffer}} is a temporary storage area in memory used to cache data between disk and the application
tags: databases::storage

C: {{c1::WAL (Write-Ahead Log)}} is a durability mechanism that ensures data consistency even after crashes
tags: databases::durability

C: WAL has two log types: {{c1::redo log}} (replay committed changes) and {{c2::undo log}} (revert uncommitted changes)
tags: databases::durability

C: {{c1::OLTP}} (Online Transaction Processing) handles high-concurrency, short-lived read/write queries on individual records; ACID-compliant
tags: databases::types

C: {{c1::OLAP}} (Online Analytic Processing) is used for data warehousing and complex analytical queries over large datasets
tags: databases::types

C: {{c1::HTAP}} (Hybrid Transaction and Analytic Processing) combines both OLTP and OLAP capabilities in one system
tags: databases::types

C: Hot data → {{c1::Redis}} (key-value, no ACID overhead) | Warm data → {{c2::Database buffer manager}} | Cold data → {{c3::Disk only}}
tags: databases::caching

C: A {{c1::Wide Column Store}} represents data as a multidimensional map, where rows can have different sets of columns
tags: databases::types

Q: What is the difference between a page and a bucket in database storage?
A: A page is a fixed-size physical disk I/O unit (e.g. 4KB, 8KB) — how data is stored physically. A bucket is a logical grouping in hashed files identified by a hash value, mapping to one or more pages — how hashed files decide where to put a record.
tags: databases::storage

Q: Why are range scans efficient in IOTs but slow in heap files?
A: IOTs store records in key order on disk, so a range query reads pages sequentially (sequential I/O). Heap files scatter records randomly, requiring index pointer jumps across disk (random I/O).
tags: databases::storage

Q: When should you use hashed files over IOTs?
A: Use hashed files for exact-key lookups only (e.g. session_id = 'abc123'). Useless for range queries. Good fit: session stores, caches, user-by-id lookups.
tags: databases::storage

Q: How does a DBMS find a specific record within a bucket?
A: Two methods: (a) linear scan — bucket is small (1–few pages), DBMS reads all records and compares keys; (b) sorted scan — records inside bucket are sorted, DBMS does binary search. If bucket grows too large from collisions, DBMS splits it (extendible hashing / overflow handling).
tags: databases::storage

Q: What is the time complexity of a point lookup in a hashed file vs an IOT?
A: Hashed file: O(1). IOT: O(log n). But only IOTs support range queries.
tags: databases::storage

C: A database {{c1::page}} is a fixed-size physical disk I/O unit; a {{c2::bucket}} is a logical grouping in hashed files identified by a hash value
tags: databases::storage

C: In a hashed file, the {{c1::hash value}} of a key determines which {{c2::bucket}} a record belongs to
tags: databases::storage

C: IOTs enable fast range scans because records are stored in {{c1::key order}} on disk, allowing {{c2::sequential I/O}}
tags: databases::storage

C: Heap files require {{c1::random I/O}} for range scans because records are scattered and located via {{c2::index pointer jumps}}
tags: databases::storage

C: Hashed files are optimized for {{c1::exact-key lookups}} and are useless for {{c2::range queries}}
tags: databases::storage

C: When a bucket grows too large due to collisions, the DBMS splits it — this is called {{c1::overflow handling}} or {{c2::extendible hashing}}
tags: databases::storage

Q: What is the purpose of the redo log?
A: Crash recovery — it records the new values of changes so that committed transactions can be replayed after a crash, even if the data pages weren't flushed to disk yet.
tags: databases::wal

Q: What is the purpose of the undo log?
A: Two purposes: (1) rollback — reverting uncommitted transactions by restoring old values; (2) MVCC — giving concurrent readers a consistent snapshot of data before a write.
tags: databases::wal

Q: What is Write-Ahead Logging (WAL)?
A: The principle that the redo log must be written and flushed to disk BEFORE the corresponding data page change is applied. This guarantees durability even if the process crashes mid-write.
tags: databases::wal

Q: What does the database do with the redo log on startup after a crash?
A: It replays the redo log to reapply all committed changes that hadn't yet been written to data pages, then uses the undo log to roll back any incomplete (uncommitted) transactions.
tags: databases::wal

Q: How does the undo log enable MVCC (Multi-Version Concurrency Control)?
A: When a row is modified, the old value is saved in the undo log. Concurrent readers can follow undo log pointers to reconstruct an older version of the row consistent with their transaction's start time — without blocking writers.
tags: databases::wal::mvcc

Q: When is the redo log safe to discard?
A: After a checkpoint — when all dirty pages covered by that log segment have been flushed to disk. The DB no longer needs to replay those changes on recovery.
tags: databases::wal

Q: When is the undo log safe to discard?
A: After the transaction commits AND no other active transaction needs the old snapshot for MVCC reads. Long-running reads can delay undo log cleanup.
tags: databases::wal

Q: What is the difference between redo and undo logs in terms of what they store?
A: Redo log stores new values (after-image); undo log stores old values (before-image).
tags: databases::wal

Q: In InnoDB, where are the redo log and undo log physically stored?
A: Redo log: `ib_logfile0`, `ib_logfile1` (or `#ib_redo*` in MySQL 8+). Undo log: system tablespace (`ibdata1`) or dedicated undo tablespaces (`undo_001`, `undo_002`).
tags: databases::wal::innodb

C: The redo log records {{c1::new values (after-image)}}; the undo log records {{c2::old values (before-image)}}
tags: databases::wal

C: {{c1::Write-Ahead Logging (WAL)}} requires the log to be written to disk BEFORE changes are applied to data pages
tags: databases::wal

C: On crash recovery, the DB {{c1::replays}} the redo log for committed transactions and {{c2::rolls back}} incomplete transactions using the undo log
tags: databases::wal

C: The undo log enables {{c1::MVCC}} by allowing readers to reconstruct older row versions without blocking writers
tags: databases::wal::mvcc

C: The redo log is discarded after a {{c1::checkpoint}}, when dirty pages have been flushed to disk
tags: databases::wal

C: The undo log is discarded after the transaction {{c1::commits}} AND no active transaction needs the old snapshot for {{c2::MVCC reads}}
tags: databases::wal

C: In InnoDB, the redo log is stored in {{c1::ib_logfile*}} files; the undo log is stored in {{c2::ibdata1}} or dedicated {{c3::undo tablespaces}}
tags: databases::wal::innodb
-->
