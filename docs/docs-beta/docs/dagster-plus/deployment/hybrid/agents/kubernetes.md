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

You can use Helm to do rolling upgrades of your Dagster+ agent. The version of the agent does not need to be the same as the version of Dagster used in your projects. The Dagster+ control plane is upgraded automatically but is backwards compatible with older versions of the agent.

:::tip
We recommend upgrading your Dagster+ agent every 6 months
:::

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

## Troubleshooting tips

You can see basic health information about your agent in the Dagster+ UI:

{/* TODO: Screenshot */}

### View logs

```shell
kubectl --namespace dagster-cloud logs -l deployment=agent
```


## Common configurations

There are three places to customize how Dagster interacts with Kubernetes:
- *Globally* by configuring the Dagster+ agent using [Helm values](https://artifacthub.io/packages/helm/dagster-cloud/dagster-cloud-agent?modal=values)
- *Per Project* by configuring the `dagster_cloud.yaml` file for your [code location](/dagster-plus/deployment/code-locations)
- *Per Asset or Job* by adding tags to the [asset](/todo), [job](/todo), or [customizing the Kubernetes pipes invocation](/todo)

Changes apply in a hierarchy, for example a customization for an asset will over-ride a default set globally in the agent configuration. 

An exhaustive list of settings is available [here](/dagster-plus/deployment/hybrid/agents/settings), but common options are presented below. 


### Configure your agents to serve branch deployments

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

### Deploy a high availability architecture

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

### Use a secret to pull images 

The agent is responsible for managing the lifecycle of your code locations and will typically need to pull images after your CICD process builds them and pushes them to your registry. You can specify a secret the agent will use to authenticate to your image registry.

:::tip
For cloud based Kubernetes such as AWS EKS, AKS, or GCP, you typically do not need an image pull secret. The role used by Kubernetes will have permission to access the registry. You can skip this configuration.
:::

First create the secret. This step will vary based on the registry you use, but for DockerHub: 

```
kubectl create secret docker-registry regCred \
  --docker-server=DOCKER_REGISTRY_SERVER \
  --docker-username=DOCKER_USER \
  --docker-password=DOCKER_PASSWORD \
  --docker-email=DOCKER_EMAIL
```

Use helm to configure the agent with the secret:

```yaml file=values.yaml
# values.yaml
imagePullSecrets: [regCred]
```

```shell
helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --values ./values.yaml
```

### Don't send Dagster+ stdout and stderr 

### Make secrets available to your code 

### Use a different role for a specific code location

### Use an agent installed in a different environement for a deployment

### Use an agent installed in a different environement for a code location

### Set default resources for a code location 

### Request more resources (CPU, memory, GPUs) for an asset 

:::note 
This guide shows how to request more resources for the Dagster run of an asset. If your Dagster asset uses the [Kubernetes pipes client](/todo) you should instead request resources like [this](https://github.com/dagster-io/hooli-data-eng-pipelines/blob/master/hooli_data_eng/assets/forecasting/__init__.py#L257-L288).
:::

