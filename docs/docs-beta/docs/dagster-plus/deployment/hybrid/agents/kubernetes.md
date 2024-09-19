---
title: "Running Dagster+ agents on Kubernetes"
displayed_sidebar: "dagsterPlus"
sidebar_position: 30
sidebar_label: "Kubernetes"
---

# Running Dagster+ agents on Kubernetes

This page provides instructions for running the [Dagster+ agent](/todo) on a [Kubernetes](https://kubernetes.io) cluster.

## Installation


### Prerequisites

You'll need a Kubernetes cluster. This can be a self-hosted Kubernetes cluster or a managed offering like [Amazon EKS](https://aws.amazon.com/eks/), [Azure AKS](https://azure.microsoft.com/en-us/products/kubernetes-service), or [Google GKE](https://cloud.google.com/kubernetes-engine).

You'll also need access to a container registry to which you can push images and from which pods in the Kubernetes cluster can pull images. This can be a self-hosted registry or a managed offering like [Amazon ECR](https://aws.amazon.com/ecr/), [Azure ACR](https://azure.microsoft.com/en-us/products/container-registry), or [Google GCR](https://cloud.google.com/artifact-registry).

We recommend installing the Dagster+ agent using [Helm](https://helm.sh).

## Step 1: create a Kubernetes namespace

```shell
kubectl create namespace dagster-cloud
```

## Step 2: Create an agent token secret

[Generate an agent token](/dagster-plus/deployment/hybrid/tokens) and set it as a Kubernetes secret:

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

```yaml
# values.yaml
dagsterCloudAgent:
    image:
        tag: latest
```

```shell
helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --values ./values.yaml
```

## Common configurations

You can customize your Dagster+ agent using [Helm values](https://artifacthub.io/packages/helm/dagster-cloud/dagster-cloud-agent?modal=values). Some common configuration include

### Configuring your agents to serve branch deployments

[Branch deployments](/dagster-plus/deployment/branch-deployments) are lightweight staging environments created for each code change. To configure your Dagster+ agent to manage them:

```yaml
# values.yaml
dagsterCloud:
    branchDeployment: true
```

```shell
helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --values ./values.yaml
```

### High availability configurations

You can configure your Dagster+ agent to run with multiple replicas. Work will be load balanced across all replicas.

```yaml
# values.yaml
dagsterCloudAgent:
    replicas: 2
```

```shell
helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --values ./values.yaml
```

Work load balanced across agents isn't not sticky; there's no guarantee the agent that launched a run will be the same one to receive instructions to terminate it. This is fine if both replicas run on the same Kubernetes cluster because either agent can terminate the run. But if your agents are physically isolated (for example, they run on two different Kubernetes clusters), you should configure:

```yaml
# values.yaml
isolatedAgents: true
```

```shell
helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --values ./values.yaml
```

## Troubleshooting tips

You can see basic health information about your agent in the Dagster+ UI:

![Screenshot of agent health information](/img/placeholder.svg)

### View logs

```shell
kubectl --namespace dagster-cloud logs -l deployment=agent
```
