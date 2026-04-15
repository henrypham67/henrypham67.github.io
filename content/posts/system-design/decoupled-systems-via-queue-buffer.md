---
title: 'Decoupled systems via queue/buffer'
date: 2026-03-28T18:27:34+07:00
draft: true
tags: ["system-design", "scalability", "microservices", "messaging"]
categories: ["System Design"]
---

- message depends on each other (DAG)
- handling duplication (solve: lease (lock + TTL), heartbeat)
  - at most once
  - at least once
  - exactly once
- 