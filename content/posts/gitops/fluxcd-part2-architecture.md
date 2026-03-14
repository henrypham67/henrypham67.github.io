---
title: "Architecting a Multi-Cluster GitOps Repository with FluxCD - Part 2 of 6"
date: 2025-12-20T10:15:00+07:00
draft: true
tags: ["gitops", "fluxcd", "kubernetes", "devops", "infrastructure-as-code"]
categories: ["DevOps", "Kubernetes"]
description: "Learn how to structure a GitOps repository for multi-cluster management with FluxCD. Covers separation of concerns, environment strategies, and best practices for organizing infrastructure as code."
series: ["FluxCD in Production"]
---

# Architecting a Multi-Cluster GitOps Repository with FluxCD

*This is Part 2 of a 6-part series on implementing production-ready GitOps with FluxCD. [See the full series](../fluxcd).*

In [Part 1](../fluxcd-part1-why-gitops), I explained why I chose GitOps and FluxCD over imperative infrastructure management. Now comes the critical foundation: how to structure your GitOps repository.

A good directory structure is the difference between maintainable infrastructure and a YAML nightmare. Get this right, and scaling to multiple clusters and environments becomes natural. Get it wrong, and you'll be constantly fighting your own organization.

## The Architecture Challenge

My requirements were:
- **Multiple environments**: Development and production clusters
- **Different sync strategies**: Dev syncs from GitHub (public), prod syncs from internal Gitea (air-gapped)
- **Shared infrastructure**: Some components (cert-manager, Istio) are common across environments
- **Environment-specific config**: Dev and prod have different domains, IPs, and resource limits
- **Clear separation**: Flux's own configuration should be separate from application infrastructure

Let me show you the structure I landed on after several iterations.

## The Repository Structure

```
fluxcd/
├── clusters/
│   ├── development/              # Dev cluster infrastructure resources
│   │   ├── CertManager.yaml      # cert-manager + Let's Encrypt ClusterIssuer
│   │   ├── Istio.yaml            # Istio CRDs, namespace, and control plane
│   │   ├── CoreDNS.yaml          # Custom DNS configuration
│   │   └── KubeFlowDependencies.yaml  # Base GitRepository for Kubeflow
│   ├── fluxcd/
│   │   ├── development/          # Flux operator config for dev cluster
│   │   │   ├── FluxInstance.yaml # Flux installation and sync config
│   │   │   ├── Cluster.yaml      # Kustomization syncing clusters/development
│   │   │   ├── Shared.yaml       # ConfigMap with shared variables
│   │   │   └── Notification.yaml # Alert/notification configuration
│   │   └── production/           # Flux operator config for prod cluster
│   │       ├── FluxInstance.yaml # Points to internal Gitea
│   │       └── Platform.yaml     # Platform deployment
│   └── production/
│       └── ReadOnlyUser.yaml     # RBAC for read-only cluster access
└── platform/
    ├── base/
    │   ├── gitea/                # Gitea Helm chart values
    │   └── longhorn/             # Longhorn storage Helm chart values
    └── overlays/
        └── production/           # Production-specific overrides
```

Let me break down each directory and explain the design decisions.

## The Layers: Bootstrap, Infrastructure, and Platform

The structure has three distinct layers:

### Layer 1: Bootstrap (`clusters/fluxcd/`)

This directory contains **Flux's own configuration**. It's the bootstrap layer—the first thing you apply to a cluster.

```
clusters/fluxcd/
├── development/
│   ├── FluxInstance.yaml      # Declares how Flux should be installed
│   ├── Cluster.yaml           # Tells Flux to sync clusters/development
│   ├── Shared.yaml            # Environment variables (DNS IPs, domains)
│   └── Notification.yaml      # Slack/Discord alerts
└── production/
    ├── FluxInstance.yaml
    └── Platform.yaml
```

**Key insight**: Each environment gets its own `FluxInstance.yaml` that points to different Git sources:

- **Development**: Syncs from GitHub, can point to feature branches for testing
- **Production**: Syncs from internal Gitea on master branch only

