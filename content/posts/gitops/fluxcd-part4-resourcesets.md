---
title: "Mastering FluxCD ResourceSets and Dependency Chains - Part 4 of 6"
date: 2025-12-20T10:45:00+07:00
draft: true
tags: ["gitops", "fluxcd", "kubernetes", "devops", "infrastructure-as-code"]
categories: ["DevOps", "Kubernetes"]
description: "Learn how to manage complex deployment dependencies in FluxCD using ResourceSets. Covers dependency chains, health checks, and orchestrating multi-component deployments like Istio."
series: ["FluxCD in Production"]
---

# Mastering FluxCD ResourceSets and Dependency Chains

*This is Part 4 of a 6-part series on implementing production-ready GitOps with FluxCD. [See the full series](../fluxcd).*

In [Part 3](../fluxcd-part3-bootstrapping), I showed you how to bootstrap Flux using the Flux Operator with FluxInstance resources. Now comes one of the hardest challenges in GitOps: **managing deployment order and dependencies**.

This is where I spent days banging my head against the wall, so let me save you the trouble. Flux's standard Kustomization resource has a critical limitation that isn't well documented, and understanding it is key to building reliable infrastructure automation.

## The Dependency Problem

Not all infrastructure can deploy in parallel. Some components have strict ordering requirements:

- **cert-manager** must be running before you can create ClusterIssuers
- **Istio CRDs** must exist before you deploy the Istio control plane
- **Namespaces** must exist before you create resources in them
- **Secrets** must exist before Pods that reference them can start

In the imperative kubectl world, I handled this with sleep commands and retry loops in bash scripts. Disgusting, but it worked. In the declarative GitOps world, Flux needs to understand these dependencies natively.

Flux provides the `dependsOn` field for Kustomizations:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: istio-install
spec:
  dependsOn:
    - name: istio-crds
  # ... rest of spec
```

This tells Flux: "Don't reconcile `istio-install` until `istio-crds` is ready."

Simple, right? **Wrong.**

## The Kustomization Dependency Limitation

Here's the gotcha that cost me hours: **Kustomizations can only depend on other Kustomizations if those dependencies exclusively contain Kustomization resources**.

Let me show you the problem. I tried to deploy cert-manager like this:

```yaml
# ❌ This doesn't work!
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: cert-manager-base
  namespace: flux-system
spec:
  interval: 5m0s
  path: ./common/cert-manager/base
  prune: true
  sourceRef:
    kind: GitRepository
    name: kubeflow-manifests
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: letsencrypt-issuer
  namespace: flux-system
spec:
  dependsOn:
    - name: cert-manager-base  # This fails!
  interval: 5m0s
  path: ./clusters/development/cert-manager
  prune: true
  sourceRef:
    kind: GitRepository
    name: flux-system
