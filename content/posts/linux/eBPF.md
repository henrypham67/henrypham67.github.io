---
title: 'eBPF - extended Berkeley Packet Filter'
date: 2026-03-01T09:11:06+07:00
draft: true
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

<!-- anki
Q: What is eBPF?
A: A platform-agnostic program injected into kernel space that attaches to hooks (e.g., syscalls, network packets, tracepoints) and shares data through maps
tags: linux::ebpf

Q: What is the role of the eBPF Verifier?
A: Ensures programs are safe — no crashes or infinite loops — before they are loaded into the kernel
tags: linux::ebpf::components

Q: What does the eBPF JIT Compiler do?
A: Translates eBPF bytecode into native machine code for the host CPU
tags: linux::ebpf::components

Q: What is an eBPF Map?
A: A key-value store for sharing data between user space and kernel space
tags: linux::ebpf::components

Q: What is an eBPF Helper?
A: A kernel-provided function that eBPF programs can call (e.g., to read maps, get timestamps, send signals)
tags: linux::ebpf::components

Q: What is XDP in the context of eBPF?
A: eXpress Data Path — an attachment point that processes network packets before they reach the kernel networking stack, enabling very high performance filtering/forwarding
tags: linux::ebpf::hooks

Q: What is the difference between kprobes and tracepoints in eBPF?
A: kprobes are dynamic — they attach to arbitrary kernel functions at runtime. Tracepoints are static hooks defined at compile time in the kernel source, making them more stable across kernel versions.
tags: linux::ebpf::hooks

Q: How does eBPF enable zero-trust security?
A: By attaching to kernel hooks to inspect every syscall and network packet in real time and enforce policies without modifying application code
tags: linux::ebpf::usecases

C: eBPF programs run in {{c1::kernel}} space and share data with user space through a {{c2::map}}
C: The eBPF {{c1::Verifier}} checks that a program has no crashes or infinite loops before it is loaded
C: The eBPF {{c1::JIT Compiler}} translates bytecode into {{c2::native machine code}}
C: {{c1::kprobes}} attach to {{c2::kernel functions}} dynamically at runtime
C: {{c1::uprobes}} attach to {{c2::user-space}} functions
C: {{c1::Tracepoints}} are {{c2::static}} hooks defined in the kernel source
C: {{c1::XDP}} (eXpress Data Path) processes network packets {{c2::before}} the kernel networking stack
C: The four main eBPF hook types are {{c1::kprobes}}, {{c2::uprobes}}, {{c3::tracepoints}}, and {{c4::XDP}}
C: The five main eBPF components are {{c1::Verifier}}, {{c2::JIT Compiler}}, {{c3::Map}}, {{c4::Helper}}, and {{c5::Hooks}}
-->

