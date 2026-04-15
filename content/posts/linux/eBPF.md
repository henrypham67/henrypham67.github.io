---
title: 'eBPF - extended Berkeley Packet Filter'
date: 2026-03-01T09:11:06+07:00
draft: true
flashcards:
  - q: "What is eBPF?"
    a: "A platform-agnostic program injected into kernel space that attaches to hooks (e.g., syscalls, network packets, tracepoints) and shares data through maps."
  - q: "What is the role of the eBPF Verifier?"
    a: "It ensures programs are safe—no crashes or infinite loops—before they are loaded into the kernel."
  - q: "What does the eBPF JIT Compiler do?"
    a: "It translates eBPF bytecode into native machine code for the host CPU to ensure high performance."
  - q: "What is an eBPF Map?"
    a: "A key-value store used for sharing data between user space and kernel space, or between different eBPF programs."
  - q: "What is an eBPF Helper?"
    a: "A kernel-provided function that eBPF programs can call to perform tasks like reading maps, getting timestamps, or sending signals."
  - q: "What is XDP in the context of eBPF?"
    a: "eXpress Data Path—an attachment point that processes network packets before they reach the kernel networking stack for high-performance filtering."
  - q: "What is the difference between kprobes and tracepoints?"
    a: "kprobes are dynamic and attach to arbitrary kernel functions at runtime. Tracepoints are static hooks defined at compile time, making them more stable across kernel versions."
  - q: "How does eBPF enable zero-trust security?"
    a: "By attaching to kernel hooks to inspect every syscall and network packet in real time and enforce policies without modifying application code."
quiz:
  title: "eBPF Fundamentals Quiz"
  questions:
    - q: "Which component ensures an eBPF program won't crash the kernel before it is allowed to run?"
      options:
        - "JIT Compiler"
        - "LLVM Backend"
        - "Verifier"
        - "BPF Loader"
      correct: 2
    - q: "What is the primary purpose of an eBPF Map?"
      options:
        - "To store the program's bytecode"
        - "To provide a lookup table for kernel symbols"
        - "To share data between kernel and user space"
        - "To map virtual memory to physical pages"
      correct: 2
    - q: "Which hook would you use if you wanted to drop a DDoS attack's packets as early as possible?"
      options:
        - "kprobes"
        - "uprobes"
        - "tracepoints"
        - "XDP"
      correct: 3
    - q: "Why are tracepoints considered more 'stable' than kprobes?"
      options:
        - "They are written in C++ instead of C"
        - "They are static hooks defined in the kernel source code"
        - "They have higher priority in the scheduler"
        - "They do not require the JIT compiler"
      correct: 1
    - q: "Where does an eBPF program physically execute?"
      options:
        - "In a user-space daemon"
        - "In a dedicated micro-controller on the NIC"
        - "Inside the kernel space"
        - "In a sandboxed WASM runtime"
      correct: 2
---

## Definition & How it works

A platform-agnostic program which injected to kernel space. It attaches to hooks (e.g., system calls, network packets, tracepoints) and shares data through a map

## Components

- Verifier: ensure programs are safe (no crashes/loops)
- JIT Compiler: translate bytecode to machine code
- Map: store shared data between user & kernel spaces
- Helper: Kernel functions that eBPF can call
- Hooks/Attachment Points: kprobes (kernel functions), uprobes (user-space), tracepoints (static), XDP (early network packet processing).

## Use cases

- Monitoring container lifecycle
- Debugging performance bottlenecks
- Implementing zero-trust security
- Optimizing CI/CD pipelines.