```

I wanted `letsencrypt-issuer` to wait for `cert-manager-base` to be ready. But the `letsencrypt-issuer` Kustomization contains a raw `ClusterIssuer` resource, not just Kustomizations.

**Flux errors with**: "Kustomization dependency 'cert-manager-base' contains non-Kustomization resources, cannot establish dependency."

This is a fundamental limitation: **you can't create dependency chains when mixing raw Kubernetes resources with Kustomizations**.

But in real infrastructure, you NEED to mix them. cert-manager is a Helm chart (deployed via Kustomization), but the ClusterIssuer is a raw custom resource. They must be deployed together, and the ClusterIssuer must wait for cert-manager to be ready.

## Enter ResourceSet: The Solution

This is where the Flux Operator's `ResourceSet` comes to the rescue. ResourceSet is a wrapper that can contain **both Kustomizations AND raw Kubernetes resources**, and ResourceSets can depend on other ResourceSets.

Here's the solution:

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: cert-manager
  namespace: flux-system
spec:
  commonMetadata:
    labels:
      app.kubernetes.io/part-of: kubeflow
  wait: true
  dependsOn:
    - apiVersion: fluxcd.controlplane.io/v1
      kind: ResourceSet
      name: cert-manager-base
      namespace: flux-system
  resources:
    # First: Deploy cert-manager via Kustomization
    - apiVersion: kustomize.toolkit.fluxcd.io/v1
      kind: Kustomization
      metadata:
        name: cert-manager
        namespace: flux-system
      spec:
        interval: 5m0s
        path: ./common/cert-manager/base
        prune: true
        targetNamespace: cert-manager
        sourceRef:
          kind: GitRepository
          name: kubeflow-manifests
        healthChecks:
          - apiVersion: apps/v1
            kind: Deployment
            name: cert-manager
            namespace: cert-manager
          - apiVersion: apps/v1
            kind: Deployment
            name: cert-manager-webhook
            namespace: cert-manager

    # Second: Create the ClusterIssuer (raw resource!)
    - apiVersion: cert-manager.io/v1
      kind: ClusterIssuer
      metadata:
        name: letsencrypt-route53
        namespace: flux-system
      spec:
        acme:
          email: peterbean410@gmail.com
          server: https://acme-v02.api.letsencrypt.org/directory
          privateKeySecretRef:
            name: letsencrypt-route53
          solvers:
            - dns01:
                route53:
                  region: us-east-1
                  accessKeyIDSecretRef:
                    name: aws-route53-secret
                    key: access-key-id
                  secretAccessKeySecretRef:
                    name: aws-route53-secret
                    key: secret-access-key
```

**What changed?**
1. I wrapped everything in a `ResourceSet` instead of separate Kustomizations
2. The `resources` list contains BOTH the cert-manager Kustomization AND the ClusterIssuer
3. The `wait: true` flag ensures Flux waits for all resources to be healthy before marking the ResourceSet ready
4. Health checks on the cert-manager Deployments ensure the operator is actually running before creating ClusterIssuers

Now the ClusterIssuer is guaranteed to be created only after cert-manager is fully operational.

## ResourceSet Dependency Syntax

The dependency syntax is critical and differs based on what you're depending on.

### When ResourceSets Depend on Other ResourceSets

Use the **full API reference**:

```yaml
dependsOn:
  - apiVersion: fluxcd.controlplane.io/v1
    kind: ResourceSet
    name: cert-manager-base
    namespace: flux-system
```

You must include `apiVersion`, `kind`, `name`, and `namespace`.

### When Kustomizations Inside a ResourceSet Depend on Each Other

Use the **short name-only form**:

```yaml
dependsOn:
  - name: istio-crds  # Just the name
```

This was not documented clearly anywhere, and I spent hours debugging reconciliation failures before figuring it out. If you use the wrong syntax, Flux silently fails to establish the dependency, and resources deploy in random order.

## Building Complex Dependency Chains: The Istio Example

Once I understood ResourceSets, I could build complex multi-stage deployments. Istio was the perfect test case because it requires strict ordering:

1. Install Istio CRDs
2. Create the `istio-system` namespace
3. Install the Istio control plane (istiod)

Each step depends on the previous one. Here's how I modeled it with a single ResourceSet:

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: istio
  namespace: flux-system
