---
title: 'Interview'
date: 2024-10-01T17:15:15+07:00
draft: true
---

## EC2 (Elastic Compute Cloud)

### What are the different types of EC2 instance types, and how do you choose one for your workload?

- General purpose
- Memory optimize
- Compute optimize
- Storage optimize

### Explain the difference between a Spot Instance, Reserved Instance, and On-Demand Instance

- Spot: short-term usage, fault-tolerant systems
- Reserved: Long-term usage, optionally pay upfront (1 or 3 years)
- On-demand: charged on second (linux) or hour (windows) usage

### How do you secure EC2 instances using Security Groups and NACLs (Network Access Control Lists)?

- Security Groups (SG):
  - Acts as a virtual firewall at the instance level
  - stateful (you only need to define rules once for both directions)
  - allow only allow rules.
- NACLs:
  - Stateless (You need to define both inbound and outbound rules separately)
  - operate at the subnet level
  - NACLs can have both allow and deny rules.

### What is an EC2 instance store, and how does it differ from EBS (Elastic Block Store)?

- Instance Store:
  - Temporary storage
  - physically attached to the host where your EC2 instance runs
  - It is ephemeral (data is lost when the instance is stopped or terminated).
- EBS:
  - Persistent block storage 
  - independent of the instance lifecycle
  - Data persists even after stopping or terminating the instance.

### How can you scale EC2 instances horizontally?

Use Auto Scaling Groups based on metric from Cloudwatch, set a threshold based on a EC2 instance metric, it will scale up or down base on that thresh hold

### What is an Elastic IP, and when would you use one?

Elastic IP a service which assign an EC2 instance with a public IP

### Explain how you would monitor an EC2 instance's performance

I will observe instance primarily based on CPU and RAM metrics. Addition to those metrics are network and IO throughput

## S3 (Simple Storage Service)

What is S3, and how is it used for object storage in AWS?
Explain the different storage classes in S3 (e.g., S3 Standard, S3 Glacier).
How would you secure access to S3 buckets?
What is versioning in S3, and why is it useful?
How does S3 ensure data durability and availability?
Explain S3 Transfer Acceleration.
How would you implement lifecycle policies for data stored in S3?
ECR (Elastic Container Registry)
What is ECR, and how does it relate to ECS or Kubernetes?
How would you push and pull Docker images to and from ECR?
Explain the security mechanisms available for ECR.
How does ECR integrate with CI/CD pipelines?
RDS (Relational Database Service)
What are the key differences between RDS and running a database on EC2?
What are the available database engines supported by RDS, and when would you use each one?
Explain Multi-AZ deployments in RDS.
How does automated backup work in RDS, and how would you restore a database from a backup?
What are Read Replicas in RDS, and how do they improve performance?

## DynamoDB

What is DynamoDB, and when would you choose it over RDS?
Explain the difference between DynamoDB's Provisioned and On-Demand capacity modes.
What is the DynamoDB Global Table, and how does it help in cross-region replication?
How does DynamoDB handle indexing, and what are Global and Local Secondary Indexes?
What is DynamoDB Streams, and how does it work?

## Networking Services

### What is a VPC (Virtual Private Cloud), and why is it important in AWS?

A service lets you launch AWS resources in a isolated virtual network

### Explain the difference between a Security Group and a Network ACL (NACL).

### How do you connect a private VPC to the internet?


What is a NAT Gateway, and why would you use one?
Explain what VPC Peering is and when it should be used.
How would you set up a VPN connection between your on-premises data center and AWS?
What are Elastic Load Balancers, and how do they work within a VPC?
How do Route Tables work in AWS VPC?
