---
title: 'Probe'
date: 2026-02-27T10:46:54+07:00
draft: true
---

**Kubernetes Probes – Quick Distinction + Mnemonic**

| Probe       | What it checks                  | If it **fails**                  | When it runs                          | Key point                     |
|-------------|---------------------------------|----------------------------------|---------------------------------------|-------------------------------|
| **Startup** | “Has the app finished starting?” | Pod is **killed & restarted**   | Only at the very beginning            | Disables liveness + readiness until it passes |
| **Liveness** | “Is the container still alive?” | Pod is **restarted**            | After startup passes (continuously)   | Restarts dead containers      |
| **Readiness** | “Can the container serve traffic?” | Pod is **removed from Service** | After startup passes (continuously)   | Stops receiving requests only |

### Super Simple Mnemonic (LRS)
- **S**tartup = **S**tarting up → slow apps (big JVM, heavy init, etc.)
- **L**iveness = **L**ife → if dead → kill & restart
- **R**eadiness = **R**eady for traffic → just stop sending requests (no restart)

**Rule of thumb**:
- Use **Startup** first if your app takes >30s to boot.
- Always pair **Liveness** + **Readiness** for normal health.
- Never use readiness as liveness (or vice-versa) — they do completely different things.

That’s it — 3 lines to remember forever.