spec:
  commonMetadata:
    labels:
      app.kubernetes.io/part-of: kubeflow
  wait: true
  dependsOn:
    - apiVersion: fluxcd.controlplane.io/v1
      kind: ResourceSet
      name: kubeflow-dependencies
      namespace: flux-system
  resources:
    # Step 1: Install Istio CRDs
    - apiVersion: kustomize.toolkit.fluxcd.io/v1
      kind: Kustomization
      metadata:
        name: istio-crds
        namespace: flux-system
      spec:
        interval: 5m0s
        path: ./common/istio/istio-crds/base
        prune: true
        sourceRef:
          kind: GitRepository
          name: kubeflow-manifests
        healthChecks:
          - apiVersion: apiextensions.k8s.io/v1
            kind: CustomResourceDefinition
            name: gateways.networking.istio.io
          - apiVersion: apiextensions.k8s.io/v1
            kind: CustomResourceDefinition
            name: virtualservices.networking.istio.io

    # Step 2: Create istio-system namespace
    - apiVersion: kustomize.toolkit.fluxcd.io/v1
      kind: Kustomization
      metadata:
        name: istio-ns
        namespace: flux-system
      spec:
        interval: 5m0s
        path: ./common/istio/istio-namespace/base
        prune: true
        sourceRef:
          kind: GitRepository
          name: kubeflow-manifests
        dependsOn:
          - name: istio-crds  # Short form!
        healthChecks:
          - apiVersion: v1
            kind: Namespace
            name: istio-system

    # Step 3: Install Istio control plane
    - apiVersion: kustomize.toolkit.fluxcd.io/v1
      kind: Kustomization
      metadata:
        name: istio-install
        namespace: flux-system
      spec:
        interval: 5m0s
        path: ./common/istio/istio-install/overlays/oauth2-proxy
        prune: true
        targetNamespace: istio-system
        sourceRef:
          kind: GitRepository
          name: kubeflow-manifests
        dependsOn:
          - name: istio-ns  # Short form!
        healthChecks:
          - apiVersion: apps/v1
            kind: Deployment
            name: istiod
            namespace: istio-system
```

**The dependency chain**:
```
istio-crds (deploys CRDs, waits for CRDs to register)
  └─→ istio-ns (creates namespace, waits for namespace to be active)
        └─→ istio-install (deploys istiod, waits for deployment to be ready)
```

Flux orchestrates this entire sequence automatically. When I push changes to Git, Flux reconciles in the correct order, waiting for each step to be healthy before proceeding.

## The Full Cluster Dependency Graph

My complete infrastructure has a deep dependency tree:

```
kubeflow-dependencies (GitRepository pointing to Kubeflow manifests)
  ├─→ cert-manager-base (cert-manager CRDs and namespace)
  │     └─→ cert-manager (cert-manager deployment + ClusterIssuers)
  └─→ istio (Istio CRDs → namespace → control plane)
```

All of this is managed through ResourceSets. When I bootstrap a new cluster:
1. Flux creates the `kubeflow-dependencies` GitRepository
2. Once synced, it creates `cert-manager-base` and `istio` in parallel (they don't depend on each other)
3. When `cert-manager-base` is ready, it creates the `cert-manager` ResourceSet with ClusterIssuers
4. The `istio` ResourceSet internally orchestrates CRDs → namespace → control plane

Zero manual intervention. Zero sleep commands. Just declarative dependencies.

## Health Checks: The Critical Missing Piece

Dependencies are useless if Flux doesn't know when a resource is "ready." This is where health checks come in, and they're **absolutely critical** for reliable deployments.

Without health checks, Flux considers a Kustomization ready as soon as it applies the manifests—even if pods are still starting, CRDs aren't registered yet, or services aren't reachable. This causes race conditions where dependent resources try to use things that don't exist yet.

Every Kustomization I create includes health checks for all critical resources.

### Health Check Syntax by Resource Type

The syntax varies based on what you're checking:

#### For CustomResourceDefinitions (No Namespace)

```yaml
healthChecks:
  - apiVersion: apiextensions.k8s.io/v1
    kind: CustomResourceDefinition
    name: certificates.cert-manager.io
  - apiVersion: apiextensions.k8s.io/v1
    kind: CustomResourceDefinition
    name: issuers.cert-manager.io
```

CRDs are cluster-scoped, so no namespace.

#### For Deployments (Include Namespace)

```yaml
healthChecks:
  - apiVersion: apps/v1
    kind: Deployment
    name: cert-manager
    namespace: cert-manager
  - apiVersion: apps/v1
    kind: Deployment
    name: cert-manager-webhook
    namespace: cert-manager
```

#### For Namespaces

```yaml
healthChecks:
  - apiVersion: v1
    kind: Namespace
    name: istio-system
```

#### For Custom Resources

```yaml
healthChecks:
  - apiVersion: cert-manager.io/v1
    kind: ClusterIssuer
    name: letsencrypt-route53
