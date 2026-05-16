---
title: 'Performance, backup, security'
date: 2026-05-12T10:00:00+07:00
draft: true
tags: [linux, performance, iostat, rsync, snapshots, selinux, hardening]
categories: [Linux]
flashcards:
  - q: "Which `iostat` columns matter most when diagnosing disk saturation?"
    a: "`%util` (how busy the device is), `await` (average I/O latency in ms), `r/s` and `w/s` (IOPS). A device pegged at 100% util with rising await is your bottleneck."
  - q: "What does `vmstat`'s `wa` column tell you?"
    a: "Percentage of CPU time spent waiting for I/O. Persistently high `wa` means the workload is disk-bound, not CPU-bound."
  - q: "Why are LVM snapshots dangerous if left around indefinitely?"
    a: "LVM snapshots are copy-on-write — every write to the origin volume duplicates the old block to the snapshot's reserved space. Long-lived snapshots cause write amplification, fill the snapshot, and can corrupt it when it overflows."
  - q: "What rsync flag combination preserves hard links, ACLs, and extended attributes?"
    a: "`rsync -aHAX --delete`. `-a` = archive, `-H` = hard links, `-A` = ACLs, `-X` = xattrs, `--delete` = remove files at destination that no longer exist at source."
  - q: "Why is a filesystem snapshot of a running database only 'crash-consistent', not 'application-consistent'?"
    a: "The snapshot captures whatever was on disk at that instant — including half-written transactions in the WAL. Restoring it is equivalent to recovering from a power loss. For a clean backup, quiesce the database or use its native backup tool (`pg_basebackup`, `mysqldump`)."
  - q: "What command finds all SUID/SGID binaries on the local filesystem (skipping mounts)?"
    a: "`find / -xdev \\( -perm -4000 -o -perm -2000 \\) -type f`. The `-xdev` flag prevents crossing into other mounted filesystems."
  - q: "What is `fio` used for and why does workload matching matter?"
    a: "`fio` is a synthetic I/O benchmarking tool. To get useful numbers, you must match the real workload's block size, queue depth, sync vs async, and read/write mix — otherwise you measure something irrelevant."

quiz:
  title: "Performance, Backup, Security Quiz"
  questions:
    - q: "Which tool gives you per-device I/O latency and utilization in real time?"
      options:
        - "`vmstat 1`"
        - "`iostat -xz 1`"
        - "`free -h`"
        - "`ps aux`"
      correct: 1
    - q: "Which rsync invocation correctly preserves hard links and extended attributes?"
      options:
        - "`rsync -av`"
        - "`rsync -aHAX --delete`"
        - "`rsync -rt`"
        - "`rsync --hard-links --xattrs` (no other flags)"
      correct: 1
    - q: "Why is a `cp -a` snapshot of a running Postgres data directory unsafe as a backup?"
      options:
        - "It uses too much disk space"
        - "It can't preserve file permissions"
        - "It captures inconsistent state mid-transaction — only crash recovery on restore"
        - "Postgres locks the directory and `cp` will fail"
      correct: 2
    - q: "Which command finds world-writable files on the local filesystem only?"
      options:
        - "`find / -perm 0777 -type f`"
        - "`find / -xdev -perm -0002 -type f`"
        - "`ls -laR / | grep rwxrwxrwx`"
        - "`stat -c %a /*`"
      correct: 1
---

# Performance, Backup, Security

## Performance and Observability

- **`iostat -xz 1`** — per-device I/O. Watch `%util`, `await`, `r/s`, `w/s`.
- **`iotop`** — per-process I/O.
- **`vmstat 1`** — `bi`/`bo` blocks in/out, `si`/`so` swap, `wa` I/O wait.
- **`pidstat -d 1`** — per-process disk I/O.
- **`blktrace` / `bpftrace` / `biolatency`** — deep-dive block layer.
- **`fio`** — synthetic I/O benchmarking. Match your workload (block size, queue depth, sync vs async).
- **`strace -e trace=file -p <pid>`** — what files is a process touching?
- **`fuser`, `lsof`** — who's holding this file/mount?

## Backup and Snapshots

- **rsync** with `-aHAX --delete` preserves hard links, ACLs, xattrs.
- **LVM snapshots** — copy-on-write, point-in-time. Don't leave them around indefinitely (write amplification).
- **ZFS/Btrfs snapshots** — cheap, instantaneous. `zfs send | zfs recv` for off-site replication.
- **Filesystem-level vs application-level consistency** — for databases, quiesce or use the DB's backup tool. A filesystem snapshot of a running Postgres is a crash-consistent snapshot, not a clean one.

## Security Hardening Checklist

- Mount `/tmp`, `/var/tmp`, `/home`, `/dev/shm` with `nodev,nosuid,noexec` where possible.
- Audit SUID/SGID binaries: `find / -xdev -perm -4000 -o -perm -2000`.
- Audit world-writable files: `find / -xdev -perm -0002 -type f`.
- Use capabilities instead of SUID where possible.
- SELinux / AppArmor confinement for services.
- LUKS encryption for data at rest.
- Audit framework (`auditd`) for sensitive-file watches.
