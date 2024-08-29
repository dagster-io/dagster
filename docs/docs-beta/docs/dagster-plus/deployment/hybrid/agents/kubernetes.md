---
title: "Running Dagster+ agents on Kubernetes"
displayed_sidebar: "dagsterPlus"
sidebar_position: 30
sidebar_label: "Kubernetes"
---

# Running Dagster+ agents on Kubernetes

This page provides instructions for running the [Dagster+ agent](dagster-plus/getting-started/whats-dagster-plus#Agents) on a [Kubernetes](https://kubernetes.io) cluster.

## Installation


### Prerequisites

You'll need [a Kubernetes cluster. This can be a self-hosted Kubernetes cluster or a managed offering like [Amazon EKS](https://aws.amazon.com/eks/), [Azure AKS](https://azure.microsoft.com/en-us/products/kubernetes-service), or [Google GKE](https://cloud.google.com/kubernetes-engine).

We recommend installing the Dagster+ agent using [Helm](https://helm.sh).

## Step 1: Create a Kubernetes namespace

```shell
kubectl create namespace dagster-cloud
```

## Step 2: Create an agent token secret

[Generate an agent token](dagster-plus/deployment/tokens) and set it as a Kubernetes secret:

```shell
kubectl --namespace dagster-cloud create secret generic dagster-cloud-agent-token --from-literal=DAGSTER_CLOUD_AGENT_TOKEN=<token>
```

## Step 3: Add the Dagster+ agent Helm chart repository

```shell
helm repo add dagster-cloud https://dagster-io.github.io/helm-user-cloud
helm repo update
```

## Step 4: Install the Dagster+ agent Helm chart

```shell
helm --namespace dagster-cloud install agent --install dagster-cloud/dagster-cloud-agent
```

## Upgrading

You can use Helm to do rolling upgrades of your Dagster+ agent

```shell
helm repo update
helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --set dagsterCloudAgent.image.tag=latest
```

## Common configurations

You can customize your Dagster+ agent using [Helm values](https://artifacthub.io/packages/helm/dagster-cloud/dagster-cloud-agent?modal=values). Some common configuration include

### Configuring your agents to serve branch deployments

[Branch deployments](dagster-plus/deployment/branch-deployments) are lightweight staging environments created for each code change. To configure your Dagster+ agent to manage them:

```shell
helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --set dagsterCloud.branchDeployments=true
```

### High availability configurations

You can configure your Dagster+ agent to run with multiple replicas. Work will be load balanced across all replicas.

```shell
helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --set dagsterCloudAgent.replicas=2
```

Work load balanced across agents isn't not sticky; there's no guarantee the agent that launched a run will be the same one to receive instructions to terminate it. This is fine if both replicas run on the same Kubernetes cluster because either agent can terminate the run. But if your agents are physically isolated (for example, they run on two different Kubernetes clusters), you should configure:

```shell
helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --set isolatedAgents=true
```
