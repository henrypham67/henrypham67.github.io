---
title: 'File system'
date: 2026-05-12T09:00:00+07:00
draft: true
tags: [linux, storage, kernel, syscalls]
categories: [Linux]
---

# Linux File System — The DevOps/SRE Survival Guide

A working knowledge of the Linux filesystem is a baseline skill for anyone running production systems. This section breaks the topic into focused pages.

## Sub-pages

- [Filesystem types](./filesystem-types/) — ext4, XFS, Btrfs, ZFS, tmpfs, overlayfs, and when to pick each.
- [Inodes and permissions](./inodes-and-permissions/) — the inode model, hard vs symlinks, ugo/rwx, SUID/SGID/sticky, ACLs, xattrs, capabilities.
- [Mounting and block devices](./mounting-and-block-devices/) — `/etc/fstab`, mount options, bind mounts, partitions, LVM, RAID, LUKS.
- [Durability and troubleshooting](./durability-and-troubleshooting/) — journaling, page cache, `fsync`, the daily disk-full investigation, logs and rotation.
- [Kernel interfaces and containers](./kernel-interfaces-and-containers/) — `/proc`, `/sys`, container filesystems, network filesystems.
- [Performance, backup, security](./performance-backup-security/) — observability tools, snapshots, hardening checklist.

---

## 1. The Big Picture: Everything is a File

In Linux, **files, directories, devices, sockets, pipes, and even processes** are represented as file-like objects. This unifies the API: `open()`, `read()`, `write()`, `close()` work across all of them. Understanding this unlocks `/proc`, `/sys`, `/dev`, and why tools like `lsof` can show network connections.

---

## 2. The Filesystem Hierarchy Standard (FHS)

| Path | Purpose | SRE Relevance |
|------|---------|---------------|
| `/` | Root | Never fill this up |
| `/bin`, `/sbin`, `/usr/bin`, `/usr/sbin` | System binaries | `/sbin` = root-only tools |
| `/etc` | System config | Back this up; configs live here |
| `/var` | Variable data: logs, caches, spools, databases | **Most common disk-full culprit** (`/var/log`, `/var/lib/docker`) |
| `/tmp` | Temp files, world-writable, often `tmpfs` (RAM-backed) | Cleared on reboot; watch sticky bit |
| `/home` | User home dirs | Often a separate partition |
| `/opt` | Optional/third-party software | |
| `/proc` | Virtual FS — kernel + process info | `/proc/<pid>/`, `/proc/meminfo`, `/proc/mounts` |
| `/sys` | Virtual FS — devices, kernel objects, cgroups (v1) | Tune kernel knobs here |
| `/dev` | Device nodes (block + character) | `/dev/sda`, `/dev/null`, `/dev/urandom` |
| `/run` | Runtime state (PID files, sockets); `tmpfs` | Replaced `/var/run` |
| `/boot` | Kernel + initramfs + bootloader | Don't let this fill — apt/yum upgrades break |
| `/mnt`, `/media` | Mount points | |
| `/lost+found` | fsck recovery (ext only) | If it has contents, something went wrong |

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Disk usage by mount | `df -hT` |
| Inode usage | `df -i` |
| Tree size | `du -xhd1 /path \| sort -h` or `ncdu` |
| Which process owns a file/port | `lsof <path>` / `fuser` |
| Deleted-but-open files | `lsof +L1` |
| Find large files | `find / -xdev -type f -size +500M` |
| Mount info | `findmnt`, `lsblk -f` |
| UUID / FS type | `blkid` |
| Tune ext4 | `tune2fs` |
| Check / repair | `fsck` (unmounted!) |
| Resize FS | `resize2fs` (ext), `xfs_growfs` (XFS) |
| Trim SSD | `fstrim -av` |
| Open files limit | `ulimit -n`, `/etc/security/limits.conf` |

---

## What to Internalize First

If you only memorize five things:

1. **Inodes can exhaust before bytes do.** Always alert on both.
2. **Deleted-but-open files don't free space.** Restart the holder.
3. **`fsync` is the only durability primitive that matters.** Verify it on cloud disks.
4. **Mount options change everything** — `noatime`, `noexec`, `discard`, `ro`.
5. **`/var/lib/{docker,containerd}` and `/var/log` will fill your disk before anything else does.**
