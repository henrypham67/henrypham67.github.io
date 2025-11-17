---
title: 'Migrating from ArgoCD App-of-Apps to ApplicationSet'
date: 2025-09-28T18:27:05+07:00
draft: false
---

## Introduction

As your Kubernetes deployments scale, the static App-of-Apps pattern in ArgoCD can become unwieldy. Enter ApplicationSet for dynamic, templated management.

Explain benefits (scalability, reduced duplication, easier multi-cluster).

In this post, we'll migrate a real LGTM observability stack from App-of-Apps to ApplicationSet, sharing code and tips.

### Prerequisite

- ArgoCD installed
- basic Terraform
- basic ArgoCD resources
- basic YAML knowledge

## Apply ApplicationSet

In most of the case, I only use Terraform for Infrastructure only because it's a Infrastructure as Code (Iac) tool :D However instead of installing ArgoCD and root app manually which will be hard to track and reapply when incident happen. Below is how I do it

```HCL
resource "helm_release" "appset" {
  chart            = "argocd-apps"
  name             = "appset"
  repository       = "https://argoproj.github.io/argo-helm"
  namespace        = var.argocd_namespace
  create_namespace = true

  values = [file("${path.module}/values.yaml")]
}
```

```YAML
applicationsets:
  root-app:
    namespace: argocd
    goTemplate: true
    generators:
    - list:
        elements:
        - name: app-a
          namespace: test-app
          specYaml: |
            spec:
              sources:
                - repoURL: https://github.com/henrypham67/istio
                  targetRevision: HEAD
                  path: observability/argo/values/test-app-common
                - repoURL: https://github.com/henrypham67/istio
                  targetRevision: HEAD
                  path: observability/argo/values/test-app
                  kustomize:
                    patches:
                      # 1) Deployment
                      - target:
                          group: apps
                          version: v1
                          kind: Deployment
                          name: test-app
                        patch: |-
                          - op: replace
                            path: /metadata/name
                            value: app-a
                          - op: replace
                            path: /spec/selector/matchLabels/app
                            value: app-a
                          - op: replace
                            path: /spec/template/metadata/labels/app
                            value: app-a
                          - op: replace
                            path: /spec/template/spec/containers/0/env/0/value
                            value: app-a

                      # 2) Service
                      - target:
                          group: ""           # core API
                          version: v1
                          kind: Service
                          name: test-app
                        patch: |-
                          - op: replace
                            path: /metadata/name
                            value: app-a
                          - op: replace
                            path: /metadata/labels/app
                            value: app-a
                          - op: replace
                            path: /spec/selector/app
                            value: app-a
                          - op: replace
                            path: /spec/ports/0/name
                            value: tcp-800-app-a
              

                      # 3) VirtualService (Istio)
                      - target:
                          group: networking.istio.io
                          version: v1
                          kind: VirtualService
                          name: test-app
                        patch: |-
                          - op: replace
                            path: /metadata/name
                            value: app-a
                          - op: replace
                            path: /spec/http/0/match/0/uri/prefix
                            value: /app-a/
                          - op: replace
                            path: /spec/http/0/match/1/uri/prefix
                            value: /app-a
                          - op: replace
                            path: /spec/http/0/route/0/destination/host
                            value: app-a.test-app.svc.cluster.local

                      # 4) ServiceMonitor (Prometheus)
                      - target:
                          group: monitoring.coreos.com
                          version: v1
                          kind: ServiceMonitor
                          name: test-app
                        patch: |-
                          - op: replace
                            path: /metadata/name
                            value: app-a-servicemonitor
                          - op: replace
                            path: /spec/selector/matchLabels/app
                            value: app-a
                          - op: replace
                            path: /spec/endpoints/0/port
                            value: tcp-800-app-a
              syncPolicy:
                managedNamespaceMetadata:
                  labels:
                    kubernetes.io/metadata.name: test-app
                    istio-injection: enabled
                syncOptions:
                  - ApplyOutOfSyncOnly=true
                  - RespectIgnoreDifferences=true  # Unique to app-a/b/c
              ignoreDifferences:
                - group: apps
                  kind: Deployment
                  jsonPointers:
                    - /spec/replicas
        - name: app-b
          namespace: test-app
          specYaml: |
            spec:
              sources:
                repoURL: https://github.com/henrypham67/istio
                targetRevision: HEAD
                path: observability/argo/values/test-app
                kustomize:
                  patches:
                    # 1) Deployment
                    - target:
                        group: apps
                        version: v1
                        kind: Deployment
                        name: test-app
                      patch: |-
                        - op: replace
                          path: /metadata/name
                          value: app-b
                        - op: replace
                          path: /spec/selector/matchLabels/app
                          value: app-b
                        - op: replace
                          path: /spec/template/metadata/labels/app
                          value: app-b
                        - op: replace
                          path: /spec/template/spec/containers/0/env/0/value
                          value: app-b
                    # 2) Service
                    - target:
                        group: ""           # core API
                        version: v1
                        kind: Service
                        name: test-app
                      patch: |-
                        - op: replace
                          path: /metadata/name
                          value: app-b
                        - op: replace
                          path: /metadata/labels/app
                          value: app-b
                        - op: replace
                          path: /spec/selector/app
                          value: app-b
                        - op: replace
                          path: /spec/ports/0/name
                          value: tcp-800-app-b
                    # 3) VirtualService (Istio)
                    - target:
                        group: networking.istio.io
                        version: v1
                        kind: VirtualService
                        name: test-app
                      patch: |-
                        - op: replace
                          path: /metadata/name
                          value: app-b
                        - op: replace
                          path: /spec/http/0/match/0/uri/prefix
                          value: /app-b/
                        - op: replace
                          path: /spec/http/0/match/1/uri/prefix
                          value: /app-b
                        - op: replace
                          path: /spec/http/0/route/0/destination/host
                          value: app-b.test-app.svc.cluster.local
                    # 4) ServiceMonitor (Prometheus)
                    - target:
                        group: monitoring.coreos.com
                        version: v1
                        kind: ServiceMonitor
                        name: test-app
                      patch: |-
                        - op: replace
                          path: /metadata/name
                          value: app-b-servicemonitor
                        - op: replace
                          path: /spec/selector/matchLabels/app
                          value: app-b
                        - op: replace
                          path: /spec/endpoints/0/port
                          value: tcp-800-app-b
              syncPolicy:
                syncOptions:
                  - ApplyOutOfSyncOnly=true
                  - RespectIgnoreDifferences=true  # Unique to app-a/b/c
              ignoreDifferences:
                - group: apps
                  kind: Deployment
                  jsonPointers:
                    - /spec/replicas
        - name: app-c
          namespace: test-app
          specYaml: |
            spec:
              source:
                repoURL: https://github.com/henrypham67/istio
                targetRevision: HEAD
                path: observability/argo/values/test-app
                kustomize:
                  patches:
                    # 1) Deployment
                    - target:
                        group: apps
                        version: v1
                        kind: Deployment
                        name: test-app
                      patch: |-
                        - op: replace
                          path: /metadata/name
                          value: app-c
                        - op: replace
                          path: /spec/selector/matchLabels/app
                          value: app-c
                        - op: replace
                          path: /spec/template/metadata/labels/app
                          value: app-c
                        - op: replace
                          path: /spec/template/spec/containers/0/env/0/value
                          value: app-c
                    # 2) Service
                    - target:
                        group: ""           # core API
                        version: v1
                        kind: Service
                        name: test-app
                      patch: |-
                        - op: replace
                          path: /metadata/name
                          value: app-c
                        - op: replace
                          path: /metadata/labels/app
                          value: app-c
                        - op: replace
                          path: /spec/selector/app
                          value: app-c
                        - op: replace
                          path: /spec/ports/0/name
                          value: tcp-800-app-c
                    # 3) VirtualService (Istio)
                    - target:
                        group: networking.istio.io
                        version: v1
                        kind: VirtualService
                        name: test-app
                      patch: |-
                        - op: replace
                          path: /metadata/name
                          value: app-c
                        - op: replace
                          path: /spec/http/0/match/0/uri/prefix
                          value: /app-c/
                        - op: replace
                          path: /spec/http/0/match/1/uri/prefix
                          value: /app-c
                        - op: replace
                          path: /spec/http/0/route/0/destination/host
                          value: app-c.test-app.svc.cluster.local
                    # 4) ServiceMonitor (Prometheus)
                    - target:
                        group: monitoring.coreos.com
                        version: v1
                        kind: ServiceMonitor
                        name: test-app
                      patch: |-
                        - op: replace
                          path: /metadata/name
                          value: app-c-servicemonitor
                        - op: replace
                          path: /spec/selector/matchLabels/app
                          value: app-c
                        - op: replace
                          path: /spec/endpoints/0/port
                          value: tcp-800-app-c
              ignoreDifferences:
                - group: apps
                  kind: Deployment
                  jsonPointers:
                    - /spec/replicas
        - name: keda
          namespace: keda
          specYaml: |
            spec:
              sources:
                - repoURL: https://github.com/henrypham67/istio
                  targetRevision: HEAD
                  path: observability/argo/values/keda
                  ref: custom
                - repoURL: https://kedacore.github.io/charts
                  chart: keda
                  targetRevision: 2.17.1
                  helm:
                    valueFiles:
                      - $custom/observability/argo/values/keda/values.yaml
                - repoURL: https://kedacore.github.io/charts
                  chart: keda-add-ons-http
                  targetRevision: 0.10.0
              syncPolicy:
                managedNamespaceMetadata:
                  labels:
                    monitoring: enabled
                syncOptions:
                  - ApplyOutOfSyncOnly=true
                  - ServerSideApply=true
        - name: kiali
          namespace: istio-system
          specYaml: |
            spec:
              source:
                repoURL: https://kiali.org/helm-charts
                chart: kiali-operator
                targetRevision: 2.9.0
        - name: kube-prometheus-stack
          namespace: monitoring
          specYaml: |
            spec:
              sources:
                - repoURL: https://github.com/henrypham67/istio
                  targetRevision: HEAD
                  path: observability/argo/values/kube-prometheus-stack
                  ref: custom
                - repoURL: https://prometheus-community.github.io/helm-charts
                  chart: kube-prometheus-stack
                  targetRevision: 72.1.0
                  helm:
                    valueFiles:
                      - $custom/observability/argo/values/kube-prometheus-stack/values.yaml
              syncPolicy:
                syncOptions:
                  - ApplyOutOfSyncOnly=true
                  - ServerSideApply=true
        - name: loki
          namespace: logging
          specYaml: |
            spec:
              sources:
                - repoURL: https://grafana.github.io/helm-charts
                  chart: loki
                  targetRevision: 6.29.0
                  helm:
                    valueFiles:
                      - $custom/observability/argo/values/loki.yaml
                - repoURL: https://github.com/henrypham67/istio
                  targetRevision: HEAD
                  ref: custom
        - name: mimir
          namespace: monitoring
          specYaml: |
            spec:
              sources:
                - repoURL: https://grafana.github.io/helm-charts
                  chart: mimir-distributed
                  targetRevision: 5.7.0
                  helm:
                    valueFiles:
                      - $custom/observability/argo/values/mimir.yaml
                - repoURL: https://github.com/henrypham67/istio
                  targetRevision: HEAD
                  ref: custom
        - name: open-telemetry
          namespace: opentelemetry-operator-system
          specYaml: |
            spec:
              sources:
                - repoURL: https://open-telemetry.github.io/opentelemetry-helm-charts
                  chart: opentelemetry-operator
                  targetRevision: 0.90.4
                  helm:
                    valueFiles:
                      - $custom/observability/argo/values/open-telemetry/values.yaml
                - repoURL: https://github.com/henrypham67/istio
                  targetRevision: HEAD
                  path: observability/argo/values/open-telemetry
                  ref: custom
              syncPolicy:
                syncOptions:
                  - ServerSideApply=true
                  - ApplyOutOfSyncOnly=true
        - name: tempo
          namespace: monitoring
          specYaml: |
            spec:
              sources:
                - repoURL: https://github.com/henrypham67/istio
                  targetRevision: HEAD
                  ref: custom
                - repoURL: https://grafana.github.io/helm-charts
                  chart: tempo
                  targetRevision: 1.21.1
                  helm:
                    valueFiles:
                      - $custom/observability/argo/values/tempo.yaml
              syncPolicy:
                syncOptions:
                  - ServerSideApply=true
                  - ApplyOutOfSyncOnly=true
                  - CreateNamespace=true
    template:
      metadata:
        name: '{{.name}}'
      spec:
        project: default
        destination:
          server: https://kubernetes.default.svc
          namespace: '{{.namespace}}'
        syncPolicy:
          automated:
            prune: true
            selfHeal: true
    templatePatch: |
      {{.specYaml}}
    syncPolicy:
      preserveResourcesOnDeletion: true
```

why I chose to install root Application Set using Helm chart? there are 2 reasons. Firstly, I want to utilize IDE features for YAML, when I use Terraform resource `kubernetes_resources` or `kubectl_manifest` the editor failed to suggesting or even highlighting when there is a mix between Terraform templating and Golang templating. On top of that I want to leverage a YAML feature which anchors.
