---
title: 'OSI'
date: 2025-12-26T20:26:23+07:00
draft: true
flashcards:
  - q: "What is the primary role of Layer 7 (Application) in the OSI model?"
    a: "Providing network services directly to users and applications, including protocols like HTTP, DNS, and SSH."
  - q: "Which OSI layer is responsible for data encryption and formatting, such as SSL/TLS?"
    a: "Layer 6 (Presentation)."
  - q: "What are the primary protocols associated with Layer 4 (Transport)?"
    a: "TCP (Transmission Control Protocol) for reliable delivery and UDP (User Datagram Protocol) for fast, connectionless delivery."
  - q: "Which layer handles packet routing and logical addressing (IP)?"
    a: "Layer 3 (Network)."
  - q: "What is the difference between Layer 2 (Data Link) and Layer 3 (Network)?"
    a: "Layer 2 handles local node-to-node transfer (Ethernet, MAC addresses), while Layer 3 handles end-to-end routing across different networks (IP)."
  - q: "At which layer do cables, connectors, and electrical signals reside?"
    a: "Layer 1 (Physical)."
  - q: "Which layer manages connection sessions between applications, including RPC?"
    a: "Layer 5 (Session)."
quiz:
  title: "OSI Model Fundamentals Quiz"
  questions:
    - q: "Which layer is responsible for ensuring that data is formatted in a way that the receiving application can understand (e.g., encryption, compression)?"
      options:
        - "Application (Layer 7)"
        - "Presentation (Layer 6)"
        - "Session (Layer 5)"
        - "Transport (Layer 4)"
      correct: 1
    - q: "If you are troubleshooting a 'Ping' (ICMP) failure, which OSI layer are you primarily investigating?"
      options:
        - "Layer 2"
        - "Layer 3"
        - "Layer 4"
        - "Layer 7"
      correct: 1
    - q: "Which protocol provides 'reliable' end-to-end delivery at the Transport layer?"
      options:
        - "UDP"
        - "IP"
        - "TCP"
        - "HTTP"
      correct: 2
    - q: "MAC addresses are used for addressing at which OSI layer?"
      options:
        - "Layer 1"
        - "Layer 2"
        - "Layer 3"
        - "Layer 4"
      correct: 1
    - q: "A Load Balancer terminating SSL/TLS certificates is performing work at which OSI layer?"
      options:
        - "Layer 4"
        - "Layer 5"
        - "Layer 6"
        - "Layer 7"
      correct: 2
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