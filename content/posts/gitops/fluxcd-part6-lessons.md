---
title: "FluxCD in Production: Lessons Learned and Hard-Won Wisdom - Part 6 of 6"
date: 2025-12-20T11:15:00+07:00
draft: true
tags: ["gitops", "fluxcd", "kubernetes", "devops", "infrastructure-as-code"]
categories: ["DevOps", "Kubernetes"]
description: "Real-world lessons from running FluxCD in production. Covers gotchas, mistakes, best practices, results, and what I'd do differently next time."
series: ["FluxCD in Production"]
---

# FluxCD in Production: Lessons Learned and Hard-Won Wisdom

*This is Part 6 of a 6-part series on implementing production-ready GitOps with FluxCD. [See the full series](../fluxcd).*

In [Part 5](../fluxcd-part5-production), I covered production operations including Helm integration, certificates, and monitoring. Now for the most valuable part: the lessons I learned the hard way after months of running FluxCD in production.

These aren't theoretical best practices from documentation. These are battle scars, debugging sessions, and "oh no" moments that taught me how to do GitOps right.

## The Lessons

### 1. Start Small, Grow Incrementally

**The mistake**: I initially tried to migrate everything to GitOps at once—cert-manager, Istio, Kubeflow, platform services—all simultaneously.

**What happened**: Overwhelming complexity. When things broke (and they did), I couldn't tell if the problem was with FluxCD configuration, ResourceSet dependencies, health checks, or the actual application. Debugging was a nightmare.

**The lesson**: Start with a single, simple component. I wish I'd started with CoreDNS—a single ConfigMap, minimal dependencies, easy to verify. Get that working, understand the patterns, THEN expand.

