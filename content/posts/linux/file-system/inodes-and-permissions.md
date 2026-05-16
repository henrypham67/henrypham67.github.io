---
title: 'Inodes and permissions'
date: 2026-05-12T09:20:00+07:00
draft: true
tags: [linux, inodes, permissions, suid, capabilities, acl]
categories: [Linux]
flashcards:
  - q: "What two conditions must both be true for a file's data blocks to actually be freed?"
    a: "The hard-link count must reach 0 AND no process can still have the file open. Until both happen, the inode and blocks persist."
  - q: "What command shows inode usage, and why does it matter separately from disk usage?"
    a: "`df -i`. A filesystem can exhaust inodes (millions of tiny files) long before running out of bytes, causing 'no space left on device' errors with plenty of free space."
  - q: "What is the difference between a hard link and a symbolic link?"
    a: "A hard link is another directory entry pointing to the same inode (same file, multiple names). A symlink is a separate inode whose contents are a path string pointing to another file."
  - q: "How do Linux capabilities differ from the SUID bit, and why are they preferred?"
    a: "Capabilities split root powers into ~30 fine-grained pieces (e.g., `cap_net_bind_service`), so a binary gets just the privilege it needs instead of full root. They reduce blast radius compared to SUID."
  - q: "What does the SUID bit do, and where is it commonly seen?"
    a: "SUID makes an executable run as the file's owner regardless of who invoked it. Classic examples: `passwd`, `sudo` — they need root to edit `/etc/shadow` or escalate privileges."
  - q: "What does SGID do when set on a directory?"
    a: "New files created inside inherit the directory's group ownership instead of the creator's primary group. Used for shared project directories where everyone in a team should be able to access each other's files."
  - q: "What is the purpose of the sticky bit on `/tmp`?"
    a: "It restricts file deletion to the file's owner (or root), even though the directory is world-writable. Prevents users from deleting each other's temp files."
  - q: "What does umask `0022` mean for new files and directories?"
    a: "It masks off write permission for group and other. New files get mode 644 (rw-r--r--); new directories get 755 (rwxr-xr-x). Lower umask = more open permissions."
  - q: "What command grants a non-root binary the ability to bind to privileged ports?"
    a: "`setcap cap_net_bind_service=+ep /path/to/binary`. Safer than SUID-root because the binary gets only that one capability, not full root."
  - q: "Where do SELinux labels and file capabilities physically live on disk?"
    a: "In extended attributes (xattrs) on the file's inode. Inspect with `getfattr -d` or `getcap`."

quiz:
  title: "Inodes and Permissions Quiz"
  questions:
    - q: "A directory has mode `drwxrwxrwt`. What is the `t` at the end?"
      options:
        - "Trusted-execution flag"
        - "Sticky bit — only file owners can delete their own files"
        - "Temporary filesystem indicator"
        - "Tagged/labeled by SELinux"
      correct: 1
    - q: "You see `-rwsr-xr-x` on a binary. What does the `s` mean?"
      options:
        - "Symlink target permissions"
        - "SGID bit — runs with the file's group"
        - "SUID bit — runs as the file's owner"
        - "Sticky bit — restricts deletion"
      correct: 2
    - q: "Which of these is the safer modern alternative to making a binary SUID-root just so it can bind to port 80?"
      options:
        - "Run it under sudo"
        - "Use `setcap cap_net_bind_service=+ep`"
        - "Set umask to 0000"
        - "Add the binary to `/etc/sudoers`"
      correct: 1
    - q: "A filesystem reports plenty of free space but `mkdir` fails with `No space left on device`. What should you check?"
      options:
        - "`df -i` for inode exhaustion"
        - "`vmstat` for swap pressure"
        - "`dmesg` for SCSI errors"
        - "`mount` options for `ro`"
      correct: 0
---

# Inodes and Permissions

## Inodes — The Hidden Resource

A file = **inode** (metadata: perms, owner, timestamps, block pointers) + **data blocks** + **directory entry** (name → inode mapping).

- You can run out of **inodes before disk space** — common with millions of tiny files (caches, mail spools, session files). `df -i` shows inode usage. Critical metric to alert on.
- `ls -i` shows inode number. Multiple names pointing to the same inode = **hard links** (`ln`). Different inodes = **symlinks** (`ln -s`).
- A file is deleted only when its **link count + open file handles = 0**. This is why `rm` on an open log file doesn't reclaim space until the process closes/restarts (use `lsof | grep deleted`).

## Permissions and Ownership

**Three triplets:** owner / group / others, each with `r w x`.

- Files: `x` = executable. Directories: `x` = traversable, `r` = listable.

### Special bits

- **SUID** (`chmod u+s`) — executable runs as the file's owner. `passwd`, `sudo`. Security-critical; audit these.
- **SGID** on files — runs as group. On directories — new files inherit the directory's group (useful for shared project dirs).
- **Sticky bit** (`chmod +t`) — on a directory, only file owner can delete. `/tmp` uses this.

### Beyond ugo/rwx

- **ACLs** (`getfacl`, `setfacl`) — fine-grained beyond ugo/rwx.
- **Extended attributes** (`getfattr`, `setfattr`) — namespaced metadata. SELinux labels, file capabilities live here.
- **Capabilities** (`getcap`, `setcap`) — split root powers into 30+ pieces. `setcap cap_net_bind_service=+ep` lets a non-root binary bind port 80. Better than SUID.
- **umask** — default-permission mask for new files. Typical: `0022` (files get 644, dirs 755).
