---
title: 'Durability and troubleshooting'
date: 2026-05-12T09:40:00+07:00
draft: true
tags: [linux, fsync, journaling, page-cache, disk-full, logs]
categories: [Linux]
flashcards:
  - q: "Why might `df` report a disk as full while `du` shows much less usage?"
    a: "A process still has an open file descriptor to a deleted file, so the kernel keeps the blocks allocated until the process closes it or restarts. Find it with `lsof +L1`."
  - q: "What does `fsync()` do and why do databases depend on it?"
    a: "`fsync()` forces dirty page-cache data and metadata for a file to be flushed to stable storage. Databases call it to guarantee that committed writes survive a crash or power loss."
  - q: "What are the three ext4 journaling modes and how do they differ?"
    a: "`data=writeback` (fastest, only metadata journaled — data can lag), `data=ordered` (default — metadata journaled, data written before metadata), `data=journal` (safest — both data and metadata journaled, slowest)."
  - q: "Why is `free -h`'s 'available' column more meaningful than 'free'?"
    a: "Linux deliberately uses 'free' RAM for the page cache to speed up reads. 'available' reports what could actually be reclaimed for new allocations, which is what matters for capacity planning."
  - q: "What do `vm.dirty_ratio` and `vm.dirty_background_ratio` control?"
    a: "They cap how much memory can hold un-flushed (dirty) writes. Background ratio triggers writeback in the background; dirty_ratio forces writers to block and flush synchronously. Tuning them controls latency spikes vs throughput."
  - q: "What does `O_DIRECT` do, and which workloads use it?"
    a: "It bypasses the kernel page cache, doing I/O directly between the application's buffer and disk. Databases (Oracle, MySQL InnoDB) use it to manage their own cache and avoid double-buffering."
  - q: "Why is the ext4 default of reserving 5% blocks for root sometimes wasteful?"
    a: "On a multi-TB data volume that root doesn't use, that's tens of GB held back. Disable it with `tune2fs -m 1 /dev/...` (or `-m 0`) on pure data volumes. Keep it on root filesystems so the system can recover if it fills up."
  - q: "What's the difference between logrotate's `create` and `copytruncate` modes?"
    a: "`create` renames the old log and makes a new file — the app must reopen its log handle (typically via a signal in `postrotate`). `copytruncate` copies the log and truncates the original in place — no signal needed, but writes during the copy can be lost."
  - q: "What command tail-follows logs for a specific systemd unit?"
    a: "`journalctl -u <unit> -f`. Add `--since '1 hour ago'` or `-p err` to filter."

quiz:
  title: "Durability and Troubleshooting Quiz"
  questions:
    - q: "A server reports 100% disk full, but `du -sh /` shows only 40% used. What is the most likely cause?"
      options:
        - "The filesystem journal is corrupted"
        - "A deleted file is still held open by a running process"
        - "The kernel page cache is full"
        - "Inodes are exhausted"
      correct: 1
    - q: "Which command identifies which process is holding a deleted file open?"
      options:
        - "`df -i`"
        - "`du -xhd1 /`"
        - "`lsof +L1`"
        - "`fsck -y`"
      correct: 2
    - q: "Which statement about `fsync()` is correct?"
      options:
        - "It flushes only metadata, not file data"
        - "It bypasses the page cache entirely on read and write"
        - "It forces dirty data and metadata for a file to stable storage"
        - "It is automatically called after every `write()` syscall"
      correct: 2
    - q: "Which ext4 journaling mode provides the strongest crash safety at the cost of write throughput?"
      options:
        - "`data=writeback`"
        - "`data=ordered`"
        - "`data=journal`"
        - "`data=async`"
      correct: 2
    - q: "Your monitoring shows `free -h` reporting near-zero 'free' memory but 'available' is high. What does this indicate?"
      options:
        - "The system is about to OOM"
        - "Memory is being used by the page cache and is reclaimable on demand"
        - "Swap is full"
        - "A process is leaking memory"
      correct: 1
---

# Durability and Troubleshooting

## Journaling, Caching, Durability

- **Journaling** records intent before writing data, so a crash doesn't corrupt structure. ext4 modes: `data=ordered` (default), `journal` (safest, slowest), `writeback` (fastest, riskier).
- **Page cache** — Linux caches file data in RAM aggressively. `free -h` "available" is what matters, not "free".
- **Dirty pages** are flushed by `pdflush`/writeback threads. Tunables: `vm.dirty_ratio`, `vm.dirty_background_ratio`.
- **`fsync()`** forces durability to disk. Databases live and die by this. Cloud disks lie about it sometimes.
- **`O_DIRECT`** bypasses page cache. Used by databases that manage their own cache.
- **Barriers / FUA** — ensure ordering of writes through the disk's write cache.

## Disk Full — The Daily SRE Pain

**`df` says full, `du` says not full** — classic. Reasons:

1. A deleted file still held open by a process — `lsof +L1` to find it.
2. Files hidden under a mount point — unmount and check.
3. Reserved blocks (ext4 reserves 5% for root by default — `tune2fs -m 1`).
4. Inode exhaustion — `df -i`.

### Standard investigation

```bash
df -h                          # which mount
df -i                          # inodes
du -xhd1 /var | sort -h        # don't cross filesystems
ncdu /var                      # interactive
lsof +L1                       # deleted-but-open
```

**Common offenders:** `/var/log/journal`, Docker layers (`/var/lib/docker`), unrotated logs, kernel packages in `/boot`, core dumps.

## Logs, Rotation, Journald

- **rsyslog / syslog-ng** — traditional log daemons.
- **systemd-journald** — binary structured logs. `journalctl -u nginx -f`, `--since`, `--vacuum-time=7d`.
- **logrotate** — `/etc/logrotate.d/*`. Watch for postrotate scripts that signal apps to reopen log files (`copytruncate` vs `create`).
- Persistent journal: `/var/log/journal` must exist; otherwise it's RAM-only.