**My recommendation**: Pick your first migration candidate with these criteria:
- Single component (not a complex stack)
- Few dependencies
- Easy to verify (kubectl get works, no deep health checks needed)
- Non-critical (if it breaks, production doesn't go down)

Once you've successfully GitOps'd one component and understand the Flux patterns, migrate the next. Rinse and repeat.

### 2. Health Checks Are Non-Negotiable

**The mistake**: Early on, I created Kustomizations without health checks, thinking "it's fine, Flux will apply the manifests."

**What happened**: Race conditions everywhere. Istio control plane tried to deploy before CRDs were registered. ClusterIssuers tried to create before cert-manager was ready. Dependency chains didn't work because Flux marked resources "ready" before they actually were.

**The lesson**: **Every Kustomization must have health checks**. Not optional. Not "I'll add them later." From day one.

Without health checks:
- Dependencies don't work reliably
- Resources fail with cryptic errors (CRD not found, namespace doesn't exist)
- Reconciliation appears successful when it's actually broken
- You'll spend hours debugging timing issues

With health checks:
- Flux waits for resources to actually be ready
- Dependencies work as expected
- Failures are obvious and immediate
- Reconciliation status accurately reflects cluster state

**My rule**: If it's a Kustomization, it has health checks. No exceptions.

### 3. ResourceSets vs. Kustomizations: Know When to Use Each

**The mistake**: I spent two full days trying to make plain Kustomizations work for cert-manager before discovering ResourceSets existed.

**The problem**: Kustomizations can't bundle raw resources (ClusterIssuers, Namespaces) with other Kustomizations and establish dependencies. This limitation isn't clearly documented.

**The lesson**:
- **Use plain Kustomizations** for deploying a single Helm chart or Kustomize directory
- **Use ResourceSets** when bundling Kustomizations with raw Kubernetes resources (CRDs, namespaces, ClusterIssuers)

Don't waste time fighting Kustomization limitations. If you're mixing resource types and need dependencies, use ResourceSets from the start.

### 4. The Reconciliation Interval Is a Trade-Off

**The decision**: How often should Flux check Git for changes?

I use `interval: 5m0s` for most resources. This means Flux checks Git every 5 minutes.

**The trade-offs**:
- **Shorter intervals** (1m): Faster deployments, but higher API server load and more Git fetches
- **Longer intervals** (15m): Lower load, but slower reaction to changes

**The lesson**: 5 minutes is a good default for production. It's fast enough that changes roll out quickly, but not so aggressive that it hammers your API server.

For development, you can force immediate reconciliation without waiting:

```bash
flux reconcile kustomization <name> --with-source
```

Or I have a Makefile target:

```bash
make reconcile  # Triggers immediate reconciliation
```

This annotates resources to skip the interval and reconcile now—perfect for testing.

### 5. Flux Bootstrap vs. Flux Operator: Choose Wisely

**I tried both approaches**. Here's when each makes sense:

**Use `flux bootstrap` if**:
- You're just getting started and want simplicity
- Single cluster
- Okay with CLI-driven Flux upgrades
- Don't need per-cluster Flux customization

**Use Flux Operator if**:
- Managing multiple clusters (dev, staging, prod)
- Want Flux to manage its own upgrades via GitOps
- Need per-cluster Flux configuration (different components, tolerations, patches)
- Want everything version-controlled and declarative

For production multi-cluster setups, the Flux Operator wins hands down. The FluxInstance resource makes Flux installations reproducible and auditable.

### 6. Git Repository Size Matters

**The problem**: Flux clones the entire Git repository. My repository initially included large Kubeflow manifests (hundreds of MBs), which made clones slow and consumed disk space on Flux pods.

**The solution**: Separate large upstream manifests into dedicated GitRepository resources:

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: kubeflow-manifests
spec:
  url: https://github.com/kubeflow/manifests.git
  ref:
    tag: v1.10.0
```

Now Flux pulls Kubeflow manifests directly from the upstream repo rather than vendoring them in my repo. My GitOps repo stays small and fast.

**The lesson**: Don't vendor large external manifests. Use GitRepository resources to reference upstream repos directly.

### 7. Secrets Management Requires Planning

**The challenge**: GitOps and secrets are a tricky combination. You can't commit plain secrets to Git.

**My solution**: Sealed Secrets. I encrypt secrets with `kubeseal`, commit the encrypted SealedSecret to Git, and the SealedSecret controller decrypts them in-cluster.

Example:

```bash
# Create a secret
kubectl create secret generic my-secret --from-literal=password=foo123 --dry-run=client -o yaml \
  | kubeseal -o yaml > my-secret-sealed.yaml

# Commit the sealed secret
git add my-secret-sealed.yaml
git commit -m "Add my-secret"
```

The SealedSecret can only be decrypted in the target cluster (it's encrypted with the cluster's public key). Safe to commit to Git, even public repos.

**Alternatives**: SOPS (more flexible, supports multiple backends), External Secrets Operator (pulls from Vault, AWS Secrets Manager).

**The lesson**: Pick a secrets solution EARLY. Retrofitting secrets management after you've already committed plain secrets is painful and risky.

### 8. Prune Carefully

**The `prune: true` flag** tells Flux to delete resources that are removed from Git. This is essential for true GitOps—your cluster should match Git exactly.

**The danger**: I once accidentally deleted a namespace because I moved a file in Git without updating the Kustomization path. Flux saw the namespace missing from Git and deleted it. Data loss.

**The lesson**:
- Always double-check `prune` behavior, especially in production
- Test prune changes in dev first
- Use `--dry-run` when making structural changes:

```bash
flux diff kustomization <name> --path=./clusters/production
```

This shows what would be deleted WITHOUT actually deleting it.

- For critical resources, consider `prune: false` and manual cleanup

Prune is powerful, but be careful. Git is the source of truth, and Flux will ruthlessly enforce it.

### 9. Namespace Creation Is a Gotcha

**The problem**: If your Kustomization has `targetNamespace: foo`, Flux assumes the namespace exists. If it doesn't, reconciliation fails with "namespace 'foo' not found."

**The solution**: Create namespaces in dedicated Kustomizations that other resources depend on:

```yaml
# Step 1: Create namespace
- apiVersion: kustomize.toolkit.fluxcd.io/v1
  kind: Kustomization
  metadata:
    name: istio-ns
  spec:
    path: ./common/istio/istio-namespace/base
    healthChecks:
      - apiVersion: v1
        kind: Namespace
        name: istio-system

# Step 2: Deploy into namespace (depends on step 1)
- apiVersion: kustomize.toolkit.fluxcd.io/v1
  kind: Kustomization
  metadata:
    name: istio-install
  spec:
    targetNamespace: istio-system
    dependsOn:
      - name: istio-ns  # Waits for namespace to exist
```

The health check on the Namespace ensures it's active before dependent resources try to use it.

**The lesson**: Treat namespaces as first-class resources with their own Kustomizations and dependencies.

### 10. Monitor Flux Itself

**The realization**: Flux is critical infrastructure. If Flux breaks, your GitOps automation stops.

**What I monitor**:
- **Flux controller pods**: Are source-controller, kustomize-controller, helm-controller running?
- **Reconciliation metrics**: Success rate, duration, failures (via Prometheus)
- **Git sync status**: Is Flux successfully fetching from Git?
- **Resource status**: Are Kustomizations/HelmReleases healthy?

**Alerts I set**:
- Flux controller pod not ready for >5 minutes
- Kustomization failed reconciliation 3 times in a row
- HelmRelease stuck in "upgrading" for >30 minutes
- GitRepository fetch failed (auth issues, repo unreachable)

I also send Flux events to Slack (covered in Part 5) so I know immediately when things break.

**The lesson**: Treat Flux like production infrastructure. Monitor it, alert on failures, and test disaster recovery (can you rebuild Flux if it's deleted?).

## The Results: What GitOps Has Given Me

After all the pain, learning, and debugging, was it worth it? **Absolutely.**

### Auditability

Every infrastructure change is in Git with a commit message, author, timestamp, and code review. When something breaks at 3 AM, I can:

```bash
git log --oneline -- clusters/production/CertManager.yaml
```

And immediately see what changed and when. No more "who modified this?" mysteries.

### Reproducibility

I can recreate my entire cluster from Git. If I lost the cluster tomorrow:

1. Spin up new Kubernetes cluster
2. Install Flux Operator
3. Apply FluxInstance YAML
4. Flux rebuilds everything from Git

This isn't theoretical—I've actually tested it in dev. 20 minutes from empty cluster to full Kubeflow platform, all automated.

### Collaboration

Infrastructure changes go through pull requests. Multiple people can propose changes, reviewers catch errors, and nothing reaches production without approval.

This shifted infrastructure from "scary changes I make alone" to "collaborative code with review and testing."

### Testing

Feature branches let me test infrastructure changes in dev before production, just like application code. No more "hope this works in prod" anxiety.

### Automation

No more manual kubectl commands. No more SSH sessions. No more "works on my machine" because **my machine IS the Git repository**.

The cluster state is always converging toward Git. If someone manually changes something, Flux reverts it. Git is the law.

### Sleep

I actually sleep better knowing that:
- If something breaks, I can `git revert` instead of panic-debugging
- All changes are audited and reviewable
- The cluster self-heals toward the Git state
- Rollbacks are as easy as changing a Git ref

The peace of mind alone was worth the migration effort.

## The ROI

**Time investment**: ~3 weeks to migrate all infrastructure to GitOps and learn the patterns.

**Time saved**: Countless hours of manual kubectl operations, SSH debugging, and "what's deployed?" questions.

**Reduced incidents**: Environment drift issues disappeared. "It works in dev but not prod" became rare.

**Faster deployments**: Merging to Git is faster and safer than manual kubectl commands.

**Better collaboration**: Pull requests made infrastructure changes reviewable and collaborative.

The ROI was enormous. I spend far less time firefighting and far more time building new capabilities.

## Next Steps and Future Improvements

My GitOps journey isn't finished. Here are areas I'm exploring:

### Image Automation

Flux's image-automation-controller can automatically update image tags in Git when new images are published. This would close the loop for application deployments—merge code, CI builds image, Flux updates Git, Flux deploys to cluster. Fully automated.

### Progressive Delivery with Flagger

Flagger (a Flux sub-project) enables canary deployments and A/B testing. For critical services, I want automated rollbacks if metrics degrade (latency spikes, error rate increases).

This would make deployments even safer—deploy to 10% of traffic, measure success, automatically promote or rollback.

### Multi-Cluster Management

I currently manage dev and prod separately with different FluxInstance configs. Flux's multi-cluster features could help manage shared configuration across clusters while allowing environment-specific overrides.

### Policy Enforcement

Integrating OPA (Open Policy Admission) or Kyverno with GitOps would enforce security policies on all deployments automatically. Examples:
- No containers running as root
- All ingresses must have TLS
- Resource limits required on all pods

Policies would be version-controlled and enforced declaratively.

### Disaster Recovery Testing

I want to regularly destroy and rebuild my dev cluster from Git to ensure my GitOps setup is truly reproducible. "Chaos engineering for infrastructure."

This would validate:
- Can I rebuild from scratch?
- Are there hidden manual steps?
- Are all secrets properly managed?
- Is documentation accurate?

## Final Thoughts: GitOps Is Worth the Journey

Migrating to GitOps with FluxCD was one of the best technical decisions I've made. It transformed infrastructure management from imperative chaos to declarative order.

**The learning curve is real**:
- Understanding Flux architecture
- Mastering ResourceSets and dependencies
- Implementing health checks everywhere
- Setting up secrets management
- Learning the gotchas (prune, namespaces, reconciliation intervals)

It all takes time. Budget 2-4 weeks for the initial migration and learning.

**But the investment pays off exponentially**:
- Auditability and compliance
- Reproducibility and disaster recovery
- Collaboration and code review
- Automation and self-healing
- Peace of mind and better sleep

If you're managing Kubernetes infrastructure with kubectl scripts, manual changes, and "hope this works" deployments, I encourage you to explore GitOps.

**Start small**. Pick one simple component. Migrate it to FluxCD. Learn the patterns. Get comfortable with Kustomizations, health checks, and reconciliation. Then expand incrementally.

Your future self (and your on-call teammates) will thank you.

## The Complete Series

If you've made it this far, thank you for following along! Here's the complete series:

- **[Part 1: Why GitOps?](../fluxcd-part1-why-gitops)** - The philosophy and choosing FluxCD vs ArgoCD
- **[Part 2: Repository Architecture](../fluxcd-part2-architecture)** - Structuring a multi-cluster GitOps repo
- **[Part 3: Bootstrapping](../fluxcd-part3-bootstrapping)** - FluxInstance and declarative installation
- **[Part 4: ResourceSets](../fluxcd-part4-resourcesets)** - Managing dependencies and deployment order
- **[Part 5: Production Operations](../fluxcd-part5-production)** - Helm, secrets, certificates, monitoring
- **[Part 6: Lessons Learned](../fluxcd-part6-lessons)** - This post!

---

**Resources:**

- [FluxCD Documentation](https://fluxcd.io/docs/)
- [Flux Operator GitHub](https://github.com/controlplaneio-fluxcd/flux-operator)
- [GitOps Principles](https://opengitops.dev/)
- [My GitOps Repository](https://github.com/peterbean/fluxcd) - See the real implementation

**Questions or want to share your GitOps story?** Find me on Twitter [@henrypham67](https://twitter.com/henrypham67). I'd love to hear how you're implementing GitOps!
