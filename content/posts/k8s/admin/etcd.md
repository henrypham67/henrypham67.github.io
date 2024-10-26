# ETCD

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
 