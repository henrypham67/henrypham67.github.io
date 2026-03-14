---
title: 'Managing PostgreSQL in Kubernetes with CloudNativePG'
date: 2025-12-27T15:25:34+07:00
draft: false
---

<!-- ## Introduction

Managing PostgreSQL databases in Kubernetes presents unique challenges. While Kubernetes excels at orchestrating stateless applications, stateful workloads like databases require specialized operators to handle backups, recovery, high availability, and lifecycle management properly.

CloudNativePG is a lightweight Kubernetes operator that brings native PostgreSQL management to your cluster. It allows you to define and manage PostgreSQL databases using Kubernetes resources, treating your database infrastructure as declarative code. Instead of manually configuring backups, setting up replication, or managing failover, you define these requirements in YAML manifests and let the operator handle the complexity.

In this post, I'll walk through how I configured CloudNativePG for a production Gitea instance, focusing on optimal settings for WAL archiving, backup strategies, and cost-effective configurations for both production and development environments. -->

## Why use a Postgres operator?

<!-- Traditional database management in Kubernetes involves creating StatefulSets, manually configuring backup scripts, setting up monitoring, and writing custom logic for failover scenarios. This approach is error-prone and requires significant maintenance overhead. -->

A Postgres operator solves these problems by providing:

### Declarative database management

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: my-database
spec:
  instances: 3        # Number of PostgreSQL instances
  storage:
    size: 10Gi        # Storage per instance
```

**Backups**: beside on-demand `Backup` and `ScheduledBackup` (which set me free from writing scripts). The operator handles WAL archiving to S3-compatible storage for point-in-time recovery.

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: ScheduledBackup
metadata:
  name: daily-backup
spec:
  schedule: "0 0 2 * * *"    # Daily at 2 AM
  cluster:
    name: my-database
```

**High availability**: Automatic failover, replication slot management, and synchronous replication configuration without manual intervention.

```yaml
spec:
  instances: 3
  replicationSlots:
    highAvailability:
      enabled: true      # Automatic replication slot management
  minSyncReplicas: 1     # Synchronous replication to 1 standby
```

**Lifecycle management**: Handle PostgreSQL upgrades, scaling, and configuration changes through standard Kubernetes workflows.

```yaml
spec:
  instances: 5                  # Scale from 3 to 5 instances
  imageName: ghcr.io/cloudnative-pg/postgresql:16.1  # Upgrade PostgreSQL version
```

## Choosing CloudNativePG

After evaluating several PostgreSQL operators for Kubernetes, I chose CloudNativePG for several reasons:

**Lightweight architecture**: CloudNativePG has a minimal footprint compared to alternatives like Zalando's Postgres Operator or Crunchy Data. It follows the Kubernetes operator pattern closely without introducing unnecessary abstractions.

**Native Kubernetes integration**: Uses standard Kubernetes concepts and integrates cleanly with existing tooling. The CRDs are intuitive and well-documented.

**Active development**: The project is actively maintained by the Cloud Native Computing Foundation with regular releases and a responsive community.

**Integrated backup support**: CloudNativePG provides native support for the Barman plugin, enabling PostgreSQL backups to S3-compatible storage with WAL archiving for point-in-time recovery.

## Understanding WAL archiving and backups

Before diving into configuration, it's important to understand two key concepts:

**Write-Ahead Logging (WAL)**: PostgreSQL writes all changes to WAL files before modifying the actual data files. Archiving these WAL files enables point-in-time recovery (PITR), allowing you to restore your database to any moment within your retention window.

**Base backups**: Full backups of your database at a specific point in time. Combined with archived WAL files, base backups enable complete disaster recovery.

CloudNativePG uses the Barman plugin (configured in the `plugins` section of your Cluster spec) to handle both WAL archiving and scheduled base backups to S3-compatible storage. The key configuration parameters are:

- **Compression type**: Balances CPU usage against storage costs
- **Parallel jobs**: Controls how many files are archived or restored simultaneously
- **Retention policy**: Determines how long backups and WAL files are kept

