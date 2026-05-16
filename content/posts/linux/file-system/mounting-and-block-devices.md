---
title: 'Mounting and block devices'
date: 2026-05-12T09:30:00+07:00
draft: true
tags: [linux, mount, fstab, lvm, raid, luks]
categories: [Linux]
flashcards:
  - q: "What does the `noatime` mount option do, and why is it commonly used?"
    a: "It disables updating the access-time metadata on every read, eliminating writes triggered by reads. Improves performance significantly, especially for databases and busy filesystems."
  - q: "Why use `UUID=` instead of `/dev/sda1` in `/etc/fstab`?"
    a: "Kernel device names like `/dev/sdX` can change between boots when disks are added, removed, or reordered. UUIDs and labels are stable identifiers tied to the filesystem itself."
  - q: "What is a bind mount, and why is it important for containers?"
    a: "`mount --bind src dst` makes a directory accessible at a second location, sharing the same inodes. Containers use bind mounts to inject host paths (volumes, configs, sockets) into their mount namespace."
  - q: "What are the three commands to set up LVM, in order?"
    a: "`pvcreate` (mark a block device as a Physical Volume), `vgcreate` (group PVs into a Volume Group), `lvcreate` (carve Logical Volumes out of the VG)."
  - q: "Why is RAID 5 a poor choice for write-heavy workloads like database journals?"
    a: "Every write requires reading old data + old parity, computing new parity, then writing new data + new parity (4 I/Os per write). This 'write hole' kills small-write performance. Use RAID 10 instead."
  - q: "What mount options should you set on `/tmp` for security hardening?"
    a: "`nodev,nosuid,noexec` — prevents device files, blocks SUID escalation, and stops attackers from running binaries dropped into a world-writable directory."
  - q: "What does `fstrim` do, and why does it matter on SSDs?"
    a: "It tells the SSD which blocks are no longer in use so the controller can reclaim them for wear leveling. Without trim (either periodic `fstrim` or `discard` mount option), SSDs slow down over time as the controller can't tell free blocks from used ones."

quiz:
  title: "Mounting and Block Devices Quiz"
  questions:
    - q: "Which mount option forces a write to the inode on every read, hurting database performance the most?"
      options:
        - "`noatime`"
        - "`relatime`"
        - "`strictatime`"
        - "`nodiratime`"
      correct: 2
    - q: "What is the correct LVM setup order?"
      options:
        - "`lvcreate` → `vgcreate` → `pvcreate`"
        - "`pvcreate` → `vgcreate` → `lvcreate`"
        - "`vgcreate` → `pvcreate` → `lvcreate`"
        - "`mkfs` → `pvcreate` → `lvcreate`"
      correct: 1
    - q: "You're hardening a server. Which mount options should `/tmp` have?"
      options:
        - "`ro,sync`"
        - "`nodev,nosuid,noexec`"
        - "`exec,dev,suid`"
        - "`auto,defaults`"
      correct: 1
    - q: "Why is identifying a filesystem by UUID in `/etc/fstab` preferred over `/dev/sdb1`?"
      options:
        - "UUID is shorter to type"
        - "UUID is a stable identifier; `/dev/sdX` names can shift between boots"
        - "UUID survives `mkfs`; `/dev/sdX` does not"
        - "UUID is required for journaling"
      correct: 1
---

# Mounting and Block Devices

## Mounting

- `/etc/fstab` — persistent mounts. `UUID=`/`LABEL=` is safer than `/dev/sdX` (device names can shift).
- `mount`, `umount`, `findmnt`, `lsblk`, `blkid`.

### Critical mount options

- `noatime` / `relatime` — kill access-time updates for performance.
- `nodev`, `nosuid`, `noexec` — security hardening for `/tmp`, `/home`, `/var`.
- `ro` — read-only.
- `defaults` — `rw,suid,dev,exec,auto,nouser,async`.
- `discard` / periodic `fstrim` for SSDs.

### Bind mounts and namespaces

- **Bind mounts** (`mount --bind`) — mount a directory at another location. Foundation of containers.
- **Namespaces + mount propagation** (`shared`, `private`, `slave`) — how containers see/don't see host mounts.

## Block Devices, Partitions, LVM

- `lsblk`, `fdisk`, `parted`, `gdisk` — partition tools. **GPT** over MBR for anything modern.
- **LVM** (`pvcreate` → `vgcreate` → `lvcreate`) — Physical Volumes → Volume Groups → Logical Volumes. Lets you resize, snapshot, span disks. Snapshot for backups.
- **RAID** — `mdadm` for software RAID. RAID 1 (mirror), 10 (stripe+mirror), 5/6 (parity, slower writes). Don't put a journal on RAID 5.
- **dm-crypt / LUKS** — disk encryption.
- **Multipath** for SAN connections.