```

Flux waits for the resource to exist and for its status to indicate readiness (e.g., `Ready=True` condition).

### Real-World Example: Istio Health Checks

I learned the importance of health checks the hard way when Istio installations kept failing. The `istio-install` Kustomization would try to create VirtualServices before the CRDs were registered, causing errors like:

```
error: unable to recognize "STDIN": no matches for kind "VirtualService" in version "networking.istio.io/v1beta1"
```

The fix was adding comprehensive health checks to `istio-crds`:

```yaml
healthChecks:
  - apiVersion: apiextensions.k8s.io/v1
    kind: CustomResourceDefinition
    name: gateways.networking.istio.io
  - apiVersion: apiextensions.k8s.io/v1
    kind: CustomResourceDefinition
    name: virtualservices.networking.istio.io
  - apiVersion: apiextensions.k8s.io/v1
    kind: CustomResourceDefinition
    name: destinationrules.networking.istio.io
```

Now Flux waits for all three CRDs to be fully registered (not just created, but actually available in the API server) before marking `istio-crds` as ready. This ensures `istio-install` has everything it needs.

## The `wait: true` Flag

ResourceSets have a `wait` field:

```yaml
spec:
  wait: true
```

When `true`, Flux waits for **all resources** in the ResourceSet to be healthy before marking the ResourceSet as ready. This is essential for dependency chains—you want the entire ResourceSet (not just individual resources) to be fully operational before dependents proceed.

I set `wait: true` on every ResourceSet. The alternative (`wait: false`) applies resources and immediately marks the ResourceSet ready, which defeats the purpose of health checks.

## Common Patterns and Best Practices

After building dozens of ResourceSets, here are my patterns:

### Pattern 1: Base + Configuration

Separate the base installation from configuration:

```yaml
# ResourceSet 1: Base (just the Helm chart or operator)
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: cert-manager-base

# ResourceSet 2: Configuration (ClusterIssuers, Certificates)
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: cert-manager
spec:
  dependsOn:
    - apiVersion: fluxcd.controlplane.io/v1
      kind: ResourceSet
      name: cert-manager-base
```

This separation makes it easy to change configuration (ClusterIssuers) without redeploying the base (cert-manager operator).

### Pattern 2: CRDs → Namespace → Application

For anything that uses CRDs:

```yaml
1. Install CRDs (Kustomization with CRD health checks)
2. Create namespace (Kustomization with Namespace health check)
3. Deploy application (Kustomization with Deployment health checks)
```

All inside a single ResourceSet with internal `dependsOn` between Kustomizations.

### Pattern 3: Shared Dependencies

Multiple ResourceSets can depend on the same base:

```yaml
cert-manager-base
  ├─→ cert-manager (ClusterIssuers)
  ├─→ app-certificates (Certificate resources for apps)
  └─→ ingress-tls (TLS secrets for ingresses)
```

This models "cert-manager must be ready before anything creates Certificates."

## When to Use ResourceSets vs. Plain Kustomizations

**Use plain Kustomizations when**:
- You're deploying a single Helm chart or Kustomize directory
- No raw Kubernetes resources need to be bundled with it
- Dependencies are simple (just wait for another Kustomization)

**Use ResourceSets when**:
- You need to bundle Kustomizations with raw Kubernetes resources
- You're building complex multi-stage deployments (CRDs → namespace → app)
- Dependencies involve mixing different resource types

I wasted days trying to make plain Kustomizations work before discovering ResourceSets. Don't make the same mistake.

## What's Next

Now that you can manage complex dependencies and orchestrate multi-component deployments, the next post covers production operations: Helm integration, variable substitution, secret management, certificate automation, and monitoring.

- **[Part 5: Production Operations](../fluxcd-part5-production)** - Helm charts, PostBuild variables, cert-manager, and Flux monitoring
- **[Part 6: Lessons Learned](../fluxcd-part6-lessons)** - Real-world gotchas, best practices, and hard-won wisdom

---

**Questions about ResourceSets or dependency management?** Find me on Twitter [@henrypham67](https://twitter.com/henrypham67). I'd love to help debug your Flux setup!
