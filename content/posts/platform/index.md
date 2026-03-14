---
title: 'Platform'
date: 2025-11-24T12:07:24+07:00
draft: true
---

## Key aspects to consider when operating a Platform's workload

### Observability

- Telemetries:

  - Metrics (Prometheus - CPU, Mem, IO throughput, ...)
  - Logs (Loki)
  - Traces (Opentelemetry - Span)

- Alerts
- Dashboards

### Reliability & Availability

- Replication
- Multi-AZ/Zones

### Scalability

- Vertical scaling:

  - scale up (Server with higher CPU, RAM)
  - scale down

- Horizontal scaling:

  - scale in (Add more instance)
  - scale out

### Security

#### Confidentiality

- identity-based security
  - AuthN
  - AuthZ
- Role-Based Access Control
- Attribute-Based Access Control

#### Integrity

- data encryption
- secret management
- auditing

#### Availability
<!-- similar to ###Availability? -->

### Optimization

- Cost
- Performance

### Deployment

- Install
- Update
- CI/CD
- VCS
- Container & Orchestration

### Disaster Recovery

- Backup
- Restore
- consideration: RTO & RPO
