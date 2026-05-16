---
title: 'Data streaming system'
date: 2026-05-06T10:00:00+07:00
draft: true
tags: ["system-design", "scalability", "messaging", "data-streaming"]
categories: ["System Design"]
---

## Components

producer (API, CDC) -> Kafka (broker) -> Flink(processor) -> consumer (services, DB)
                                    |
                                    |-> Schema Registry (AWS Glue, Confluent Schema Registry) (Avro)

Monitoring & Observability: LGTM
Platform: Kubernetes

## Criteria

- near real-time
  - Producer -> Kafka: no batch
  - Kafka -> Processor: flush immediately, reduce replication lag
  - Kafka -> Consumer: minimize interval
- scale
  - producer, consumer (horizontal)
  - processor (stateful -> vertical)
- resilience
  - broker multi AZ
  - DLQ

