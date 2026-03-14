---
title: "From kubectl Scripts to GitOps: My Journey Implementing FluxCD in Production"
date: 2025-12-20
draft: false
tags: ["gitops", "fluxcd", "kubernetes", "devops", "infrastructure-as-code"]
categories: ["DevOps", "Kubernetes"]
description: "A comprehensive 6-part series on implementing production-ready GitOps with FluxCD v2, covering multi-cluster management, ResourceSets, dependency chains, and lessons learned from migrating a Kubeflow platform from imperative to declarative infrastructure."
series: ["FluxCD in Production"]
---

# From kubectl Scripts to GitOps: My Journey Implementing FluxCD in Production

If you've ever found yourself SSH'd into a production cluster at 2 AM, desperately searching through bash history to figure out which `kubectl apply` command you ran three weeks ago, this series is for you. That was my reality before I embraced GitOps with FluxCD, and the transformation has been nothing short of remarkable.

## About This Series

This is a comprehensive guide to implementing production-ready GitOps with FluxCD v2, including the Flux Operator. This isn't just theory—I share real code, actual challenges, and hard-won lessons from managing a multi-cluster Kubernetes platform running Kubeflow, Istio, cert-manager, and custom platform services on ARM64 architecture.

The series is broken into six focused posts, each covering a specific aspect of FluxCD implementation:

## The Complete Series

### [Part 1: Why GitOps? Choosing FluxCD for Production Kubernetes](index.md)

Learn why GitOps matters and how to choose between FluxCD and ArgoCD.

**What you'll learn**:
- The problems GitOps solves (audit trails, reproducibility, drift prevention)
- FluxCD vs ArgoCD: detailed comparison
- When to choose each tool based on your use case
- The GitOps philosophy and core principles

**Key takeaways**:
- FluxCD: Kubernetes-native, declarative, perfect for infrastructure-as-code teams
- ArgoCD: Powerful UI, better for teams needing visual cluster management
- Both are excellent—choose based on your team's needs

---

### [Part 2: Architecting a Multi-Cluster GitOps Repository with FluxCD](./fluxcd-part2-architecture)

How to structure a GitOps repository for multi-environment management.

**What you'll learn**:
- Repository directory structure for multi-cluster setups
- Separation of concerns: Flux config vs infrastructure vs applications
- Multi-environment strategy (dev vs prod sync approaches)
- Managing environment-specific configuration

**Key patterns**:
- `clusters/fluxcd/`: Flux's own configuration (FluxInstance)
- `clusters/{env}/`: Environment-specific infrastructure resources
- `platform/base/`: Reusable application configurations
- `platform/overlays/`: Environment-specific overrides

**Code example**: Complete repository structure supporting dev (GitHub sync) and prod (internal Gitea sync) with feature branch testing.

---

### [Part 3: Bootstrapping FluxCD with the Flux Operator](./fluxcd-part3-bootstrapping)

Learn how to bootstrap Flux using the Flux Operator with FluxInstance resources.

**What you'll learn**:
- Traditional `flux bootstrap` vs Flux Operator approach
- FluxInstance configuration deep dive
- Auto-upgrades and version management
- Component selection and customization
- Dev vs prod sync strategies
- Handling private Git repositories

**Key features**:
- `version: "2.x"` for automatic Flux upgrades
- Kustomize patches for customizing Flux deployments (tolerations, node selectors)
- Feature branch testing in dev, master-only in prod

**Code example**: Complete FluxInstance with ARM64 tolerations, component selection, and sync configuration.

---

### [Part 4: Mastering FluxCD ResourceSets and Dependency Chains](./fluxcd-part4-resourcesets)

Solve the dependency puzzle with ResourceSets and health checks.

**What you'll learn**:
- The Kustomization dependency limitation (and why it matters)
- ResourceSet pattern for mixing Kustomizations with raw resources
- Building complex dependency chains (Istio example: CRDs → namespace → control plane)
- Health check syntax for different resource types
- Dependency syntax (full vs short form)

**Critical insight**: Kustomizations can only depend on other Kustomizations if dependencies contain ONLY Kustomizations. ResourceSets solve this by bundling both resource types.

**Code example**: Complete Istio deployment with multi-stage dependencies and comprehensive health checks.

