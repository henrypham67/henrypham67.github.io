---
title: "Production FluxCD: Operations, Monitoring, and Best Practices - Part 5 of 6"
date: 2025-12-20T11:00:00+07:00
draft: true
tags: ["gitops", "fluxcd", "kubernetes", "devops", "infrastructure-as-code", "helm"]
categories: ["DevOps", "Kubernetes"]
description: "Production-ready FluxCD operations including Helm integration, variable substitution, automated certificate management, monitoring, notifications, and day-to-day workflows."
series: ["FluxCD in Production"]
---

# Production FluxCD: Operations, Monitoring, and Best Practices

*This is Part 5 of a 6-part series on implementing production-ready GitOps with FluxCD. [See the full series](../fluxcd).*

In [Part 4](../fluxcd-part4-resourcesets), I showed you how to manage complex dependencies with ResourceSets. Now let's cover the production operations that make FluxCD viable for real-world infrastructure: Helm chart management, environment-specific configuration, automated certificates, monitoring, and day-to-day workflows.

These are the patterns that transformed FluxCD from "interesting tool" to "production-critical infrastructure" for me.

## Variable Substitution with PostBuild

One challenge with GitOps is handling environment-specific values. You don't want to hardcode production IPs, domains, or API keys in your Git repository. But you also want everything to be declarative.

Flux solves this elegantly with **PostBuild variable substitution** using ConfigMaps or Secrets.

### The Pattern

First, create a ConfigMap with environment-specific variables:

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
  ENVIRONMENT: "development"
```

Then in your Kustomizations, reference this ConfigMap:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: coredns
  namespace: flux-system
spec:
  interval: 5m0s
  path: ./clusters/development
  prune: true
  sourceRef:
    kind: GitRepository
    name: flux-system
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: shared
```

Now in your actual manifests, use variable syntax:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns-custom
  namespace: kube-system
data:
  custom.server: |
    peterbean.net {
      forward . ${DNS_SERVER_IP}
    }
    ${DOMAIN} {
      forward . ${DNS_SERVER_IP}
    }
```

When Flux applies this, it automatically substitutes:
- `${DNS_SERVER_IP}` → `192.168.1.55`
- `${DOMAIN}` → `dev.peterbean.net`

### Environment-Specific Values

The beauty is that **each environment has its own `shared` ConfigMap**:

**Development**:
```yaml
data:
  DNS_SERVER_IP: "192.168.1.55"
  DOMAIN: "dev.peterbean.net"
```

**Production**:
```yaml
data:
  DNS_SERVER_IP: "10.0.1.100"
  DOMAIN: "peterbean.net"
```

Same code, different values per environment. This achieves:
- **No hardcoded values** in Git (except in the ConfigMap itself)
- **Clear separation** of environment config
- **Single source of truth** for environment variables

### Using Secrets for Sensitive Data

For sensitive values, use Secrets instead of ConfigMaps:

```yaml
postBuild:
  substituteFrom:
    - kind: Secret
      name: cluster-secrets
```

The syntax is identical, but values come from a Secret. I use this for database passwords, API tokens, and other credentials.

**Important**: The Secret itself should be managed with Sealed Secrets or SOPS so you can commit encrypted versions to Git. Plain Secrets should never be committed.

## Helm Integration: Managing Complex Applications

Not everything in my infrastructure is raw YAML. I use Helm charts for complex applications like Gitea (Git server) and Longhorn (persistent storage). Flux's `HelmRelease` CRD makes this seamless.

### Basic HelmRelease

Here's my Gitea HelmRelease:

```yaml
# platform/base/gitea/helmrelease.yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: gitea
  namespace: gitea
spec:
  interval: 10m
  chart:
    spec:
      chart: gitea
      version: "10.x"
      sourceRef:
        kind: HelmRepository
        name: gitea
        namespace: flux-system
  values:
    ingress:
      enabled: true
      annotations:
        cert-manager.io/cluster-issuer: letsencrypt-route53
      hosts:
        - host: git.${DOMAIN}
          paths:
            - path: /
              pathType: Prefix
      tls:
        - secretName: gitea-tls
          hosts:
            - git.${DOMAIN}

    postgresql-ha:
      enabled: true
      postgresql:
        replicaCount: 3

    redis-cluster:
      enabled: true
      cluster:
        nodes: 6
```

**Key fields**:

**`chart.spec.version: "10.x"`**: Automatically pull the latest 10.x version. When Gitea releases 10.1.0, 10.2.0, Flux upgrades automatically. You can also pin to exact versions (`"10.1.0"`) for more control.

**`interval: 10m`**: Flux checks the Helm repository every 10 minutes for new chart versions.

**`values`**: Helm chart values, just like you'd pass to `helm install -f values.yaml`. Notice I'm using `${DOMAIN}` for environment-specific substitution.

### HelmRepository: Defining Chart Sources

HelmReleases pull charts from HelmRepositories:

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: gitea
  namespace: flux-system
spec:
  interval: 10m
  url: https://dl.gitea.com/charts/
```

