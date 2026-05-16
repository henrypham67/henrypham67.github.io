---
title: 'Filesystem types'
date: 2026-05-12T09:10:00+07:00
draft: true
tags: [linux, storage, ext4, xfs, btrfs, zfs]
categories: [Linux]
flashcards:
  - q: "Why can XFS grow but not shrink?"
    a: "XFS encodes an inode's physical location (allocation group + offset) into its inode number. Shrinking would require relocating data off the tail and renumbering every inode, which breaks open file descriptors, NFS handles, and hard links."
  - q: "What command grows an XFS filesystem to fill its underlying block device?"
    a: "`xfs_growfs /mountpoint`. It runs online (filesystem stays mounted) and appends new allocation groups to cover the larger block device."
  - q: "Which filesystem is the foundation of Docker and Podman image layers?"
    a: "overlayfs — a union filesystem that stacks read-only image layers with a writable top layer, presenting a single unified view."
  - q: "What distinguishes Btrfs and ZFS from ext4/XFS in their core design?"
    a: "Btrfs and ZFS are copy-on-write (COW): writes go to new blocks instead of overwriting in place. This makes cheap snapshots, checksums, and send/receive replication first-class operations."
  - q: "Why is tmpfs not a substitute for a regular filesystem?"
    a: "tmpfs lives in RAM (backed by swap if available) and loses all contents on reboot. It's for ephemeral data only — `/tmp`, `/run`, `/dev/shm`."
  - q: "When would you pick XFS over ext4?"
    a: "Large files, parallel I/O at scale, very large volumes. XFS shines on big media, scientific, and log/data-warehouse workloads. Pick ext4 for general-purpose roots and when you might need to shrink."

quiz:
  title: "Filesystem Types Quiz"
  questions:
    - q: "Which filesystem feature is the foundation of Docker's image layer system?"
      options:
        - "Btrfs subvolumes"
        - "LVM thin provisioning"
        - "overlayfs union mounts"
        - "tmpfs"
      correct: 2
    - q: "Which statement about XFS is correct?"
      options:
        - "XFS can be shrunk online with `xfs_shrinkfs`"
        - "XFS can be shrunk offline but not online"
        - "XFS cannot be shrunk in place; you must back up, recreate, and restore"
        - "XFS can only be resized at `mkfs` time"
      correct: 2
    - q: "Which filesystem stores its data in RAM and loses contents on reboot?"
      options:
        - "Btrfs"
        - "tmpfs"
        - "squashfs"
        - "ext4 with `data=writeback`"
      correct: 1
    - q: "For a workload that needs cheap, atomic snapshots and send/recv replication, which filesystem family is the natural fit?"
      options:
        - "ext4 with LVM"
        - "XFS with mdadm RAID"
        - "Btrfs or ZFS"
        - "tmpfs"
      correct: 2
---

# Filesystem Types — Pick the Right One

- **ext4** — Default on most distros. Reliable, journaled, well-understood. Good general-purpose choice.
- **XFS** — Default on RHEL/CentOS. Excellent for large files, parallel I/O, big volumes. Can't shrink.
- **Btrfs** — Copy-on-write, snapshots, subvolumes, checksums. Used by default on Fedora, openSUSE. Beware RAID 5/6.
- **ZFS** — COW, snapshots, send/recv, compression, checksums, integrated volume management. Hungry for RAM. Licensing keeps it out of mainline kernel.
- **tmpfs** — RAM-backed. `/tmp`, `/run`, `/dev/shm`. Lost on reboot.
- **overlayfs** — Union mount. Powers Docker/Podman image layers.
- **squashfs** — Read-only, compressed. Live ISOs, snap packages.
- **NFS, CIFS/SMB** — Network filesystems. Watch for stale handles, soft vs hard mounts.
- **FUSE** — Userspace filesystems (sshfs, s3fs, rclone mount).

## Rules of thumb

- Database volume → XFS or ext4 with `noatime`, tuned mount options.
- General-purpose VM root → ext4.
- Large media / scientific workloads → XFS.
- Snapshots/cheap clones needed → ZFS or Btrfs.

## A note on XFS resize

`xfs_growfs /mountpoint` extends an XFS filesystem to fill its underlying block device. **Growing is online and safe; shrinking is not supported.** XFS encodes inode location into the inode number, so relocating data off the tail of the device would require renumbering every inode — a stop-the-world change incompatible with NFS handles and open file descriptors. Plan capacity assuming the only way down is backup → `mkfs` → restore.
