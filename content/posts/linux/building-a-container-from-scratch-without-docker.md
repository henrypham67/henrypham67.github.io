---
title: 'Building a container from scratch without Docker'
date: 2026-05-12T09:44:40+07:00
draft: true
tags: ["linux", "containers", "namespaces", "cgroups"]
categories: ["Linux"]
---

Introduction — Open with the observation that docker run is just a handful of syscalls. State the payoff: a working shell in an isolated environment built by hand.

Section 1: What a container actually is
- No container_t kernel object — it's a collection of isolation mechanisms applied to an ordinary process
- Three categories: namespaces (what it can see), cgroups (what it can use), filesystem + capabilities (what it can do)

Section 2: Namespaces
- All 7 namespace types (mnt, pid, net, uts, ipc, user, cgroup)
- unshare --uts, unshare --pid --fork --mount-proc demos
- Network namespaces + veth pairs
- User namespaces and UID mapping

Section 3: Cgroups
- v1 vs v2 (focus on v2, unified hierarchy under /sys/fs/cgroup)
- Creating a cgroup, setting memory.max and cpu.max by writing files
- Triggering the OOM killer to verify limits work

Section 4: Filesystem isolation
- Getting a rootfs (Alpine tarball via docker export)
- chroot — what it does, and the classic escape vulnerability
- pivot_root — why it's escape-resistant; full step-by-step example

Section 5: Capabilities and seccomp
- Dropping capabilities with capsh; reading Cap* bitmasks from /proc/self/status
- Seccomp BPF for syscall filtering (conceptual + Docker's default profile)

Section 6: The capstone script (the payoff)
- A ~50-line annotated shell script that assembles everything: namespaces →
cgroup → pivot_root → drop caps → exec shell
- Validation checklist: hostname, ps aux, ip addr, /proc/1/cgroup
- Cleanup commands

Section 7: Bridging back to runc / OCI
- Map each primitive to config.json fields in the OCI Runtime Spec
- Honest list of what you skipped (overlayfs, AppArmor, rootless, device
allowlisting)

Conclusion — Container = process + namespaces + cgroups + isolated rootfs.
Security takeaway. Next steps: trace docker run with strace -f, try rootless,
read runc source.

---
Cross-links

- Link Section 2.3 (net namespaces) → your existing pod-network-namespace.md post
- Link Section 5.2 (seccomp/BPF) → your existing eBPF.md post

Want me to scaffold the file with /new-post and start drafting any section?