## Optimizing WAL archiving settings

### Compression strategies

Choosing the right compression algorithm significantly impacts both performance and cost. Here's how the options compare:

**gzip** - The balanced choice
- Compression ratio: 60-70%
- CPU usage: Moderate to high
- Speed: Moderate
- Best for: Production environments where storage cost matters and CPU resources are adequate

**snappy** - The performance option
- Compression ratio: 40-50%
- CPU usage: Very low
- Speed: Very fast
- Best for: High-write workloads where CPU efficiency is critical, or development environments

**bzip2** - The maximum compression option
- Compression ratio: 70-80%
- CPU usage: Very high
- Speed: Slow
- Best for: Cold archives or environments with extremely expensive storage

**none** - The zero-overhead option
- Compression ratio: 0%
- CPU usage: None
- Speed: Instant
- Best for: Development environments with negligible data or abundant cheap storage

For my Gitea production instance, I chose **gzip** for its balanced compression ratio and broad compatibility. For development environments, **snappy** provides better performance with acceptable compression.

### Configuring parallel archiving

The `maxParallel` setting controls how many WAL files can be archived or restored simultaneously. Finding the optimal value requires understanding your workload characteristics.

**Factors to consider:**

1. **CPU cores**: The primary constraint. A reasonable starting point is `maxParallel = min(CPU_cores / 2, 8)`
2. **Network bandwidth**: Higher parallelism can saturate your network connection to S3
3. **Write rate**: High-write databases generate WAL files faster and may need more parallel workers
4. **S3 rate limits**: AWS S3 supports 5,500 PUT requests per second per prefix, which is unlikely to be your bottleneck

### Finding the optimal value

Monitor these metrics to tune `maxParallel`:

**Check WAL archiving lag:**
```bash
kubectl exec -n gitea <postgres-pod> -- \
  psql -U postgres -c "SELECT * FROM pg_stat_archiver;"
```

**Monitor WAL file accumulation:**
```bash
kubectl exec -n gitea <postgres-pod> -- \
  ls -lh /var/lib/postgresql/data/pg_wal/ | wc -l
```

**Track CPU usage during archiving:**
```bash
kubectl top pods -n gitea
```

**Testing methodology:**

1. Start with `maxParallel: 2`
2. Monitor archiver lag and CPU usage under normal load
3. Increase if CPU usage is below 50% and WAL files are accumulating
4. Decrease if CPU usage exceeds 80% or you see no throughput improvement

**Recommended values by workload:**

| Workload type                | maxParallel | Compression    | Rationale                |
| ---------------------------- | ----------- | -------------- | ------------------------ |
| Low-write                    | 2           | gzip           | Minimal archiving needed |
| Medium-write (typical Gitea) | 4           | gzip or snappy | Balanced performance     |
| High-write                   | 6-8         | snappy         | Maximize throughput      |
| Archive/backup only          | 2           | bzip2          | Optimize storage cost    |

For a typical production Gitea instance, `maxParallel: 4` with gzip compression provides the right balance.

**Plugin configuration**: The Barman backup functionality requires configuring the `barman-cloud.cloudnative-pg.io` plugin in your Cluster specification. The production example below shows this in the `plugins` section.

## Production configuration

Here's my production configuration for a high-availability Gitea PostgreSQL cluster:

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: gitea-pg-ha
  namespace: gitea
