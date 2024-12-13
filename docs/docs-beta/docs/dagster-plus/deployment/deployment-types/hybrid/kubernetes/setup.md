---
title: Kubernetes agent setup
sidebar_position: 100
---

This page provides instructions for running the [Dagster+ agent](/todo) on a [Kubernetes](https://kubernetes.io) cluster.

## Installation

### Prerequisites

You'll need a Kubernetes cluster. This can be a self-hosted Kubernetes cluster or a managed offering like [Amazon EKS](https://aws.amazon.com/eks/), [Azure AKS](https://azure.microsoft.com/en-us/products/kubernetes-service), or [Google GKE](https://cloud.google.com/kubernetes-engine).

You'll also need access to a container registry to which you can push images and from which pods in the Kubernetes cluster can pull images. This can be a self-hosted registry or a managed offering like [Amazon ECR](https://aws.amazon.com/ecr/), [Azure ACR](https://azure.microsoft.com/en-us/products/container-registry), or [Google GCR](https://cloud.google.com/artifact-registry).

We recommend installing the Dagster+ agent using [Helm](https://helm.sh).

### Step 1: Create a Kubernetes namespace

```shell
kubectl create namespace dagster-cloud
```

### Step 2: Create an agent token secret

[Generate an agent token](/dagster-plus/deployment/management/tokens) and set it as a Kubernetes secret:

```shell
kubectl --namespace dagster-cloud create secret generic dagster-cloud-agent-token --from-literal=DAGSTER_CLOUD_AGENT_TOKEN=<token>
```

### Step 3: Add the Dagster+ agent Helm chart repository

```shell
helm repo add dagster-cloud https://dagster-io.github.io/helm-user-cloud
helm repo update
```

### Step 4: Install the Dagster+ agent Helm chart

```shell
helm --namespace dagster-cloud install agent --install dagster-cloud/dagster-cloud-agent
```

## Upgrading

You can use Helm to do rolling upgrades of your Dagster+ agent. The version of the agent doesn't need to be the same as the version of Dagster used in your projects. The Dagster+ control plane is upgraded automatically but is backwards compatible with older versions of the agent.

:::tip
We recommend upgrading your Dagster+ agent every 6 months. The version of your agent is visible on the "Deployments", "Agents" tab https://your-org.dagster.plus/deployment/health. The current version of the agent matches the most [recent Dagster release](https://github.com/dagster-io/dagster/releases).
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

[comment]: <> (TODO: Screenshot of Dagster+ Deployments agents tab)

### View logs

```shell
kubectl --namespace dagster-cloud logs -l deployment=agent
```

## Common configurations

There are three places to customize how Dagster interacts with Kubernetes:

- **Per Deployment** by configuring the Dagster+ agent using [Helm values](https://artifacthub.io/packages/helm/dagster-cloud/dagster-cloud-agent?modal=values)
- **Per Project** by configuring the `dagster_cloud.yaml` file for your [code location](/dagster-plus/deployment/code-locations)
- **Per Asset or Job** by adding tags to the [asset](/todo), [job](/todo), or [customizing the Kubernetes pipes invocation](/todo)

Changes apply in a hierarchy, for example, a customization for an asset will override a default set globally in the agent configuration. Attributes that are not customized will use the global defaults.

An exhaustive list of settings is available [here](/dagster-plus/deployment/management/settings/hybrid-agent-settings), but common options are presented below.

### Configure your agents to serve branch deployments

[Branch deployments](/dagster-plus/features/ci-cd/branch-deployments/index.md) are lightweight staging environments created for each code change. To configure your Dagster+ agent to manage them:

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

Work load balanced across agents isn't sticky; there's no guarantee the agent that launched a run will be the same one to receive instructions to terminate it. This is fine if both replicas run on the same Kubernetes cluster because either agent can terminate the run. But if your agents are physically isolated (for example, they run on two different Kubernetes clusters), you should configure:

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

The agent is responsible for managing the lifecycle of your code locations and will typically need to pull images after your CI/CD process builds them and pushes them to your registry. You can specify a secret the agent will use to authenticate to your image registry.

:::tip
For cloud-based Kubernetes deployments such as AWS EKS, AKS, or GCP, you don't need an image pull secret. The role used by Kubernetes will have permission to access the registry, so you can skip this configuration.
:::

First create the secret. This step will vary based on the registry you use, but for DockerHub:

```
kubectl create secret docker-registry regCred \
  --docker-server=DOCKER_REGISTRY_SERVER \
  --docker-username=DOCKER_USER \
  --docker-password=DOCKER_PASSWORD \
  --docker-email=DOCKER_EMAIL
```

Use Helm to configure the agent with the secret:

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

By default, Dagster+ will capture stdout and stderr and present them to users in the runs page. You may not want to send Dagster+ these logs, in which case you should update the compute logs setting.

<Tabs>

<TabItem value="s3" label="Store logs in S3">

The compute logs for a run will be stored in your S3 bucket and a link will be presented to users in the Dagster run page.

```yaml file=values.yaml
# values.yaml
computeLogs:
  enabled: true
  custom:
    module: dagster_aws.s3.compute_log_manager
    class: S3ComputeLogManager
    config:
      show_url_only: true
      bucket: your-compute-log-storage-bucket
      region: your-bucket-region
```

```shell
helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --values ./values.yaml
```

</TabItem>
<TabItem value="disable" label="Do not store logs">

You can turn off compute logs altogether which will prevent Dagster+ from storing stdout and stderr. This setting will prevent users from accessing these logs.

```yaml file=values.yaml
# values.yaml
computeLogs:
  enabled: false
```

```shell
helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --values ./values.yaml
```

</TabItem>
</Tabs>

### Make secrets available to your code

You can make secrets available [through the Dagster+ web interface](/dagster-plus/deployment/management/environment-variables) or through Kubernetes. Configuring secrets through Kubernetes has the benefit that Dagster+ never stores or accesses the secrets, and they can be managed as code. First, create the Kubernetes secret:

```bash
kubectl create secret generic database-password-kubernetes-secret \
    --from-literal=DATABASE_PASSWORD=your_password \
    --namespace dagster-plus
```

Next, determine if the secret should be available to all code locations or a single code location.

<Tabs>
<TabItem value="agent-secrets" label="All code locations">

```yaml file=values.yaml
# values.yaml
workspace:
  envSecrets:
    - name: database-password-kubernetes-secret
```

```shell
helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --values ./values.yaml
```

`envSecrets` will make the secret available in an environment variable, see the Kubernetes docs on [`envFrom` for details](https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables). In this example the environment variable `DATABASE_PASSWORD` would have the value `your_password`.

</TabItem>

<TabItem value="code-location-secrets" label="Single code location">

Modify the [`dagster_cloud.yaml` file](/todo) in your project's Git repository:

```yaml file=dagster_cloud.yaml
location:
  - location_name: cloud-examples
    image: dagster/dagster-cloud-examples:latest
    code_source:
      package_name: dagster_cloud_examples
    container_context:
      k8s:
        env_secrets:
          - database-password
```

`env_secrets` will make the secret available in an environment variable, see the Kubernetes docs on [`envFrom` for details](https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables). In this example the environment variable `DATABASE_PASSWORD` would have the value `your_password`.

</TabItem>
</Tabs>

:::note
If you need to request secrets from a secret manager like AWS Secrets Manager or HashiCorp Vault, follow one of the prior methods to give your code access to vault credentials. Then, inside your Dagster code, use those credentials to authenticate a Python client that requests secrets from the secret manager.
:::

### Use a different service account for a specific code location

Modify the [`dagster_cloud.yaml` file](/todo) in your project's Git repository:

```yaml file=dagster_cloud.yaml
locations:
  - location_name: cloud-examples
    image: dagster/dagster-cloud-examples:latest
    code_source:
      package_name: dagster_cloud_examples
    container_context:
      k8s:
        service_account_name: my_service_account_name
```

### Run Dagster+ with different Kubernetes clusters

<Tabs>
<TabItem value="ha" label="Work can happen in either cluster">

Deploy the agent Helm chart to each cluster, setting the `isolatedAgents.enabled` flag to true.

```yaml file=values.yaml
# values.yaml
isolatedAgents:
  enabled: true
```

```shell
helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --values ./values.yaml
```

In this configuration, requests will be randomly distributed across agents in both clusters.

</TabItem>
<TabItem value="queues" label="Global asset graph, but projects run in different clusters">

You may wish to run data pipelines from project A in Kubernetes cluster A, and project B in Kubernetes cluster B. For example, you may wish to run some jobs on-premise and other jobs in AWS. To accomplish this task:

- Deploy an agent into each environment and use the `agentQueue` configuration:
  Specify an agent queue for the on-prem agent:

  ```yaml file=values.yaml
  dagsterCloud:
    agentQueues:
      additionalQueues:
        - on-prem-agent-queue
  ```

  Deploy onto the on-prem Kubernetes cluster:

  ```shell
  helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --values ./values.yaml
  ```

  Specify an agent queue for the agent on AWS:

  ```yaml file=values.yaml
  dagsterCloud:
    agentQueues:
      additionalQueues:
        - aws-agent-queue
  ```

  Deploy onto the AWS Kubernetes cluster:

  ```shell
  helm --namespace dagster-cloud upgrade agent \
    dagster-cloud/dagster-cloud-agent \
    --values ./values.yaml
  ```

- Create separate code locations for each project
- Update the `dagster_cloud.yaml` file for each code location
  ```yaml file=dagster_cloud.yaml
  locations:
    - location_name: project-a
      ...
      agent_queue: on-prem-agent-queue
    - location_name: project-b
      ...
      agent_queue: aws-agent-queue
  ```

:::tip
Code locations without an `agent_queue` will be routed to a default queue. By default, all agents will serve this default queue. You can specify which agent should serve the default queue using the `includeDefaultQueue` setting:

```yaml file=values.yaml
dagsterCloud:
  agentQueues:
    includeDefaultQueue: true
```

:::

</TabItem>
<TabItem value="separate-agents" label="Separate deployments per cluster">

If you want completely separate environments with their own asset graph, run history, and access controls you should create different Dagster+ deployments. Separate deployments are common for isolated tenants or separate dev, stage, and prod environments. Multiple deployments require a Dagster+ Pro plan. To create separate deployments:

- Navigate to the deployments page for your organization: https://your-organizaiton.dagster.plus/org-settings/deployments

- Click "New Deployment"

- Follow the preceding instructions for creating and deploying agent for this deployment

</TabItem>
</Tabs>

### Request resources such as CPU, memory, or GPU

:::tip
Dagster+ makes it easy to monitor CPU and memory used by code location servers and individual runs. Follow [this guide](/todo) for details.
:::

First determine if you want to change the requested resource for everything in a code location, or for a specific job or asset.

<Tabs>

<TabItem value="code-location-resource" label="Resources for everything in a code location">

Modify the [`dagster_cloud.yaml` file](/todo) in your project's Git repository:

```yaml file=dagster_cloud.yaml
locations:
  - location_name: cloud-examples
    image: dagster/dagster-cloud-examples:latest
    code_source:
      package_name: dagster_cloud_examples
    container_context:
      k8s:
        server_k8s_config:
          container_config:
            resources:
              limits:
                cpu: 500m
                memory: 2560Mi
        run_k8s_config:
          container_config:
            resources:
              limits:
                cpu: 500m
                memory: 2560Mi
                nvidia.com/gpu: 1
```

The `server_k8s_config` section sets resources for the code location servers, which is where schedule and sensor evaluations occur.

The `runs_k8s_config` section sets resources for the individual run.

Requests are used by Kubernetes to determine which node to place a pod on, and limits are a strict upper bound on how many resources a pod can use while running. We recommend using both in most cases.

The units for CPU and memory resources are described [in this document](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#resource-units-in-kubernetes).

</TabItem>
<TabItem value="asset-resource" label="Resources for specific asset or job">

The default behavior in Dagster+ is to create one pod for a run. Each asset targeted by that run is executed in subprocess within the pod. Use a job tag to request resources for this pod, which in turn makes those resources available to the targeted assets.

<CodeExample
  filePath="dagster-plus/deployment/hybrid/agents/kubernetes/resource_request_job.py"
  language="python"
  title="Request resources for a job"
/>

Another option is to launch a pod for each asset by telling Dagster to use the Kubernetes job executor. In this case, you can specify resources for each individual asset.

<CodeExample
  filePath="dagster-plus/deployment/hybrid/agents/kubernetes/resource_request_asset.py"
  language="python"
  title="Request resources for an asset"
/>

</TabItem>

<TabItem value="pipes" label="Resources if using kubernetes pipes">

Dagster can launch and manage existing Docker images as Kubernetes jobs using the [Dagster kubernetes pipes integration](/integrations/libraries/kubernetes). To request resources for these jobs by supplying the appropriate Kubernetes pod spec.

<CodeExample
  filePath="dagster-plus/deployment/hybrid/agents/kubernetes/resource_request_pipes.py"
  language="python"
  title="Request resources for a k8s pipes asset"
/>

</TabItem>
</Tabs>
