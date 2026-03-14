---
title: "Bootstrapping FluxCD with the Flux Operator - Part 3 of 6"
date: 2025-12-20T10:30:00+07:00
draft: true
tags: ["gitops", "fluxcd", "kubernetes", "devops", "infrastructure-as-code"]
categories: ["DevOps", "Kubernetes"]
description: "Learn how to bootstrap FluxCD using the Flux Operator with FluxInstance resources. Covers declarative installation, auto-upgrades, component selection, and environment-specific sync strategies."
series: ["FluxCD in Production"]
---

# Bootstrapping FluxCD with the Flux Operator

*This is Part 3 of a 6-part series on implementing production-ready GitOps with FluxCD. [See the full series](../fluxcd).*

In [Part 2](../fluxcd-part2-architecture), I showed you how to structure a GitOps repository for multi-environment management. Now let's dive into the most critical piece: bootstrapping Flux itself using the Flux Operator.

The Flux Operator was a game-changer for me. Instead of running `flux bootstrap` commands with CLI flags that I'd inevitably forget, I could declare my entire Flux installation as a Kubernetes resource. And because it's declarative, Flux can manage its own upgrades via GitOps. This is infrastructure eating its own dog food, and it's beautiful.

## Traditional Bootstrap vs. Flux Operator

Let me first explain the traditional approach and why I moved away from it.

### The Traditional Way: `flux bootstrap`

The standard Flux installation uses the `flux bootstrap` CLI command:

```bash
flux bootstrap github \
  --owner=peterbean \
  --repository=fluxcd \
  --branch=main \
  --path=clusters/development \
  --personal
```

This command:
1. Installs Flux components (controllers) into your cluster
2. Creates a GitRepository resource pointing to your repo
3. Creates a Kustomization to sync the specified path
4. Commits Flux manifests back to your repo

