---
title: 'Systemctl'
date: 2024-10-26T14:24:37+07:00
draft: true
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
