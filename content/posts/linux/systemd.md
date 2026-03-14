---
title: 'SystemD'
date: 2024-10-26T14:24:37+07:00
draft: true
tags: ["linux", "command", "systemd"]
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
systemctl stop ssh.servicehugo 
```

```bash
systemctl reload ssh.service
```

```bash
systemctl restart ssh.service
```

prevent serice from being activated?

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

<!-- anki
Q: What command enables a systemd service to start at boot?
A: `systemctl enable <service>.service`

Q: What command prevents a service from being started (even manually)?
A: `systemctl mask <service>.service` — creates a symlink to /dev/null

Q: What are the three main sections of a systemd unit file?
A: [Unit], [Service], [Install]
tags: concepts

Q: Where are system-level systemd unit files stored?
A: `/lib/systemd/system/` (packaged) and `/etc/systemd/system/` (admin overrides)
tags: paths

Q: What command reloads all unit files after you edit one?
A: `systemctl daemon-reload`

Q: What is the difference between `systemctl restart` and `systemctl reload`?
A: `restart` stops and starts the service (new PID). `reload` sends SIGHUP to re-read config without stopping (same PID, if supported).
tags: concepts

Q: How do you list all systemd services (including inactive)?
A: `systemctl list-units --type service --all`

C: To enable a service to start at boot: `systemctl {{c1::enable}} ssh.service`
C: To prevent a service from being started, even manually: `systemctl {{c1::mask}} ssh.service` — this creates a symlink to {{c2::/dev/null}}
C: To reverse a mask: `systemctl {{c1::unmask}} ssh.service`
C: To re-read config without stopping a service (same PID): `systemctl {{c1::reload}} ssh.service`
C: To stop and start a service (new PID): `systemctl {{c1::restart}} ssh.service`
C: The three main sections of a systemd unit file are {{c1::[Unit]}}, {{c2::[Service]}}, and {{c3::[Install]}}
C: Two common restart-related options in a unit file are {{c1::Restart}} and {{c2::RestartSec}}
C: System-packaged unit files are stored in {{c1::/lib/systemd/system/}}, while admin overrides go in {{c2::/etc/systemd/system/}}
C: After editing a unit file, reload all units with `systemctl {{c1::daemon-reload}}`
C: To list all services including inactive ones: `systemctl list-units --type service {{c1::--all}}`
C: `systemctl reload` sends {{c1::SIGHUP}} to re-read config, while `systemctl restart` gives the service a {{c2::new PID}}
C: To read the manual for service unit files: `man {{c1::systemd.service}}`
-->