**The problems**:
- CLI flags must be documented somewhere (or you'll forget them)
- Upgrading Flux requires running commands, not committing to Git
- Multi-cluster setups require running bootstrap for each cluster
- You're managing Flux with imperative commands while trying to do declarative infrastructure

### The Flux Operator Way: FluxInstance

The Flux Operator introduces the `FluxInstance` custom resource. Your entire Flux installation becomes a YAML file you can commit to Git:

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
  components:
    - source-controller
    - kustomize-controller
    - helm-controller
    - notification-controller
  sync:
    kind: GitRepository
    url: "https://github.com/peterbean/fluxcd.git"
    ref: "refs/heads/main"
    path: "clusters/fluxcd/development"
```

**The advantages**:
- Entire Flux config is version-controlled
- Flux manages its own upgrades (when you change `version`)
- Multi-cluster management: apply different FluxInstance per cluster
- No CLI commands to remember—everything is declarative

Let me break down each section of the FluxInstance.

## FluxInstance Deep Dive

Here's my development FluxInstance with detailed explanations:

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
  components:
    - source-controller
    - kustomize-controller
    - helm-controller
    - notification-controller
  cluster:
    type: kubernetes
    multitenant: false
    networkPolicy: true
  kustomize:
    patches:
      - target:
          kind: Deployment
        patch: |
          - op: add
            path: /spec/template/spec/tolerations
            value:
              - key: "CriticalAddonsOnly"
                operator: "Exists"
              - key: "arch"
                effect: "NoExecute"
                value: "arm64"
  sync:
    kind: GitRepository
    url: "https://github.com/peterbean/fluxcd.git"
    ref: "refs/heads/feat/migrate-istio"
    path: "clusters/fluxcd/development"
    pullSecret: "flux-system"
```

Let me break down each section.

### Distribution: Auto-Upgrades

```yaml
distribution:
  version: "2.x"
  registry: "ghcr.io/fluxcd"
```

**`version: "2.x"`** is the killer feature. This tells Flux to automatically pull the latest v2.x release. When Flux releases v2.5.0, v2.6.0, etc., the Flux Operator automatically upgrades Flux without me doing anything.

You can also pin to specific versions:
- `version: "2.4.x"` - Latest patch in the 2.4 series
- `version: "2.4.0"` - Exact version
- `version: "2.x"` - Latest v2 (what I use for dev)

For production, I use `"2.x"` but with additional testing: I test auto-upgrades in dev first, and if something breaks, I temporarily pin production to a specific version while I investigate.

**`registry`** specifies where to pull Flux images from. The default `ghcr.io/fluxcd` is fine for most use cases. If you're in an air-gapped environment, you'd mirror images to an internal registry and point here.

### Components: Only What You Need

```yaml
components:
  - source-controller
  - kustomize-controller
  - helm-controller
  - notification-controller
```

Flux is modular. Each controller has a specific job:

- **source-controller**: Fetches artifacts from Git, Helm repos, S3 buckets, OCI registries
- **kustomize-controller**: Applies Kustomize directories and raw manifests
- **helm-controller**: Manages Helm releases
- **notification-controller**: Sends alerts to Slack, Discord, etc.
- **image-reflector-controller**: Scans container registries for new image tags
- **image-automation-controller**: Updates Git with new image tags

I explicitly list only the components I need. For my setup, I don't use image automation (yet), so I omit those controllers. This keeps the installation lean and reduces resource usage.

If I later want image automation, I just add those components to the list and commit. Flux installs them automatically.

### Cluster Configuration: Multi-Tenancy and Security

```yaml
cluster:
  type: kubernetes
  multitenant: false
  networkPolicy: true
```

**`type: kubernetes`**: Standard Kubernetes cluster (as opposed to `openshift` for OpenShift-specific configurations).

**`multitenant: false`**: I'm the sole operator, so I don't need tenant isolation. If you're running Flux for multiple teams with separate namespaces, set this to `true` to enable Flux's multi-tenancy features (scoped service accounts, RBAC, etc.).

**`networkPolicy: true`**: Enables network policies to restrict communication between Flux components. This hardens security by ensuring only necessary pod-to-pod traffic is allowed.

### Kustomize Patches: Customizing Flux's Own Deployments

This is where things get powerful. You can patch Flux's own Deployments before they're applied:

```yaml
kustomize:
  patches:
    - target:
        kind: Deployment
      patch: |
        - op: add
          path: /spec/template/spec/tolerations
          value:
            - key: "CriticalAddonsOnly"
              operator: "Exists"
            - key: "arch"
              effect: "NoExecute"
              value: "arm64"
```

My cluster runs on ARM64 architecture, so all workloads need tolerations to schedule on ARM64 nodes. By patching Flux's Deployments here, I ensure all Flux controllers can run on my nodes.

**Other use cases for patches**:
- Adding resource limits to Flux controllers
- Injecting node selectors for dedicated Flux nodes
- Adding annotations for service meshes (Istio, Linkerd)
- Configuring pod security contexts

The patch syntax uses JSON Patch (RFC 6902). The `target` selects which resources to patch (here, all Deployments).

### Sync Configuration: Where Flux Pulls From

```yaml
sync:
  kind: GitRepository
  url: "https://github.com/peterbean/fluxcd.git"
  ref: "refs/heads/feat/migrate-istio"
  path: "clusters/fluxcd/development"
  pullSecret: "flux-system"
```

This is the most important section. It tells Flux **where to sync configuration from**.

**`kind: GitRepository`**: Flux will create a GitRepository resource. You could also use `OCIRepository` for OCI artifacts or `Bucket` for S3-compatible storage.

**`url`**: The Git repository URL. For development, I use public GitHub. For production, I use an internal Gitea server.

**`ref`**: Which Git reference to track. Notice I'm using a **feature branch** in development (`feat/migrate-istio`). This lets me test infrastructure changes before merging to master.

Supported ref formats:
- `refs/heads/main` - Track the main branch
- `refs/heads/feat/my-feature` - Track a feature branch
- `refs/tags/v1.0.0` - Track a specific tag

**`path`**: The directory within the repo to sync. Flux will recursively apply all Kustomizations, HelmReleases, and raw manifests in this path.

**`pullSecret`**: If your repo is private (mine is), reference a Secret containing Git credentials. I'll cover this next.

## Handling Private Repositories

If your Git repository is private, Flux needs credentials. You create a Secret with SSH keys or a personal access token:

### Using SSH Keys (Recommended)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: flux-system
  namespace: flux-system
stringData:
  identity: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    <your SSH private key>
    -----END OPENSSH PRIVATE KEY-----
  known_hosts: |
    github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl
```

Generate the key:
```bash
ssh-keygen -t ed25519 -C "flux"
```

Add the public key to your GitHub repository's deploy keys with read-only access.

### Using Personal Access Tokens

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: flux-system
  namespace: flux-system
stringData:
  username: git
  password: <your GitHub personal access token>
```

Then in your FluxInstance, use HTTPS URL with `pullSecret`:

```yaml
sync:
  url: "https://github.com/peterbean/fluxcd.git"
  pullSecret: "flux-system"
```

## Development vs. Production Sync Strategies

My dev and prod clusters have different FluxInstances with different sync strategies:

### Development FluxInstance

```yaml
sync:
  kind: GitRepository
  url: "https://github.com/peterbean/fluxcd.git"
  ref: "refs/heads/feat/migrate-istio"  # Feature branches!
  path: "clusters/fluxcd/development"
```

**Why feature branches?** In development, I can test infrastructure changes by pointing Flux to a feature branch. If it breaks, I just revert the FluxInstance to point back to master. No harm done.

This is infrastructure CI: test in dev before merging to master.

### Production FluxInstance

```yaml
sync:
  kind: GitRepository
  url: "http://gitea-http.gitea.svc.cluster.local:3000/Platform/fluxcd.git"
  ref: "refs/heads/master"  # Master only
  path: "clusters/fluxcd/production"
```

**Production differences**:
- Points to **internal Gitea server** (cluster-local service)
- **Master branch only** (only tested, approved changes)
- Air-gapped: production doesn't depend on external GitHub

This achieves:
- **Change control**: Only merged PRs reach production
- **Security**: No external dependencies
- **Reliability**: Continues working even if GitHub is down

## The Bootstrap Process

With the Flux Operator, bootstrapping a new cluster is simple:

### Step 1: Install the Flux Operator (One-Time)

```bash
kubectl apply -k "https://github.com/controlplaneio-fluxcd/flux-operator//config/default"
```

This installs the Flux Operator itself (not Flux). The operator watches for FluxInstance resources.

### Step 2: Create the Pull Secret (If Using Private Repos)

```bash
kubectl create namespace flux-system

kubectl create secret generic flux-system \
  --namespace=flux-system \
  --from-file=identity=./flux-key \
  --from-file=known_hosts=./known_hosts
```

### Step 3: Apply Your FluxInstance

```bash
kubectl apply -f clusters/fluxcd/development/FluxInstance.yaml
```

**That's it.** The Flux Operator:
1. Installs Flux controllers based on your `components` list
2. Applies any `kustomize.patches`
3. Creates a GitRepository pointing to your `sync.url`
4. Creates a Kustomization to sync the `sync.path`

Flux takes over from here, pulling your infrastructure from Git and applying it.

### Step 4: Watch Flux Bootstrap Itself

```bash
kubectl get fluxinstance -n flux-system
kubectl get pods -n flux-system
kubectl get gitrepositories -n flux-system
kubectl get kustomizations -n flux-system
```

Within a minute or two, you'll see:
- Flux controllers running (source-controller, kustomize-controller, etc.)
- GitRepository synced
- Kustomizations reconciling your infrastructure

## Upgrading Flux

To upgrade Flux, just change the version in your FluxInstance and commit:

```yaml
distribution:
  version: "2.5.x"  # Changed from "2.4.x"
```

Push to Git. Flux sees the change, and the Flux Operator upgrades the controllers. No CLI commands, no manual intervention.

For production, I test upgrades in dev first:
1. Update dev FluxInstance to new version
2. Monitor for issues over a few days
3. If stable, update prod FluxInstance

## Flux Operator vs. `flux bootstrap`

When should you use each?

**Use Flux Operator if**:
- You want Flux to manage its own upgrades
- You're managing multiple clusters
- You want everything declarative and version-controlled
- You need to customize Flux installations per cluster

**Use `flux bootstrap` if**:
- You're just getting started and want simplicity
- You have a single cluster
- You're okay with CLI-driven upgrades
- You don't need per-cluster Flux customization

For production multi-cluster setups, the Flux Operator is the clear winner.

## What's Next

Now that Flux is installed and syncing from Git, the next challenge is managing deployment order and dependencies. Not everything can apply in parallel—cert-manager needs to be ready before you create ClusterIssuers, Istio CRDs must exist before you deploy the control plane.

In the next post, I'll show you how to solve this with ResourceSets and dependency chains.

- **[Part 4: ResourceSets and Dependencies](../fluxcd-part4-resourcesets)** - Managing complex deployment order with health checks
- **[Part 5: Production Operations](../fluxcd-part5-production)** - Helm, secrets, variable substitution, and monitoring
- **[Part 6: Lessons Learned](../fluxcd-part6-lessons)** - Real-world gotchas and best practices

---

**Questions about bootstrapping Flux?** Find me on Twitter [@henrypham67](https://twitter.com/henrypham67). I'd love to hear how you're using the Flux Operator!
