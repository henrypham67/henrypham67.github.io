---
title: 'Open Policy Agent - OPA'
date: 2026-02-28T11:12:14+07:00
draft: true
---

## Definition

A unifying policy management engine

## Use cases

Kubernetes Admission Control: Enforces rules during deployment, e.g., requiring vulnerability-scanned images, mandatory labels for security/cost, or blocking unsafe configurations.
Microservices Authorization: Implements ABAC/RBAC for fine-grained access, using user attributes, roles, or environment factors to allow/deny requests.
CI/CD Pipeline Enforcement: Checks builds/deployments for compliance, e.g., registry restrictions or policy approvals before promotion.
API Gateway Policies: Handles authorization at ingress, validating requests based on JWTs, IPs, or time-based rules.
Cloud Resource Access: Controls access to resources like S3 buckets via attributes (team, IP, time), ensuring security/compliance.
Infrastructure Governance: Automates approvals, cost controls, and misconfiguration prevention across clouds.