spec:
  instances: 3
  imageName: ghcr.io/cloudnative-pg/postgresql:18.1-minimal-trixie

  storage:
    size: 10Gi

  plugins:
    - name: barman-cloud.cloudnative-pg.io
      isWALArchiver: true
      parameters:
        barmanObjectName: gitea-s3-pg-store

  bootstrap:
    initdb:
      database: gitea
      owner: gitea
      secret:
        name: gitea-db-secret

  superuserSecret:
    name: pg-superuser-secret

  replicationSlots:
    highAvailability:
      enabled: true

  minSyncReplicas: 1
  maxSyncReplicas: 1

  backup:
    target: "prefer-standby"
    retentionPolicy: "30d"
    barmanObjectStore:
      destinationPath: s3://prod-barman-postgres-backup-731833471586/
      endpointURL: https://s3.ap-southeast-1.amazonaws.com
      s3Credentials:
        accessKeyId:
          name: barman-s3-secret
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: barman-s3-secret
          key: ACCESS_SECRET_KEY
      wal:
        compression: gzip
        maxParallel: 4
      data:
        compression: gzip
        jobs: 2
        immediateCheckpoint: true
```

**Key configuration choices:**

- **3 instances**: Provides high availability with one primary and two standby replicas
- **Synchronous replication**: `minSyncReplicas: 1` ensures writes are confirmed by at least one standby before committing
- **30-day retention**: Balances compliance requirements with storage costs
- **Backup target**: `prefer-standby` reduces load on the primary instance
- **gzip compression**: Achieves 60-70% compression with moderate CPU usage
- **Immediate checkpoint**: Ensures consistent backup starting points

### Scheduled backups

Create a daily backup schedule with this resource:

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: ScheduledBackup
metadata:
  name: gitea-pg-daily
  namespace: gitea
spec:
  schedule: "0 0 19 * * *"  # Daily at 7 PM
  backupOwnerReference: self
  method: plugin
  pluginConfiguration:
    name: barman-cloud.cloudnative-pg.io
  cluster:
    name: gitea-pg-ha
```

## Development environment configuration

Development environments have different requirements than production. Lower write volumes, relaxed recovery time objectives, and cost sensitivity justify different configuration choices.

**Recommended changes for development:**

1. **Reduce instances**: 2 replicas instead of 3
2. **Faster compression**: Use snappy instead of gzip for lower CPU usage
3. **Lower parallelism**: `maxParallel: 1` is sufficient for low-write workloads
4. **Less frequent backups**: Weekly instead of daily
5. **Shorter retention**: 7 days instead of 30

Here's the development configuration:

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: gitea-pg-ha
  namespace: gitea
spec:
  instances: 2
  imageName: ghcr.io/cloudnative-pg/postgresql:18.1-minimal-trixie

  storage:
    size: 5Gi

  plugins:
    - name: barman-cloud.cloudnative-pg.io
      isWALArchiver: true
      parameters:
        barmanObjectName: gitea-s3-pg-store

  backup:
    target: "prefer-standby"
    retentionPolicy: "7d"
    barmanObjectStore:
      destinationPath: s3://dev-barman-postgres-backup-731833471586/
      endpointURL: https://s3.ap-southeast-1.amazonaws.com
      s3Credentials:
        accessKeyId:
          name: barman-s3-secret
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: barman-s3-secret
          key: ACCESS_SECRET_KEY
      wal:
        compression: snappy
        maxParallel: 1
      data:
        compression: snappy
        jobs: 1

---
apiVersion: postgresql.cnpg.io/v1
kind: ScheduledBackup
metadata:
  name: gitea-pg-weekly
  namespace: gitea
spec:
  schedule: "0 0 19 * * 0"  # Weekly on Sundays
  backupOwnerReference: self
  method: plugin
  pluginConfiguration:
    name: barman-cloud.cloudnative-pg.io
  cluster:
    name: gitea-pg-ha