Flux periodically checks this repository for new chart versions. When it finds a newer version matching your `version` constraint, it upgrades the release automatically.

### Combining HelmReleases with Kustomize Overlays

The real power comes from combining Helm with Kustomize. My base configuration works for all environments:

```yaml
# platform/base/gitea/helmrelease.yaml
values:
  ingress:
    hosts:
      - host: git.${DOMAIN}  # Variable!
```

Then I use Kustomize overlays for production-specific patches:

```yaml
# platform/overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base/gitea

patches:
  - patch: |-
      - op: replace
        path: /spec/values/postgresql-ha/postgresql/replicaCount
        value: 5  # More replicas in production
    target:
      kind: HelmRelease
      name: gitea
  - patch: |-
      - op: add
        path: /spec/values/resources
        value:
          limits:
            memory: 4Gi  # More memory in production
    target:
      kind: HelmRelease
      name: gitea
```

This gives me:
- **Shared base configuration** (Helm chart, basic values)
- **Environment-specific overrides** (replica counts, resource limits)
- **No duplication** (don't repeat the entire HelmRelease per environment)

### HelmRelease Upgrade Strategies

HelmReleases support sophisticated upgrade behaviors:

```yaml
spec:
  upgrade:
    remediation:
      retries: 3  # Retry failed upgrades 3 times
      remediateLastFailure: true  # Rollback on failure
  rollback:
    recreate: true  # Recreate resources on rollback
    timeout: 5m
  test:
    enable: true  # Run Helm tests after install/upgrade
```

This makes upgrades resilient:
- If an upgrade fails, Flux retries automatically
- If retries fail, Flux rolls back to the previous version
- Helm tests validate the deployment before marking it successful

### Monitoring HelmReleases

Check HelmRelease status:

```bash
kubectl get helmreleases -A
kubectl describe helmrelease gitea -n gitea
```

Flux updates the HelmRelease status with:
- Current chart version
- Upgrade status (ready, upgrading, failed)
- Error messages if reconciliation fails

## Automated Certificate Management with cert-manager

One of my favorite GitOps success stories is certificate management. Before, I manually created certificates and updated secrets. Now, cert-manager handles everything automatically, and it's all declared in Git.

### The Setup: Let's Encrypt with Route53

I use Let's Encrypt for free TLS certificates, with DNS-01 challenges via AWS Route53. The ClusterIssuer lives in my cert-manager ResourceSet:

```yaml
apiVersion: cert-manager.io/v1
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

**`dns01` challenges** are critical for wildcard certificates. cert-manager creates a TXT record in Route53, Let's Encrypt verifies it, and issues the certificate. All automatic.

The `aws-route53-secret` contains AWS credentials with Route53 permissions. I manage this Secret with Sealed Secrets (encrypted in Git), so even AWS credentials are version-controlled securely.

### Using the ClusterIssuer

Now when I add an ingress, I just annotate it:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gitea
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-route53
spec:
  tls:
    - hosts:
        - git.peterbean.net
      secretName: gitea-tls
  rules:
    - host: git.peterbean.net
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: gitea
                port:
                  number: 3000
```

cert-manager sees the annotation and:
1. Creates a `Certificate` resource automatically
2. Performs the DNS-01 challenge with Route53
3. Obtains a certificate from Let's Encrypt
4. Stores it in the `gitea-tls` Secret
5. Renews it automatically every 60 days

**Zero manual certificate operations.** All auditable in Git.

This has eliminated an entire class of operations work. I've never had a certificate expire unexpectedly, and renewal failures trigger Slack notifications (more on that next).

## Monitoring and Notifications: Knowing When Things Break

GitOps is amazing, but you need to know when reconciliation fails. Flux has a powerful notification system that integrates with Slack, Discord, Microsoft Teams, and more.

### Setting Up Notifications

First, create a Provider (Slack in my case):

```yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta1
kind: Provider
metadata:
  name: slack
  namespace: flux-system
spec:
  type: slack
  channel: "#flux-alerts"
  secretRef:
    name: slack-webhook-url
```

The `slack-webhook-url` Secret contains the Slack webhook URL:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: slack-webhook-url
  namespace: flux-system
stringData:
  address: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

Then create Alerts to send notifications:

```yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta1
kind: Alert
metadata:
  name: cluster-reconciliation
  namespace: flux-system
spec:
  providerRef:
    name: slack
  eventSeverity: error
  eventSources:
    - kind: Kustomization
      name: '*'
    - kind: HelmRelease
      name: '*'
```

**What this does**:
- Watches all Kustomizations and HelmReleases (note the `name: '*'` wildcard)
- Sends Slack notifications for `error` severity events
- Includes error messages in the notification

Now I get Slack alerts like:

```
⚠️ Flux Alert: Kustomization/cert-manager failed
Namespace: flux-system
Message: Health check failed for Deployment/cert-manager: deployment not ready
```

This immediately tells me what broke and where to look.

### Monitoring Flux with Prometheus and Grafana

Flux controllers expose Prometheus metrics that I scrape for monitoring:

- **`gotk_reconcile_duration_seconds`**: How long reconciliations take (detect slowness)
- **`gotk_reconcile_condition`**: Current status of each resource (ready, failed, reconciling)
- **`gotk_suspend_status`**: Whether reconciliation is suspended

I create Grafana dashboards with these metrics to visualize:
- Reconciliation success rate
- Reconciliation duration over time
- Which resources are failing
- Flux controller health

I also set up Prometheus alerts for:
- **Reconciliation stuck**: Resource hasn't reconciled successfully in 30 minutes
- **Reconciliation failure**: Resource failed 3 times in a row
- **Controller down**: Flux controller pod is not ready

This gives me both real-time notifications (Slack) and historical trends (Grafana).

## Operational Workflows: Making Changes with GitOps

Let me walk through a typical workflow for making infrastructure changes.

### Scenario: Upgrading Istio

**Step 1: Create a feature branch**

```bash
git checkout -b feat/upgrade-istio
```

**Step 2: Update the configuration**

Change the Istio version in the GitRepository reference:

```yaml
# clusters/development/KubeFlowDependencies.yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: kubeflow-manifests
spec:
  url: https://github.com/kubeflow/manifests.git
  ref:
    tag: v1.11.0  # Changed from v1.10.2
  interval: 10m
```

**Step 3: Commit and push**

```bash
git add clusters/development/KubeFlowDependencies.yaml
git commit -m "Upgrade Kubeflow manifests to v1.11.0"
git push origin feat/upgrade-istio
```

**Step 4: Test in development**

Point the dev FluxInstance to the feature branch:

```yaml
# clusters/fluxcd/development/FluxInstance.yaml
sync:
  ref: "refs/heads/feat/upgrade-istio"  # Changed from main
```

Flux immediately pulls the change and starts reconciling. Watch the rollout:

```bash
kubectl get kustomizations -n flux-system -w
flux logs --kind=Kustomization --name=istio
```

**Step 5: Verify health**

Flux's health checks ensure all resources are ready:

```bash
kubectl get pods -n istio-system
kubectl get helmreleases -n flux-system
kubectl describe kustomization istio -n flux-system
```

If anything fails, I see it immediately in Slack and in the Kustomization status.

**Step 6: Create pull request**

Once verified in dev, I create a PR to main. I include:
- What changed (Istio v1.10.2 → v1.11.0)
- Why (bug fixes, new features)
- Testing proof (Flux reconciliation logs, pod status)

**Step 7: Merge and deploy to production**

After code review and approval, I merge to main. Production FluxInstance automatically pulls from main, so the upgrade rolls out to production without manual intervention.

### The Workflow Benefits

This workflow gives me:
- **Change control**: All changes go through pull requests and code review
- **Auditability**: Full Git history of who changed what and when
- **Rollback capability**: If something breaks, `git revert` and Flux automatically rolls back
- **Testing**: Feature branches let me test in dev before production
- **No manual steps**: Zero SSH sessions, zero kubectl apply commands

## ARM64 Architecture: Tolerations at Scale

My cluster runs on ARM64 nodes, which requires adding tolerations to every workload. Initially, I added these manually to each deployment. Tedious and error-prone.

The solution: **patch Kustomizations** to inject tolerations into all deployed resources:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: cert-manager
  namespace: flux-system
spec:
  interval: 5m0s
  path: ./common/cert-manager/base
  prune: true
  sourceRef:
    kind: GitRepository
    name: kubeflow-manifests
  patches:
    - patch: |-
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: all
        spec:
          template:
            spec:
              nodeSelector:
                kubernetes.io/os: linux
              tolerations:
                - key: "CriticalAddonsOnly"
                  operator: "Exists"
                - key: "arch"
                  effect: "NoExecute"
                  value: "arm64"
                - key: "workload"
                  effect: "NoExecute"
                  value: "ml"
      target:
        kind: Deployment
```

This patches **all Deployments** in the Kustomization with:
- Node selector for Linux OS
- Tolerations for ARM64 architecture
- Toleration for ML workload nodes

Now every deployment automatically gets the necessary scheduling configuration. No manual editing required.

## What's Next

You now have the operational patterns for production FluxCD: Helm charts, variable substitution, automated certificates, monitoring, and daily workflows.

The final post in this series covers the hard-won lessons I learned running FluxCD in production: gotchas, best practices, what went wrong, and what I'd do differently.

- **[Part 6: Lessons Learned](../fluxcd-part6-lessons)** - Real-world gotchas, mistakes, and hard-won wisdom

---

**Questions about production FluxCD operations?** Find me on Twitter [@henrypham67](https://twitter.com/henrypham67). I'd love to help you level up your GitOps game!
