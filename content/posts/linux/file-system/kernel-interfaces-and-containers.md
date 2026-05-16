---
title: 'Kernel interfaces and containers'
date: 2026-05-12T09:50:00+07:00
draft: true
tags: [linux, proc, sys, cgroups, containers, nfs]
categories: [Linux]
flashcards:
  - q: "Why should you prefer `hard` over `soft` NFS mounts for data integrity?"
    a: "Soft mounts return I/O errors after a timeout, which can cause silent data loss or corruption in apps that don't check every write. Hard mounts block until the server responds, preserving correctness."
  - q: "What's inside `/proc/<pid>/fd/`?"
    a: "Symlinks to every file, socket, and pipe the process currently has open. Inspect them with `ls -l` to see what a process is touching — including deleted files (`(deleted)` suffix)."
  - q: "What is `/sys/fs/cgroup/` used for in modern Linux?"
    a: "It exposes cgroups v2 controls: memory, CPU, and I/O limits applied to processes and containers. systemd and Kubernetes write to it to enforce resource limits."
  - q: "What does `pivot_root` do in a container's lifecycle?"
    a: "It swaps the container process's root filesystem to the prepared overlay (image + writable layer), then unmounts the old root. After pivot_root, the container can't see the host's filesystem tree."
  - q: "Why are object storage mounts (s3fs, goofys) a bad choice for databases?"
    a: "They fake POSIX semantics on top of HTTP. No atomic rename across keys, no real `fsync` durability, high latency. Databases assume strong filesystem guarantees that S3 can't provide."
  - q: "What does the `(deleted)` suffix in `lsof` output mean?"
    a: "The file was unlinked from its directory entry, but a process still has it open. Its blocks won't be freed until that process closes the fd or exits — classic 'df full, du empty' cause."
  - q: "Which `/proc` file shows the kernel's view of currently mounted filesystems?"
    a: "`/proc/mounts` (or `/proc/self/mountinfo` for richer detail including propagation flags and namespace info)."

quiz:
  title: "Kernel Interfaces and Containers Quiz"
  questions:
    - q: "An NFS server briefly disconnects. Your `hard` mount causes the application to hang; an SRE suggests switching to `soft`. What's the risk?"
      options:
        - "Soft mounts double network traffic"
        - "Soft mounts can return I/O errors mid-write, causing silent data corruption"
        - "Soft mounts disable caching"
        - "Soft mounts require kerberos"
      correct: 1
    - q: "Where would you set a memory limit for a container using cgroups v2?"
      options:
        - "`/proc/sys/vm/swappiness`"
        - "`/sys/fs/cgroup/<group>/memory.max`"
        - "`/etc/security/limits.conf`"
        - "`/proc/<pid>/limits`"
      correct: 1
    - q: "Why is running a Postgres database on an s3fs FUSE mount a bad idea?"
      options:
        - "S3 doesn't support files larger than 5 GB"
        - "FUSE mounts can't be exported over NFS"
        - "Object storage mounts fake POSIX semantics; no real fsync, no atomic rename"
        - "Postgres requires ext4 specifically"
      correct: 2
---

# Kernel Interfaces and Containers

## /proc and /sys — The Kernel's API

- `/proc/<pid>/` — per-process. `cmdline`, `status`, `fd/`, `maps`, `limits`, `cgroup`, `ns/`.
- `/proc/mounts`, `/proc/meminfo`, `/proc/cpuinfo`, `/proc/loadavg`, `/proc/net/`.
- `/proc/sys/` — tunables, mostly accessed via `sysctl`. `vm.swappiness`, `fs.file-max`, `net.ipv4.*`.
- `/sys/fs/cgroup/` — cgroups v2 controls. Memory, CPU, IO limits for containers/services.
- `/sys/block/<dev>/queue/scheduler` — I/O scheduler (`mq-deadline`, `none`, `bfq`).

## Containers and Filesystems

- Docker/containerd images = **stack of read-only layers + writable top layer**, unioned by **overlayfs**.
- Container root filesystem is ephemeral. **Volumes** (bind mounts or named volumes) for persistence.
- Each container has its own **mount namespace** + **pivot_root** + (usually) read-only overlay layers.
- `/var/lib/docker` / `/var/lib/containerd` is a notorious disk hog. Use `docker system prune`, image GC policies in Kubernetes (`kubelet --image-gc-high-threshold`).
- Watch for **inode exhaustion** on container hosts (many tiny layer files).

## Network Filesystems

- **NFS** — `hard,intr,nfsvers=4.2`. Soft mounts → silent data loss on timeout. Hard mounts → hangs. Pick hard for data integrity.
- **Stale file handles** — server-side change broke client cache. Remount.
- **SMB/CIFS** — Windows interop.
- **Object storage mounts** (s3fs, rclone, goofys) — POSIX semantics are faked. No `fsync` guarantees, no atomic rename across keys. Don't run databases on these.
