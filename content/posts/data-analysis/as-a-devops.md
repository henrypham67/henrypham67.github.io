---
title: "Data analyst with Python - as a DevOps"
date: 2026-03-28T00:00:00+07:00
draft: true
tags: ["data-analysis", "devops", "sre", "python"]
categories: ["Data Analysis"]
---

This post maps every course in [DataCamp's Data Analyst with Python](https://www.datacamp.com/tracks/data-analyst-with-python) career track to concrete DevOps, Platform Engineering, and SRE use cases. The track has 9 courses over 36 hours — and every single one is directly applicable to infrastructure work.

## 1. Introduction to Python

Lists, dictionaries, functions, loops — the building blocks.

- **Incident response automation**: parse JSON payloads from PagerDuty API webhooks to extract incident IDs, affected services, and triggering users. Use dictionaries to map service names to specific runbook URLs
- **Infrastructure security auditing**: loop through Kubernetes deployment manifests (YAML) to check if security contexts like `runAsNonRoot` are set, outputting a list of non-compliant namespaces

## 2. Intermediate Python (Matplotlib, pandas basics)

Basic DataFrames, plotting, logic flow.

- **Capacity planning**: query Prometheus via its HTTP API for 30 days of CPU utilization, load into a pandas DataFrame, and use Matplotlib to plot trendlines predicting when resource limits will be hit
- **Cost spike investigation**: export CSV reports from AWS Cost Explorer, load into pandas to filter out baseline costs, and use bar charts to visualize sudden spikes in S3 API costs

## 3. Data manipulation with pandas

Transforming, grouping, slicing, aggregating.

- **SLO/error budget analysis**: load exports of ELK access logs into pandas, group by HTTP status code and service name, and aggregate to calculate the exact percentage of successful requests (2xx/3xx) vs. errors (5xx) to measure against your error budget
- **Deployment performance profiling**: parse Kubernetes events to track pod lifecycle timestamps. Calculate average time for pods to transition from `Pending` to `Running`, grouped by EC2 instance type
- **DORA metrics calculation**: compute deployment frequency and lead time for changes by calculating time deltas between commit timestamps and deploy timestamps, then resampling weekly

## 4. Joining data with pandas

Merging (inner/outer joins) and concatenating datasets.

- **Cost allocation and FinOps**: join billing data from the AWS Cost and Usage Report (CUR) with resource metadata parsed from Terraform state files. Merge on resource IDs to attribute untagged cloud costs to specific engineering teams
- **Root cause analysis**: correlate PagerDuty incident timestamps with application error counts from CloudWatch logs using time-series merge (`merge_asof`) to pinpoint which log errors spiked milliseconds before alarms fired
- **Infrastructure drift detection**: left-join AWS EC2 instances from `boto3` with Terraform-managed instances. Rows present only in the AWS data (`_merge == 'left_only'`) are rogue instances created outside IaC

## 5. Introduction to statistics in Python

Mean, median, variance, standard deviation, percentiles.

- **Defining realistic SLOs**: averages hide tail latency. Calculate P95 and P99 of request latency from Prometheus metrics rather than using mean response time. This ensures SLOs reflect the experience of the slowest 5% of users
- **Anomaly detection**: calculate standard deviation of disk I/O across a fleet of Datadog-monitored database nodes. If a single node exceeds 3 standard deviations from the mean, trigger preemptive investigation for hardware degradation
- **Error budget burn rate**: use Exponentially Weighted Moving Averages (EWMA) to smooth micro-bursts of errors while remaining sensitive to sustained incidents. Formula: `Burn Rate = Current Error Rate / Allowed Error Rate`

### Why percentiles beat averages for SLOs

If 99 requests take 10ms and 1 request takes 10,000ms, the average is ~110ms (looks fine), but the P99 is 10,000ms (severe customer impact). SREs must define SLIs using percentiles, not means.

## 6. Introduction to data visualization with Seaborn

Heatmaps, boxplots, violin plots, statistical visualizations.

- **Cluster capacity planning**: create Seaborn boxplots of daily memory consumption across 50+ Kubernetes namespaces. Boxplots immediately visualize variance and identify namespaces with heavy memory constraints
- **Cost optimization scheduling**: plot a Seaborn heatmap of AWS EC2 CPU utilization by hour-of-day (y-axis) and day-of-week (x-axis). This provides concrete evidence for implementing auto-scaling schedules that shut down staging environments on weeknights
- **Incident postmortem reports**: create annotated charts with vertical lines marking the exact second a bad config was pushed, when the alert fired, and when rollback completed — far more compelling than Grafana screenshots in postmortem documents

### When Grafana is not enough

| Scenario | Chart type | Why custom viz |
|---|---|---|
| Latency distribution analysis | Violin plot / KDE | Reveals bimodal distributions (cold starts, cache misses) that time-series lines hide |
| Incident postmortem timeline | Annotated Matplotlib | Programmatic vertical lines, shaded regions, exportable to PDF |
| Executive cost reports | Stacked bar + trendline | Projected spend vs. budget allocations over 4 quarters |
| Team DORA metrics comparison | Seaborn boxplot | Shows lead time variance across squads |
| Resource utilization patterns | Heatmap (hour x day) | Concrete evidence for auto-scaling schedules |

## 7. Exploratory data analysis (EDA) in Python

Cleaning messy data, finding hidden patterns, handling missing values.

- **Post-mortem log investigation**: load gigabytes of unstructured CloudWatch logs, clean inconsistent timestamp formats, fill in missing correlation IDs, and explore the sequence of events in a cascading microservice failure
- **Cloud waste discovery**: perform EDA on AWS CUR data to identify orphaned resources. Filter out attached resources, handle null values in attachment columns, and cross-reference with active deployment manifests to safely delete thousands of dollars of unused EBS volumes

## 8. Sampling in Python

Random sampling, stratified sampling, bootstrapping.

- **High-volume log analysis (cost reduction)**: ingesting 100% of CDN access logs into ELK is prohibitively expensive. Apply stratified sampling based on HTTP endpoint paths to accurately estimate error rates and traffic patterns while only storing 5% of total log volume
- **Stress testing and capacity planning**: use statistical bootstrapping on historical Prometheus CPU metrics from peak traffic periods. Resample with replacement to simulate thousands of potential load scenarios, ensuring Kubernetes cluster limits can handle worst-case spikes
- **SLI confidence intervals**: when sampling traces instead of analyzing 100%, calculate confidence intervals on the sampled SLI. E.g., "We are 95% confident the true P99 latency is between 240ms and 260ms based on our 5% sample rate"

## 9. Hypothesis testing in Python

A/B testing, p-values, t-tests, statistical significance.

- **Canary deployment validation**: roll out a new Kubernetes ingress controller config to 10% of traffic. Define null hypothesis: "The new config has no effect on latency." Run a Mann-Whitney U test comparing canary vs. stable pods using Prometheus metrics. A p-value < 0.05 justifies full rollout
- **Cost vs. performance migration testing**: test the hypothesis that migrating to AWS Graviton (ARM) instances reduces costs without impacting latency. Compare Datadog performance metrics and AWS Cost Explorer data before/after migration using a paired t-test
- **Change impact analysis**: after deploying a new database connection pool configuration, statistically compare query latencies from the 24 hours before vs. after the change to determine if the improvement is real or noise

### Non-parametric tests for infrastructure

Latency distributions are almost never normally distributed — they are right-skewed. Standard t-tests assume normality. Use the **Mann-Whitney U test** for comparing two distributions (canary vs. baseline) or the **Kolmogorov-Smirnov test** for comparing distribution shapes.

## Pandas cheat sheet for ops

| Operation | pandas function | SRE use case |
|---|---|---|
| Filter errors | `df[df['status_code'] >= 500]` | Isolate 5xx errors from access logs |
| Group and count | `df.groupby('service')['error'].sum()` | Error counts per microservice |
| Time-series resample | `df.resample('W').size()` | Weekly deployment frequency (DORA) |
| Merge datasets | `pd.merge(aws_df, tf_df, on='id', how='left')` | Find infrastructure drift |
| Time deltas | `(df['deploy'] - df['commit']).dt.total_seconds()` | Lead time for changes (DORA) |
| Rolling statistics | `df['latency'].rolling('1h').quantile(0.99)` | Rolling P99 latency calculation |
| Value counts | `df['endpoint'].value_counts().head(10)` | Top 10 failing endpoints |

## The career advantage

Most data scientists don't understand Kubernetes networking, kernel panics, or Terraform. Most SREs don't understand non-parametric statistics, DataFrame vectorization, or ML pipelines. The intersection is small and high-value.

### Roles this enables

| Role | Why data skills are required |
|---|---|
| **ML platform engineer (MLOps)** | Cannot build infrastructure for data scientists without speaking their language — Python, pandas, CUDA, data lineage |
| **FinOps engineer** | Managing $10M+ cloud bills requires treating billing data as a big-data problem |
| **Observability engineer** | Moving beyond Datadog setup to running anomaly detection models on distributed trace data |
| **Platform data engineer** | Building internal developer platforms with usage analytics and efficiency metrics |

### Path to staff/principal engineer

A Senior Engineer builds robust systems. A Staff/Principal Engineer aligns system architecture with business outcomes. Data literacy is the bridge:

- You cannot convince a VP to halt feature work for tech debt by saying "the database is acting weird"
- You *can* convince them with a rigorous analysis showing deployment lead times degraded 40% with R-squared correlation to un-refactored microservices, backed by statistically significant test data showing a resulting drop in user conversion
- Data literacy enables authoring definitive, heavily quantified design documents that drive organizational change
