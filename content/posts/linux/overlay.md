---
title: 'Overlay filesystem'
date: 2026-05-16T10:54:12+07:00
draft: true
tags: [linux, containers, kernel, storage]
categories: [linux]
quiz:
  title: "Overlay Filesystem Basics Quiz"
  questions:
    - q: "Which directories MUST be specified to mount an overlay filesystem?"
      options:
        - "lowerdir and upperdir only"
        - "lowerdir, upperdir, and workdir"
        - "upperdir and workdir only"
        - "lowerdir and mergeddir only"
      correct: 1
    - q: "What is the role of the upper layer in an overlay mount when it is first created?"
      options:
        - "It contains a full copy of the lower layer's files"
        - "It is empty and only receives files when they are modified"
        - "It is a read-only mirror of the merged view"
        - "It holds whiteout files for every file in the lower layer"
      correct: 1
    - q: "What happens when a process writes to a file that exists only in the lower layer?"
      options:
        - "The write fails because the lower layer is read-only"
        - "The file is modified in place in the lower layer"
        - "The file is copied to the upper layer first, then modified there (copy-up)"
        - "The write is buffered in the workdir indefinitely"
      correct: 2
    - q: "How does overlayfs represent the deletion of a file that exists in the lower layer?"
      options:
        - "It removes the file from the lower layer directly"
        - "It creates a whiteout entry (a character device with major/minor 0/0) in the upper layer"
        - "It marks the file with a special extended attribute in the lower layer"
        - "It moves the file into the workdir as a tombstone"
      correct: 1
    - q: "Why does overlayfs require a separate workdir on the same filesystem as the upper layer?"
      options:
        - "To cache reads from the lower layer for performance"
        - "To store backup copies of files before modification"
        - "To provide scratch space for atomic operations like copy-up and whiteouts"
        - "To hold the merged view that users see"
      correct: 2
    - q: "If a file exists in both the lower and upper layer, which version does a reader see in the merged view?"
      options:
        - "The lower layer version (it has priority)"
        - "The upper layer version (it shadows the lower)"
        - "Both versions are concatenated"
        - "Reads fail with EEXIST until the conflict is resolved"
      correct: 1
    - q: "Can a single lower layer be shared across multiple overlay mounts simultaneously?"
      options:
        - "No, each overlay mount requires an exclusive lower layer"
        - "Yes, because the lower layer is read-only"
        - "Only if the upper layers are also identical"
        - "Only with the shared=1 mount option"
      correct: 1
---
