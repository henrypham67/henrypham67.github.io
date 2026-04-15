---
title: 'SystemD'
date: 2024-10-26T14:24:37+07:00
draft: true
tags: ["linux", "command", "systemd"]
flashcards:
  - q: "What command enables a systemd service to start at boot?"
    a: "`systemctl enable <service>.service`"
  - q: "What command prevents a service from being started (even manually)?"
    a: "`systemctl mask <service>.service` — this creates a symlink to /dev/null"
  - q: "What are the three main sections of a systemd unit file?"
    a: "[Unit], [Service], [Install]"
  - q: "Where are system-level systemd unit files stored?"
    a: "`/lib/systemd/system/` (packaged) and `/etc/systemd/system/` (admin overrides)"
  - q: "What command reloads all unit files after you edit one?"
    a: "`systemctl daemon-reload`"
  - q: "What is the difference between `systemctl restart` and `systemctl reload`?"
    a: "`restart` stops and starts the service (new PID). `reload` sends SIGHUP to re-read config without stopping (same PID, if supported)."
  - q: "How do you list all systemd services (including inactive)?"
    a: "`systemctl list-units --type service --all`"
  - q: "What signal does `systemctl reload` typically send to a process?"
    a: "It usually sends `SIGHUP` to tell the process to re-read its configuration files."
quiz:
  title: "SystemD Mastery Quiz"
  questions:
    - q: "Which command would you use to prevent a service from being started even by another service?"
      options:
        - "systemctl stop"
        - "systemctl disable"
        - "systemctl mask"
        - "systemctl isolate"
      correct: 2
    - q: "You've just edited a .service file in /etc/systemd/system/. What must you do before systemd recognizes the changes?"
      options:
        - "systemctl restart <service>"
        - "systemctl daemon-reload"
        - "systemctl reload-env"
        - "reboot the system"
      correct: 1
    - q: "Which section of a systemd unit file is used to define dependencies and metadata like 'Description'?"
      options:
        - "[Service]"
        - "[Install]"
        - "[Unit]"
        - "[Metadata]"
      correct: 2
    - q: "What is the key difference between 'enable' and 'start' in systemctl?"
      options:
        - "Enable starts it now; Start makes it persistent"
        - "Enable makes it persistent across boots; Start starts it now"
        - "They are aliases for the same operation"
        - "Enable is for services; Start is for timers"
      correct: 1
    - q: "If you want to see all services, including those that failed or are inactive, which flag do you add to 'list-units'?"
      options:
        - "--verbose"
        - "--failed"
        - "--all"
        - "--status"
      correct: 2
---

```bash
systemctl enable ssh.service
```

```bash
systemctl disable ssh.service
```

```bash
systemctl start ssh.service
```

```bash
systemctl stop ssh.service
```

```bash
systemctl reload ssh.service
```

```bash
systemctl restart ssh.service
```

prevent service from being activated?

```bash
systemctl mask ssh.service
```

```bash
systemctl unmask ssh.service
```

```bash
systemctl list-units --type service --all
```

how to mention a service without its postfix `.service`?

what are other types beside `service` ?

How to create a systemd service?

man systemd.service

Options:

- Restart
- RestartSec

Sections:

- Unit
- Service
- Install

/lib/systemd/system/ssh.service

learn more about permission best practices
