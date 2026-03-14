---
title: 'OSI'
date: 2025-12-26T20:26:23+07:00
draft: true
---

| Layer | Name         | Role (Brief)                | Key Protocols/Examples (80/20 Focus) | Memorization Tip (Protocol-Focused) |
| :---- | :----------- | :-------------------------- | :----------------------------------- | :---------------------------------- |
| 7     | Application  | User/app network services.  | "HTTP/HTTPS (web traffic)            | DNS (domain lookup)                 |, SSH (remote access).","""All"" = All apps start here; ""all web ops use HTTPS"" or ""all scripts resolve DNS""—think curl commands in pipelines."
| 6     | Presentation | Data formatting/encryption. | "SSL/TLS (secure data)               | MIME (attachments)."                |,"""People"" = People protect data; ""people encrypt with TLS""—recall cert configs in load balancers."
| 5     | Session      | Connection management.      | "RPC (remote procedures)             | SOCKS (proxies)."                   |,"""Seem"" = Seem connected; ""seem to call RPC in services""—link to API sessions in microservices."
| 4     | Transport    | End-to-end delivery.        | "TCP (reliable)                      | UDP (fast)                          |, ports (e.g., 80/443).","""To"" = To transport; ""to reliably use TCP""—associate with Docker port mappings."
| 3     | Network      | Packet routing/addressing.  | "IP (addressing)                     | ICMP (ping)."                       |,"""Need"" = Need routes; ""need IP for clouds""—practice pinging in VPCs."
| 2     | Data Link    | Local node transfer.        | "Ethernet (framing)                  | MAC addresses."                     |,"""Data"" = Data locally; ""data via Ethernet switches""—visualize VLANs in infra."
| 1     | Physical     | Bit transmission.           | "Cables (RJ-45/fiber)                | Wi-Fi signals."                     |,"""Processing"" = Processing hardware; ""processing cables in racks""—recall physical server checks."

<!-- anki
Q: What is Layer 7 (Application) and its key protocols?
A: Role: User/app network services. Key Protocols/Examples: HTTP/HTTPS (web traffic), DNS (domain lookup), SSH (remote access). Tip: Think curl in CI/CD for HTTPS or DNS in Terraform.

Q: What is Layer 6 (Presentation) and its key protocols?
A: Role: Data formatting/encryption. Key Protocols/Examples: SSL/TLS (secure data), MIME (attachments). Tip: Recall TLS certs in AWS ALB or MIME in email alerts.

Q: What is Layer 5 (Session) and its key protocols?
A: Role: Connection management. Key Protocols/Examples: RPC (remote procedures), SOCKS (proxies). Tip: Link to RPC in gRPC services or SOCKS for proxy setups in VPNs.

Q: What is Layer 4 (Transport) and its key protocols?
A: Role: End-to-end delivery. Key Protocols/Examples: TCP (reliable), UDP (fast), ports (e.g., 80/443). Tip: Associate with kubectl port-forward (TCP) or UDP for streaming in apps.

Q: What is Layer 3 (Network) and its key protocols?
A: Role: Packet routing/addressing. Key Protocols/Examples: IP (addressing), ICMP (ping). Tip: Practice with ip addr show or ping in cloud VPC troubleshooting.

Q: What is Layer 2 (Data Link) and its key protocols?
A: Role: Local node transfer. Key Protocols/Examples: Ethernet (framing), MAC addresses. Tip: Visualize Ethernet in switch configs or MAC in container networking.

Q: What is Layer 1 (Physical) and its key protocols?
A: Role: Bit transmission. Key Protocols/Examples: Cables (RJ-45/fiber), Wi-Fi signals. Tip: Recall checking RJ-45 ports in server racks or Wi-Fi in edge deployments.

C: Layer {{c1::7}} - {{c2::Application}} handles user/app services like {{c3::HTTP/HTTPS}}, {{c4::DNS}}, and {{c5::SSH}}.
C: Layer {{c1::6}} - {{c2::Presentation}} manages data formatting and encryption using {{c3::SSL/TLS}} and {{c4::MIME}}.
C: Layer {{c1::5}} - {{c2::Session}} manages connections with {{c3::RPC}} and {{c4::SOCKS}}.
C: Layer {{c1::4}} - {{c2::Transport}} provides end-to-end delivery with {{c3::TCP}} (reliable) and {{c4::UDP}} (fast).
C: Layer {{c1::3}} - {{c2::Network}} handles routing with {{c3::IP}} and troubleshooting with {{c4::ICMP/ping}}.
C: Layer {{c1::2}} - {{c2::Data Link}} manages local transfers with {{c3::Ethernet}} framing and {{c4::MAC}} addresses.
C: Layer {{c1::1}} - {{c2::Physical}} transmits bits over {{c3::cables}} (RJ-45/fiber) and {{c4::Wi-Fi}} signals.
tags: osi, networking
-->