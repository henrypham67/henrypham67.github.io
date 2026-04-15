---
title: 'StorageClass'
date: 2026-04-04T15:30:06+07:00
draft: true
tags: ["kubernetes", "storage", "persistent-volumes"]
categories: ["Kubernetes"]
---

## Parameters

- Optional
- Immutable
- Common general-purpose parameters
  - `csi.storage.k8s.io/fstype`: Filesystem type (e.g., ext4, xfs)
  - `encrypted`: `true` / `false` for at-rest encryption
- For AWS EBS
  - `type`: gp3 (general purpose, balanced), io2 (high IOPS SSD), st1 (throughput-optimized HDD), etc.
  - `iops`: Absolute IOPS value (for io2/io1).
  - `throughput`: MiB/s (for gp3).
  - `fsType`: ext4 or xfs.
