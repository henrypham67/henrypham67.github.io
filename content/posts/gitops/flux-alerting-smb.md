---
title: "FluxCD Alerting Strategy for Small-Medium Companies"
date: 2025-12-16T11:00:00+07:00
slug: fluxcd-alerting-smb
draft: true
---

## Company Profile

**Typical SMB Context**:

- 5-15 Kubernetes clusters (production, staging, dev)
- 1-3 platform/DevOps engineers
- 3-10 development teams
- 20-50 microservices
- Single cloud provider (AWS or GCP or Azure)
- Budget-conscious
- Already using Slack/Discord/Microsoft Teams

**Key Constraints**:

- No budget for PagerDuty ($30/user/month too expensive)
- Small platform team (can't maintain complex alerting infrastructure)
- Developers wear multiple hats
- Need simple, low-maintenance solution
- Must work with existing tools

## Strategy: Keep It Simple

### The Pragmatic Approach

**Don't overcomplicate it**. For SMBs, a simpler 3-tier model works better:

| Severity     | Destination              | Response          | Examples                                             |
| ------------ | ------------------------ | ----------------- | ---------------------------------------------------- |
| **Critical** | Slack + @channel mention | Immediate         | Flux down, production deploys failing, auth failures |
| **Warning**  | Slack (no mention)       | Next business day | Staging issues, slow reconciliation                  |
| **Info**     | Slack (success channel)  | No action         | Successful deploys, git commits detected             |

**Total Cost**: $0 (uses existing Slack/Teams)

### Architecture

```text
┌────────────────────────────────────┐
│   Flux Notification Controller     │
└────────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
Critical   Warning    Info
    │         │         │
    ▼         ▼         ▼
┌────────────────────────────────────┐
│     Slack (3 channels)             │
│  #flux-critical (@channel)         │
│  #flux-warnings                    │
│  #flux-deployments                 │
└────────────────────────────────────┘
         │
         ▼
   Mobile push notifications
   (via Slack mobile app)
```

**Why this works for SMBs**:

- Everyone already has Slack on their phone
- @channel mentions trigger mobile push (free PagerDuty alternative)
- Simple to set up and maintain
- No additional tools to learn
- Can upgrade to Alertmanager later if needed

## Implementation

### 1. Slack Setup (5 minutes)

Create 3 Slack channels:

- `#flux-critical` - For @channel alerts, production issues only
- `#flux-warnings` - For non-urgent issues, staging problems
- `#flux-deployments` - For success notifications, informational

**Channel Settings**:
```
#flux-critical:
  - Notification: All messages
  - Add: @platform-team, @dev-leads
  - Pin: Runbook links
  - Description: "PRODUCTION ONLY. @channel for immediate attention"

#flux-warnings:
  - Notification: Mentions only (to reduce noise)
  - Add: @platform-team
  - Description: "Non-urgent Flux issues, check during business hours"

#flux-deployments:
  - Notification: Nothing (optional check-in)
  - Add: @everyone
  - Description: "Successful deployments and info updates"
```

### 2. Notification Providers

#### Single Namespace Approach (Simpler)

For SMBs, put all providers in `flux-system` namespace (easier to manage):

```yaml
---
# Critical alerts with @channel mention
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: slack-critical
  namespace: flux-system
spec:
  type: slack
  channel: flux-critical
  username: FluxCD-Critical
  secretRef:
    name: slack-critical-webhook

---
# Warnings without mentions
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: slack-warnings
  namespace: flux-system
spec:
  type: slack
  channel: flux-warnings
  username: FluxCD-Warnings
  secretRef:
    name: slack-warnings-webhook

---
# Success/info notifications
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: slack-deployments
  namespace: flux-system
spec:
  type: slack
  channel: flux-deployments
  username: FluxCD-Deployments
  secretRef:
    name: slack-deployments-webhook

---
# Optional: Discord for dev team
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: discord-dev
  namespace: flux-system
spec:
  type: discord
  address: https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
  username: FluxCD
```

### 3. Alert Configurations

#### Critical Alerts (Production Only)

```yaml
---
# CRITICAL: Production Flux system failing
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: production-flux-critical
  namespace: flux-system
spec:
  summary: "<!channel> PRODUCTION: Flux system failing"
  eventSeverity: error
  eventSources:
    - kind: GitRepository
      name: 'flux-system'
    - kind: Kustomization
      name: 'flux-system'
  providerRef:
    name: slack-critical

---
# CRITICAL: Production app deployments failing
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: production-apps-critical
  namespace: flux-system
spec:
  summary: "<!channel> PRODUCTION: Application deployment failing"
  eventSeverity: error
  eventSources:
    - kind: Kustomization
      name: '*'
      namespace: production
    - kind: HelmRelease
      name: '*'
      namespace: production
  inclusionList:
    - ".*health check failed.*"
    - ".*ImagePullBackOff.*"
    - ".*CrashLoopBackOff.*"
    - ".*authentication.*failed.*"
  providerRef:
    name: slack-critical

---
# CRITICAL: Git authentication issues (affects all environments)
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: git-auth-critical
  namespace: flux-system
spec:
  summary: "<!channel> CRITICAL: Git authentication failing"
  eventSeverity: error
  eventSources:
    - kind: GitRepository
      name: '*'
  inclusionList:
    - ".*authentication.*"
    - ".*credentials.*invalid.*"
    - ".*401.*"
    - ".*403.*"
  providerRef:
    name: slack-critical
```

#### Warning Alerts (Staging, Development)

```yaml
---
# WARNING: Staging issues (no @channel)
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: staging-warnings
  namespace: flux-system
spec:
  summary: "Staging: Deployment issues detected"
  eventSeverity: error
  eventSources:
    - kind: Kustomization
      name: '*'
      namespace: staging
    - kind: HelmRelease
      name: '*'
      namespace: staging
  providerRef:
    name: slack-warnings

---
# WARNING: Development issues
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: dev-warnings
  namespace: flux-system
spec:
  summary: "Dev: Reconciliation issues"
  eventSeverity: error
  eventSources:
    - kind: Kustomization
      namespace: development
    - kind: HelmRelease
      namespace: development
  providerRef:
    name: slack-warnings

---
# WARNING: Slow reconciliation (any environment)
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: slow-reconciliation
  namespace: flux-system
spec:
  summary: "Warning: Slow Flux reconciliation detected"
  eventSeverity: warn
  eventSources:
    - kind: Kustomization
      name: '*'
  inclusionList:
    - ".*timeout.*"
    - ".*slow.*"
  providerRef:
    name: slack-warnings
```

#### Info Alerts (Successful Deployments)

```yaml
---
# INFO: Successful production deployments
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: production-deployments-success
  namespace: flux-system
spec:
  summary: "Production: Deployment successful"
  eventSeverity: info
  eventSources:
    - kind: Kustomization
      namespace: production
    - kind: HelmRelease
      namespace: production
  inclusionList:
    - ".*Reconciliation finished.*"
    - ".*Health check passed.*"
  exclusionList:
    - ".*failed.*"
    - ".*error.*"
  providerRef:
    name: slack-deployments

---
# INFO: Git commits detected (all environments)
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: git-updates
  namespace: flux-system
spec:
  summary: "Git update detected"
  eventSeverity: info
  eventSources:
    - kind: GitRepository
      name: '*'
  inclusionList:
    - ".*stored artifact.*"
    - ".*new commit.*"
  providerRef:
    name: slack-deployments
```

### 4. Secrets Setup

```yaml
---
apiVersion: v1
kind: Secret
metadata:
  name: slack-critical-webhook
  namespace: flux-system
type: Opaque
stringData:
  address: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX

---
apiVersion: v1
kind: Secret
metadata:
  name: slack-warnings-webhook
  namespace: flux-system
type: Opaque
stringData:
  address: https://hooks.slack.com/services/T00000000/B00000000/YYYYYYYYYYYYYYYYYYYY

---
apiVersion: v1
kind: Secret
metadata:
  name: slack-deployments-webhook
  namespace: flux-system
type: Opaque
stringData:
  address: https://hooks.slack.com/services/T00000000/B00000000/ZZZZZZZZZZZZZZZZZZZZ
```

**How to get Slack webhooks**:
1. Go to https://api.slack.com/apps
2. Create new app → From scratch
3. Add "Incoming Webhooks" feature
4. Activate and create webhook for each channel
5. Copy webhook URLs into secrets above

### 5. Optional: Lightweight Alertmanager (If You Grow)

When you reach ~15+ clusters or need more sophisticated routing, add Alertmanager:

```yaml
# Simple Alertmanager for SMB
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK'

    route:
      receiver: 'slack-default'
      group_by: ['alertname', 'namespace']
      group_wait: 10s
      group_interval: 5m
      repeat_interval: 4h

      routes:
        - match:
            severity: critical
            namespace: production
          receiver: 'slack-critical'
          group_wait: 5s
          repeat_interval: 30m

        - match:
            severity: error
          receiver: 'slack-warnings'

    receivers:
      - name: 'slack-critical'
        slack_configs:
          - channel: '#flux-critical'
            text: '<!channel> {{ .CommonAnnotations.summary }}'
            color: 'danger'

      - name: 'slack-warnings'
        slack_configs:
          - channel: '#flux-warnings'
            color: 'warning'

      - name: 'slack-default'
        slack_configs:
          - channel: '#flux-deployments'
            color: 'good'
```

## Alternative: Microsoft Teams Setup

If your company uses Teams instead of Slack:

```yaml
---
# Teams critical channel
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: teams-critical
  namespace: flux-system
spec:
  type: msteams
  address: https://outlook.office.com/webhook/YOUR_WEBHOOK_URL
  secretRef:
    name: teams-webhook

---
# Critical alert for Teams
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: production-critical-teams
  namespace: flux-system
spec:
  summary: "🚨 PRODUCTION: Flux deployment failing"
  eventSeverity: error
  eventSources:
    - kind: Kustomization
      namespace: production
  providerRef:
    name: teams-critical
```

**Teams Mentions**:
Teams doesn't support @channel in webhook messages, but you can:
1. Set channel to "Show banner for all messages"
2. Use emojis for visibility: 🚨 for critical, ⚠️ for warnings, ✅ for success
3. Add urgent keywords: "PRODUCTION", "CRITICAL", "URGENT"

## Alternative: Discord Setup

Popular for smaller dev teams:

```yaml
---
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: discord-critical
  namespace: flux-system
spec:
  type: discord
  address: https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN
  username: FluxCD
  channel: flux-critical

---
# Discord supports @everyone and @here
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: production-critical-discord
  namespace: flux-system
spec:
  summary: "@everyone PRODUCTION: Flux failing"
  eventSeverity: error
  eventSources:
    - kind: Kustomization
      namespace: production
  providerRef:
    name: discord-critical
```

## Budget-Friendly On-Call Alternative

Instead of PagerDuty ($30/user/month), use **free alternatives**:

### Option 1: Slack + Mobile App (Free)
- Configure `#flux-critical` to notify on all messages
- Enable Slack mobile push notifications
- Use @channel for urgent alerts
- **Cost**: $0 (included in free Slack)

### Option 2: Opsgenie Free Tier
- 5 users free
- Integrates with Slack
- Basic on-call scheduling
- **Cost**: $0 for ≤5 users

```yaml
---
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: opsgenie-free
  namespace: flux-system
spec:
  type: generic-hmac
  address: https://api.opsgenie.com/v2/alerts
  secretRef:
    name: opsgenie-api-key
```

### Option 3: Email + SMS Forwarding (Hacky but Free)
- Use email provider
- Set up email → SMS forwarding via carrier (e.g., phonenumber@txt.att.net)
- **Cost**: $0

```yaml
---
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: sms-critical
  namespace: flux-system
spec:
  type: generic
  address: https://your-smtp-relay/webhook
  secretRef:
    name: smtp-config
```

### Option 4: Grafana OnCall (Free Tier)
- Recently open-sourced by Grafana
- 5 users free on cloud, unlimited self-hosted
- Integrates with Alertmanager
- **Cost**: $0 (self-hosted) or free tier

## Simple Runbooks

### Critical: Flux System Down

**Detection**: Alert in #flux-critical with "@channel"

**Quick Fix** (5 minutes):
```bash
# 1. Check controllers
kubectl -n flux-system get pods

# 2. Restart if needed
flux suspend kustomization flux-system
flux resume kustomization flux-system

# 3. Force reconcile
flux reconcile kustomization flux-system --with-source
```

**If still failing**:

- Check controller logs: `kubectl -n flux-system logs -l app=kustomize-controller`
- Verify Git access: `flux reconcile source git flux-system`
- Check cluster resources: `kubectl -n flux-system top pods`

**When to escalate**: If not resolved in 15 minutes, call senior engineer

---

### Critical: Production Deploy Failing

**Detection**: Alert in #flux-critical

**Quick Investigation** (2 minutes):
```bash
# Check what's failing
flux get kustomizations -n production

# Get details
kubectl -n production describe kustomization <name>

# Check recent commits
flux reconcile source git <source> --with-source
```

**Common Fixes**:
1. **Invalid YAML**: Fix in Git and push
2. **Image pull error**: Check image tag exists
3. **Resource limit**: Adjust resource quotas
4. **Secret missing**: Verify secrets exist

---

### Warning: Staging Issues

**Detection**: Alert in #flux-warnings (no @channel)

**Response**: Check during business hours (not urgent)

**Investigation**:
```bash
flux get kustomizations -n staging
kubectl -n staging get events --sort-by='.lastTimestamp'
```

## Monitoring Setup (Optional but Recommended)

### Grafana Dashboard for Flux

Use the community dashboard: https://grafana.com/grafana/dashboards/16714

**Key Metrics**:

- Reconciliation success rate
- Time to reconcile
- Pending reconciliations
- Failed resources

```yaml
# Prometheus ServiceMonitor for Flux
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-system
  namespace: flux-system
spec:
  endpoints:
    - interval: 30s
      port: http-prom
  namespaceSelector:
    matchNames:
      - flux-system
  selector:
    matchLabels:
      app.kubernetes.io/part-of: flux
```

## Testing Your Setup

### 1. Test Critical Alerts

```bash
# Create a failing Kustomization in production
cat <<EOF | kubectl apply -f -
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: test-critical
  namespace: production
spec:
  interval: 1m
  path: ./non-existent
  prune: true
  sourceRef:
    kind: GitRepository
    name: flux-system
    namespace: flux-system
EOF

# Wait 2 minutes, check #flux-critical for @channel alert
# Clean up: kubectl -n production delete kustomization test-critical
```

### 2. Test Success Notifications

```bash
# Make a successful change
git commit --allow-empty -m "Test flux notification"
git push

# Check #flux-deployments for success message
```

### 3. Test Staging Warnings

```bash
# Create a warning in staging
cat <<EOF | kubectl apply -f -
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: test-warning
  namespace: staging
spec:
  interval: 1m
  path: ./invalid-path
  prune: true
  sourceRef:
    kind: GitRepository
    name: flux-system
    namespace: flux-system
EOF

# Check #flux-warnings (no @channel)
# Clean up: kubectl -n staging delete kustomization test-warning
```

## Scaling Up: When to Add Complexity

**Stay simple until you hit these thresholds**:

| Threshold           | Add This                                    |
| ------------------- | ------------------------------------------- |
| 15+ clusters        | Alertmanager for routing                    |
| 24/7 services       | Paid on-call tool (PagerDuty/Opsgenie)      |
| 10+ dev teams       | Multi-tenant alerts (per-team channels)     |
| Compliance required | Audit logs, alert retention                 |
| 100+ services       | Alert aggregation, ML-based noise reduction |

**Don't prematurely optimize**. Start with Slack, add complexity only when pain points emerge.

## Cost Comparison

### SMB Strategy (This Guide)
- **Slack webhooks**: $0 (included in free/paid Slack)
- **Flux notification controller**: $0 (included in Flux)
- **On-call (Slack mobile)**: $0
- **Total**: $0/month

### Enterprise Strategy (Previous Guide)
- **Alertmanager**: $0 (self-hosted, ~$10/month compute)
- **PagerDuty**: $300/month (10 users)
- **Slack**: $0 (included)
- **Total**: ~$310/month

**SMB Savings**: $300+/month = **$3,600+/year**

## Summary

For small-medium companies:

**Do**:

- ✅ Use existing tools (Slack/Teams/Discord)
- ✅ Keep it simple (3 tiers: Critical, Warning, Info)
- ✅ Use @channel mentions for critical production alerts
- ✅ Mobile push via Slack app (free on-call alternative)
- ✅ Start minimal, add complexity as you grow

**Don't**:

- ❌ Pay for PagerDuty if <10 clusters
- ❌ Set up complex Alertmanager initially
- ❌ Alert on everything (causes fatigue)
- ❌ Create per-team channels until >10 teams
- ❌ Over-engineer for future scale

**Key Principle**: The best alerting system is the one your team actually uses. Start simple, iterate based on pain points.

## Quick Start Checklist

- [ ] Create 3 Slack channels (#flux-critical, #flux-warnings, #flux-deployments)
- [ ] Generate Slack webhooks for each channel
- [ ] Apply Provider configs from this guide
- [ ] Apply Alert configs (critical, warning, info)
- [ ] Test critical alert (@channel should trigger)
- [ ] Test warning alert (no @channel)
- [ ] Document runbook URLs in #flux-critical channel description
- [ ] Set up Slack mobile app notifications for #flux-critical
- [ ] Schedule monthly review of alert noise

**Time to implement**: ~1 hour

**Maintenance**: ~1 hour/month (review and tune)

That's it! You now have production-ready Flux alerting for $0/month.