This separation means I can test infrastructure changes in dev before they reach prod, just like application code.

### Layer 2: Infrastructure (`clusters/development/` and `clusters/production/`)

These directories contain the **actual infrastructure resources** for each environment:

```
clusters/development/
├── CertManager.yaml           # ResourceSet with cert-manager + ClusterIssuer
├── Istio.yaml                 # ResourceSet with Istio CRDs + control plane
├── CoreDNS.yaml              # Custom DNS forwarding rules
└── KubeFlowDependencies.yaml # GitRepository pointing to Kubeflow manifests
```

Each YAML file typically contains a `ResourceSet` (more on this in Part 4) that bundles related infrastructure components.

**Why not one big file?** Separating components into individual files makes them:
- **Easier to review**: PRs show exactly what changed (cert-manager vs Istio)
- **Independently deployable**: I can delete `Istio.yaml` without affecting cert-manager
- **Clearer in Git history**: "Update cert-manager" vs "Update infrastructure"

### Layer 3: Platform (`platform/`)

This directory contains **reusable application configurations** using Kustomize's base/overlay pattern:

```
platform/
├── base/
│   ├── gitea/
│   │   ├── kustomization.yaml
│   │   ├── helmrelease.yaml    # Gitea Helm chart config
│   │   └── namespace.yaml
│   └── longhorn/
│       ├── kustomization.yaml
│       └── helmrelease.yaml
└── overlays/
    └── production/
        ├── kustomization.yaml
        └── gitea-values-patch.yaml  # Prod-specific overrides
```

The `base/` contains default configuration. The `overlays/production/` patches it with environment-specific values (domains, resource limits, replica counts).

## Separation of Concerns: Why This Matters

The key architectural principle is **separation of concerns**:

1. **Flux configuration** (`clusters/fluxcd/*`) is isolated from infrastructure
2. **Infrastructure resources** (`clusters/{env}/*`) are isolated from applications
3. **Application bases** (`platform/base/*`) are reusable across environments
4. **Environment overrides** (`platform/overlays/*`) are clearly separated

This makes it obvious:
- Where to change Flux itself (sync interval, alerts)
- Where to change infrastructure (Istio version, cert-manager config)
- Where to change applications (Gitea replicas, Longhorn settings)
- Where to add environment-specific config

## Multi-Environment Strategy: Dev vs. Prod

My dev and prod clusters have fundamentally different sync strategies:

### Development Cluster

```yaml
# clusters/fluxcd/development/FluxInstance.yaml
spec:
  sync:
    kind: GitRepository
    url: "https://github.com/peterbean/fluxcd.git"
    ref: "refs/heads/feat/migrate-istio"  # Can point to feature branches!
    path: "clusters/fluxcd/development"
```

**Development advantages**:
- Syncs from **public GitHub**
- Can test **feature branches** before merging to master
- Allows experimentation without affecting production
- If GitHub is down, dev is down (acceptable for non-critical env)

### Production Cluster

```yaml
# clusters/fluxcd/production/FluxInstance.yaml
spec:
  sync:
    kind: GitRepository
    url: "http://gitea-http.gitea.svc.cluster.local:3000/Platform/fluxcd.git"
    ref: "refs/heads/master"  # Only master branch
    path: "clusters/fluxcd/production"
```

**Production advantages**:
- Syncs from **internal Gitea server** (air-gapped security)
- **Cluster-local** Git source (no external dependencies)
- **Master branch only** (only tested, approved changes)
- Continues working even if external internet is unavailable

This separation achieves:
- **Change control**: Only merged PRs reach production
- **Security**: Production doesn't depend on external GitHub availability
- **Testing**: Feature branches can be tested in dev first

## Managing Environment-Specific Configuration

Different environments need different values (domains, IP addresses, replica counts). I use two approaches:

### Approach 1: ConfigMaps with PostBuild Substitution

For simple values like DNS IPs or domain names:

```yaml
# clusters/fluxcd/development/Shared.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: shared
  namespace: flux-system
data:
  DNS_SERVER_IP: "192.168.1.55"
  DOMAIN: "dev.peterbean.net"
```

