---
title: 'ETCD'
date: 2024-10-26T16:00:33+07:00
draft: true
tags: ["kubernetes"]
flashcards:
  - q: "What is etcd?"
    a: "A distributed key-value store that holds all Kubernetes cluster state."
  - q: "What does the kube-scheduler do?"
    a: "Watches for newly created Pods with no assigned Node and selects a Node to run them on."
  - q: "What is a ReplicaSet?"
    a: "Ensures a specified number of Pod replicas are running at any given time."
  - q: "What is the difference between a Deployment and a StatefulSet?"
    a: "Deployments are for stateless apps with interchangeable Pods; StatefulSets give each Pod a stable identity and persistent storage."
  - q: "What is a PersistentVolumeClaim (PVC)?"
    a: "A request for storage that binds to a PersistentVolume matching its size and access mode."
quiz:
  title: "Kubernetes Basics Quiz"
  questions:
    - q: "Which component stores the entire cluster state in Kubernetes?"
      options:
        - "kube-apiserver"
        - "etcd"
        - "kube-scheduler"
        - "kubelet"
      correct: 1
    - q: "What command creates a new Kubernetes namespace?"
      options:
        - "kubectl apply namespace my-ns"
        - "kubectl create ns my-ns"
        - "kubectl new namespace my-ns"
        - "kubectl add ns my-ns"
      correct: 1
    - q: "Which resource exposes a Deployment to external traffic?"
      options:
        - "ConfigMap"
        - "PersistentVolume"
        - "Service of type LoadBalancer"
        - "ResourceQuota"
      correct: 2
    - q: "What does 'kubectl rollout undo deployment/my-app' do?"
      options:
        - "Deletes the deployment"
        - "Rolls back to the previous ReplicaSet revision"
        - "Pauses the rollout"
        - "Scales the deployment to zero"
      correct: 1
---

## Definition

```text
etcd is a consistent and highly-available key value store used as Kubernetes' backing store for all cluster data.
```

1. How is ETCD used in the Kubernetes' control plane?
   - It's used to store and manage the configuration data
2. How is ETCD used to store Kubernetes cluster data?
      - API server act as an interface to interact with the client and others components
3. How is ETCD crucial to Kubernetes?
   - Etcd allows clients to subscribe to changes to a particular key or set of key

## Flashcards

{{< flashcards >}}

## Quiz

{{< quiz >}}
