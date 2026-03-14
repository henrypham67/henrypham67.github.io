---
title: 'Learning'
date: 2025-12-26T09:16:32+07:00
draft: true
---

| Function    | Concepts (Higher Order)         | Tools (Lower Order)       |
| :---------- | :------------------------------ | :------------------------ |
| Consistency | Environment Parity, Isolation   | Docker, Podman            |
| Automation  | CI/CD Pipelines, Feedback Loops | GitHub Actions, GitLab CI |
| Stability   | Observability, Health Checks    | Prometheus, Grafana       |

## Phase 1: Priming & Landscape Mapping

Before you dive into a tutorial or documentation.

[ ] Define the "Pain Point": Ask yourself, "What problem does this topic solve that wasn't solved before?" (e.g., Why do I need Terraform if I already have Bash scripts?).

[ ] Pre-Map Connections: Look at the table of contents or documentation headers. Draw a quick sketch of how these sub-topics might relate to what you already know (e.g., How does 'State' in Terraform relate to 'Variables' in Python?).

[ ] Set a "Process Goal": Instead of saying "I will finish this video," say "I will be able to explain the relationship between X and Y by the end of this session."

## Phase 2: Deep Encoding (The Learning Block)

While you are consuming the information.

[ ] Identify the "Core Logic": Don't write down every command. Write down the rules the system follows.

Example: "In Kubernetes, the Control Plane always tries to match the 'Actual State' to the 'Desired State'."

[ ] Create a Relational Diagram: Don't use linear notes. Use a mind map or a flow chart to show how data moves through the system.

[ ] Perform "Inquiry Interleaving": If the tutorial says "Type this command," stop and ask, "What would happen if I changed this flag? Would the whole system crash or just one part?"

## Phase 3: The "Stress Test" (Active Retrieval)

Immediately after the study session.

[ ] The Blank Sheet Summary: Close all tabs. On a blank piece of paper (or digital canvas), recreate the architecture of the topic from memory. If you hit a "gap" where you can't remember how Part A talks to Part B, that is your learning priority for the next session.

[ ] Explain the "Why" (The Feynman Audit): Record a 2-minute voice note or type a summary explaining the topic to a "Junior Dev." If you use jargon (e.g., "It's for orchestration"), you haven't mastered it. Use "First Principles" (e.g., "It's a robot that restarts your apps if they die").

[ ] The "Broken Lab" Exercise: Go to your terminal and try to implement the concept. Once it works, purposefully break it. Change a configuration file until it fails, then use your mental model to deduce why it failed.