Then in Kustomizations, I reference this ConfigMap:

```yaml
spec:
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: shared
```

Now in my manifests I can use `${DNS_SERVER_IP}` and `${DOMAIN}`, and Flux substitutes the values automatically.

**Production has a different ConfigMap** with production IPs and domains. Same code, different values per environment.

### Approach 2: Kustomize Overlays

For complex patches (Helm values, resource limits, replica counts):

```yaml
# platform/overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base/gitea

patches:
  - patch: |-
      - op: replace
        path: /spec/values/ingress/hosts/0/host
        value: git.peterbean.net  # Production domain
    target:
      kind: HelmRelease
      name: gitea
```

This patches the base configuration with production-specific values without duplicating the entire HelmRelease.

## Repository Organization Best Practices

After several refactorings, here are my key learnings:

### 1. One Component Per File

Instead of `infrastructure.yaml` with everything, split into:
- `CertManager.yaml`
- `Istio.yaml`
- `CoreDNS.yaml`

This makes Git diffs readable and changes obvious.

### 2. Name Files After Their Purpose

Use descriptive names: `LetsEncryptIssuer.yaml` is clearer than `issuer.yaml`.

### 3. Keep Flux Config Separate

Never mix Flux's own configuration (`FluxInstance`, `Kustomization`) with infrastructure resources. Flux config lives in `clusters/fluxcd/`, everything else lives in `clusters/{env}/`.

### 4. Use ResourceSets for Related Resources

If resources need to be deployed together with dependencies (like cert-manager + ClusterIssuer), use a ResourceSet. I'll cover this in detail in Part 4.

### 5. Environment Directories Mirror Each Other

Both `clusters/development/` and `clusters/production/` should have similar structure. If dev has `CertManager.yaml`, prod should too. This makes it obvious what infrastructure exists in each environment.

### 6. Platform Base Is Environment-Agnostic

The `platform/base/` directory should have NO environment-specific values. Everything should work with defaults or be overrideable via Kustomize patches.

## Scaling to More Environments

This structure scales naturally to additional environments:

```
clusters/
├── fluxcd/
│   ├── development/
│   ├── staging/          # New environment
│   └── production/
├── development/
├── staging/              # New environment infrastructure
└── production/
```

Each new environment gets:
1. A FluxInstance config in `clusters/fluxcd/{env}/`
2. An infrastructure directory in `clusters/{env}/`
3. Optionally, a Kustomize overlay in `platform/overlays/{env}/`

## The Bootstrap Process

With this structure, bootstrapping a new cluster is straightforward:

1. **Install Flux Operator** (one-time manual step):
   ```bash
   kubectl apply -k "https://github.com/controlplaneio-fluxcd/flux-operator//config/default"
   ```

2. **Apply the FluxInstance** for your environment:
   ```bash
   kubectl apply -f clusters/fluxcd/development/FluxInstance.yaml
   ```

3. **Flux takes over**: It syncs `clusters/fluxcd/development/` which contains a Kustomization pointing to `clusters/development/`, which contains all your infrastructure.

Everything from that point is GitOps. No more manual kubectl commands.

## What's Next

Now that you understand the repository architecture, the next posts will show you how to actually use it:

- **[Part 3: Bootstrapping with Flux Operator](../fluxcd-part3-bootstrapping)** - Deep dive into FluxInstance configuration, component selection, and sync strategies
- **[Part 4: ResourceSets and Dependencies](../fluxcd-part4-resourcesets)** - Managing deployment order and dependency chains
- **[Part 5: Production Operations](../fluxcd-part5-production)** - Helm integration, variable substitution, certificates, and monitoring
- **[Part 6: Lessons Learned](../fluxcd-part6-lessons)** - Real-world gotchas and best practices

In Part 3, I'll show you how to configure FluxInstance to bootstrap Flux itself using GitOps, including auto-upgrades and component customization.

---

**Questions about repository structure?** Find me on Twitter [@henrypham67](https://twitter.com/henrypham67) or check out my [full GitOps repository](https://github.com/peterbean/fluxcd).
