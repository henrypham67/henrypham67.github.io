---
title: 'HTTP'
date: 2026-02-20T12:06:26+07:00
draft: true
---

Encryption:

- optional, SSL
- optional, TLS
- encourage, TLS
- enforce, TLS 1.3

Header Compression

- no 
- gzip
-
-

Connection:

- single request per connection
- multiple requests (persistent = `Connection: keep-alive` header) per connection
- multiplex
- multiplex

Protocol:

- Text, TCP
- Text, TCP
- Binary, TCP
- Binary, UDP - QUIC

Single request -> Multi-request - MOL -> Multiplexing -> UDP + Multiplexing