---

### [Part 5: Production FluxCD: Operations, Monitoring, and Best Practices](./fluxcd-part5-production)

Production-ready patterns for Helm, secrets, certificates, and monitoring.

**What you'll learn**:
- Variable substitution with PostBuild (ConfigMaps/Secrets)
- Helm integration with HelmRelease and Kustomize overlays
- Automated certificate management with cert-manager and Let's Encrypt
- Monitoring Flux with Prometheus and Grafana
- Slack/Discord notifications for reconciliation failures
- Day-to-day operational workflows
- ARM64 architecture: injecting tolerations at scale

**Key patterns**:
- Environment-specific ConfigMaps for variable substitution
- HelmRelease + Kustomize overlays for environment-specific Helm values
- ClusterIssuer for automatic TLS certificate management
- Flux metrics and alerts for operational visibility

**Code example**: Complete HelmRelease with Kustomize patches, cert-manager ClusterIssuer with Route53, and notification configuration.

---

### [Part 6: FluxCD in Production: Lessons Learned and Hard-Won Wisdom](./fluxcd-part6-lessons)

Real-world lessons, gotchas, and hard-won wisdom from running FluxCD in production.

**What you'll learn**:
- Start small, grow incrementally (don't migrate everything at once)
- Health checks are non-negotiable (dependency chains break without them)
- ResourceSets vs Kustomizations: when to use each
- Reconciliation interval trade-offs
- Flux bootstrap vs Flux Operator decision criteria
- Git repository size optimization
- Secrets management planning (Sealed Secrets, SOPS)
- Prune gotchas and namespace creation pitfalls
- Monitoring Flux itself

**Results**:
- Auditability: Every change in Git with full history
- Reproducibility: Entire cluster rebuildable from Git
- Collaboration: Pull request-based infrastructure changes
- Automation: Zero manual kubectl commands
- Peace of mind: `git revert` for rollbacks

**ROI**: 3 weeks investment, countless hours saved, zero environment drift incidents.

---

## What You'll Build

By the end of this series, you'll have:

✅ A production-ready GitOps setup with FluxCD
✅ Multi-cluster management (dev, prod) with different sync strategies
✅ Complex dependency chains orchestrated automatically
✅ Automated certificate management with cert-manager
✅ Helm chart deployments with environment-specific overrides
✅ Monitoring and alerting for Flux itself
✅ A reproducible infrastructure entirely in Git

## Who This Series Is For

This series is for:
- **Kubernetes operators** tired of imperative kubectl scripts
- **DevOps engineers** implementing GitOps for the first time
- **Platform engineers** managing multi-cluster infrastructure
- **Teams** wanting to improve infrastructure auditability and collaboration

You should have:
- Basic Kubernetes knowledge (Deployments, Services, ConfigMaps)
- Familiarity with `kubectl` commands
- Understanding of Git workflows
- (Optional) Experience with Helm and Kustomize

## My Setup

The examples in this series come from a real production environment:

- **Platform**: Multi-cluster Kubernetes (dev + prod)
- **Architecture**: ARM64 nodes
- **Stack**: Kubeflow, Istio, cert-manager, Longhorn, Gitea
- **Flux version**: FluxCD v2 with Flux Operator
- **Git**: GitHub (dev), Internal Gitea (prod)
- **Certificates**: Let's Encrypt with DNS-01 challenges (AWS Route53)

## Resources

- [FluxCD Documentation](https://fluxcd.io/docs/)
- [Flux Operator GitHub](https://github.com/controlplaneio-fluxcd/flux-operator)
- [GitOps Principles](https://opengitops.dev/)
- [My GitOps Repository](https://github.com/peterbean/fluxcd) - See the real implementation

## Get Started

Ready to transform your Kubernetes operations? Start with [Part 1: Why GitOps?](index.md) and work through the series at your own pace.

Each post builds on the previous ones, but they're also designed to stand alone—if you're already familiar with GitOps concepts, jump straight to the ResourceSets post or the lessons learned.

---

**Questions or want to share your GitOps journey?** Find me on Twitter [@henrypham67](https://twitter.com/henrypham67). I'd love to hear about your experience implementing GitOps!
