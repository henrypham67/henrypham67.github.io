---
title: "[HOWTO] Monitor k8s cluster & app"
date: 2024-10-26T16:00:33+07:00
slug: k8s-prom
draft: true
---

deploy prome out or inside cluster?
-> close to target as possible

service discovery (k8s components/ state metrics, node exporters) -> k8s API

Usecases:
- collect metric to build dashboard
- trigger alert -> alertmanager
- scape data to get insight

Architecture:
API from exporters <- scrape data using HTTP -> TSDB <- PromQL
short lived job -> PushGateway <- scrape

pull > push:
easy to check target is down
push cause overload
have a list of truth to control target

push > pull:
event-based model
short lived job

Metrics
2 attributes:
- HELP
- TYPE
    - Counter: how many times
    - Gauge: current value
    - histogram: how long/big
    - Summary


[2m] @\<unix-timestamp\> Offset 5m 


What to Instrument?
- Online-serving system: immediate response
  - number of requests/queries
  - number of errors
  - latency
  - error of in progress requests
- Offline processing service
  - Amount of queued work
  - Amount of work in progress
- Batch job: requied push gw
  - Overall time


# Service Discovery
## Re-labeling
classify/filter Prometheus targets & metrics by rewriting their label set for SD only

label
- internal label: \__name\__
monitor k8s cluster:
- control plane components
- kubelet cAdvisor
- kube-state-metrics -cluster level metrics (deploy, pod, metrics). unable by default -> kube-state-metrics container
- node-exporter - all nodes -> use AMI/daemonset*


silence alert while mantainence


How to make alertmanager match 2 alert? continue: true


use global config to reduce repetitive config in receivers


How to deploy? helm chart


How to add new scrape configs to kube-prometheus-stack?
- edit additionalScrapeConfigs
+ use service monitor, define a set of targets for prometheus to monitor and scrape it prevent you from touch directly to prometheus config,  


kubectl get ServiceMonitor -o=yaml to get the needed labels 


The same to PrometheusRule & Alertmanager Config (snake_case -> cammel case; matchers string:string -> name:string, value:string)