```

**Configuration comparison:**

| Setting          | Production | Development | Rationale                           |
| ---------------- | ---------- | ----------- | ----------------------------------- |
| Instances        | 3          | 2           | Dev doesn't need maximum HA         |
| Storage          | 10Gi       | 5Gi         | Smaller dev datasets                |
| Compression      | gzip       | snappy      | Dev prioritizes speed over storage  |
| maxParallel      | 4          | 1           | Lower write volume                  |
| Backup frequency | Daily      | Weekly      | Less critical recovery requirements |
| Retention        | 30d        | 7d          | Shorter compliance window           |
| jobs             | 2          | 1           | Simpler backup process              |

## Cost optimization strategies

For a 10GB production database with the configuration above, here's the cost breakdown:

**Without optimization:**

- Daily backup size: 10GB compressed to ~5GB with gzip
- WAL accumulation: ~500MB per day
- Monthly storage: ~150GB base backups + 15GB WAL = 165GB
- S3 Standard cost: 165GB × $0.025 = **$4.13/month**

**With S3 lifecycle policies:**

Configure S3 lifecycle rules to automatically transition older backups to cheaper storage tiers:

```yaml
# Days 0-7: S3 Standard (hot backups)
# Days 8-30: S3 Infrequent Access
# Days 31-90: S3 Glacier Instant Retrieval
```

**Optimized cost:**

- Days 0-7: 35GB × $0.025 = $0.88
- Days 8-30: 115GB × $0.0138 = $1.59
- Days 31-90: 15GB × $0.005 = $0.08
- **Total: ~$2.55/month (38% savings)**

**Development environment cost:**

With weekly backups, 7-day retention, and snappy compression:

- 4 weekly backups of 5GB each = 20GB total
- Monthly cost: 20GB × $0.025 = **$0.50/month**
- **Savings: 80% compared to production settings**

**Cost comparison summary:**

| Environment            | Backups/month | Storage | Monthly cost | Savings  |
| ---------------------- | ------------- | ------- | ------------ | -------- |
| Production (optimized) | 30 daily      | 165GB   | $2.55        | Baseline |
| Development            | 4 weekly      | 20GB    | $0.50        | 80%      |
| Dev (minimal)          | 2 monthly     | 10GB    | $0.25        | 90%      |

## Recovery and disaster scenarios

CloudNativePG recovery requires creating a new cluster and pointing it to existing backups. This is fundamentally different from in-place restoration.

**Point-in-time recovery example:**

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: my-cluster-recovered
spec:
  ...

  externalClusters:
    - name: gitea-pg-ha
      plugin:
        name: barman-cloud.cloudnative-pg.io
        parameters:
          barmanObjectName: gitea-s3-pg-store
          serverName: gitea-pg-ha
          
      barmanObjectStore:
        destinationPath: s3://prod-barman-postgres-backup-731833471586/
        endpointURL: https://s3.ap-southeast-1.amazonaws.com
        s3Credentials:
          accessKeyId:
            name: barman-s3-secret
            key: ACCESS_KEY_ID
          secretAccessKey:
            name: barman-s3-secret
            key: ACCESS_SECRET_KEY
        wal:
          compression: gzip
          maxParallel: 4
```

After recovery completes, update your application's database connection to point to the new cluster and delete the old one.

## Key takeaways

1. **Choose compression based on your priorities**: gzip for storage savings, snappy for performance, bzip2 for cold archives
2. **Tune maxParallel based on monitoring**: Start with 2-4 and adjust based on CPU usage and WAL accumulation
3. **Differentiate production and development**: Use aggressive cost optimization for dev environments
4. **Implement S3 lifecycle policies**: Automatically transition older backups to cheaper storage tiers
5. **Monitor archiving lag**: Use `pg_stat_archiver` to ensure WAL files aren't accumulating
6. **Plan for recovery**: Test your recovery process before you need it in production

## Next steps

To implement these configurations in your environment:

1. Update your cluster manifest with appropriate compression and `maxParallel` settings
2. Create separate configurations for production and development environments
3. Configure S3 lifecycle policies in your AWS account to optimize costs
4. Set up monitoring for WAL archiving metrics using `pg_stat_archiver`
5. Test recovery procedures by creating a test cluster from your latest backup

CloudNativePG provides a robust, Kubernetes-native way to manage PostgreSQL databases. By tuning WAL archiving settings and implementing environment-specific configurations, you can achieve both high availability and cost efficiency.
