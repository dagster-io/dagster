---
title: Running multiple agents
sidebar_position: 60
sidebar_label: Multiple agents
---

:::note
This guide is applicable to Dagster+.
:::

Each Dagster+ full deployment (e.g., `prod`) needs to have at least one agent running. A single agent is adequate for many use cases, but you may want to run multiple agents to provide redundancy if a single agent goes down.

---

## Running multiple agents in the same environment

To run multiple agents in the same environment (e.g., multiple Kubernetes agents in the same namespace), you can set the number of replicas in the configuration for your particular agent type:

<Tabs groupId="same environment">
<TabItem value="docker" label="Docker">

### In Docker

In Docker, you can set the number of replicas for a service in the `docker-compose.yaml` file if the deployment mode is set to `replicated` (which is the default):

```yaml
services:
  dagster-cloud-agent:
    ...
    deploy:
      mode: replicated
      replicas: 2
```

</TabItem>
<TabItem value="Kubernetes" label="Kubernetes">

### In Kubernetes

In Kubernetes, the number of replicas is set in the Helm chart. You can set the number of replicas in the Helm command:

```shell
helm upgrade \
    ...
    --set replicas=2
```

or if using a `values.yaml` file:

```yaml
dagsterCloudAgent:
  ...
  replicas: 2
```

</TabItem>
<TabItem value="Amazon ECS" label="Amazon ECS">

### In Amazon ECS

In Amazon ECS, the number of replicas can be set via the CloudFormation template:

```yaml
DagsterCloudAgent:
  Type: AWS::ECS::Service
  Properties:
    ...
    DesiredCount: 2
```

If using the CloudFormation template provided by Dagster, the number of replicas can be set via the `NumReplicas` parameter in the Amazon Web Services (AWS) UI.

</TabItem>
</Tabs>

---

## Running multiple agents in different environments

To run multiple agents in an environment where each agent can not access the others' resources (for example, multiple Kubernetes namespaces or different clusters), enable the `isolated_agents` option. This is supported for all agent types.
<Tabs groupId="multipleAgentsDifferentEnvironment">
<TabItem value="Docker" label="Docker">

### In Docker

Add the following to the `dagster.yaml` file:

```yaml
isolated_agents:
  enabled: true

dagster_cloud_api:
  # <your other config>
  agent_label: "My agent" # optional
```

</TabItem>
<TabItem value="Kubernetes" label="Kubernetes">

### In Kubernetes

Add the following options to your Helm command:

```shell
helm upgrade \
    ...
    --set isolatedAgents.enabled=true \
    --set dagsterCloud.agentLabel="My agent" # optional, only supported on 0.13.14 and later
```

Or if you're using a `values.yaml` file:

```yaml
isolatedAgents:
  enabled: true

dagsterCloud:
  agentLabel: "My agent" # optional, only supported on 0.13.14 and later
```

</TabItem>
<TabItem value="Amazon ECS" label="Amazon ECS">

### In Amazon ECS

The `isolated_agents` option can be set as per-deployment configuration on the `dagster.yaml` file used by your agent. See the [ECS configuration reference](/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/configuration-reference) guide for more information.

</TabItem>
</Tabs>
---

## Routing requests to specific agents

:::note
Agent queues are a Dagster+ Pro feature.
:::

Every Dagster+ agent serves requests from one or more queues. By default, requests for each code location are placed on a default queue and your agent will read requests only from that default queue.

In some cases, you might want to route requests for certain code locations to specific agents. For example, routing requests for one code location to an agent running in an on-premise data center, but then routing requests for all other code locations to an agent running in AWS.

To route requests for a code location to a specific agent, annotate the code locations with the name of a custom queue and configure an agent to serve only requests for that queue.

### Step 1: Define an agent queue for the code location

First, set an agent queue for the code location in your [`dagster_cloud.yaml`](/dagster-plus/deployment/code-locations/dagster-cloud-yaml):

```yaml
# dagster_cloud.yaml

locations:
  - location_name: data-eng-pipeline
    code_source:
      package_name: quickstart_etl
    executable_path: venvs/path/to/dataengineering_spark_team/bin/python
    agent_queue: special-queue
```

### Step 2: Configure an agent to handle the agent queue

Next, configure an agent to handle your agent queue.
<Tabs groupId="agentQueue">
<TabItem value="Docker" label="Docker">

#### In Docker

Add the following to your project's [`dagster.yaml`](/todo.md) file:
{/* [lDagster Instance](https://docs.dagster.io/deployment/dagster-instance) */}

```yaml
agent_queues:
  include_default_queue: True # Continue to handle requests for code locations that aren't annotated with a specific queue
  additional_queues:
    - special-queue
```

</TabItem>
<TabItem value="Kubernetes" name="Kubernetes">

#### In Kubernetes

Add the following options to your Helm command:

```shell
helm upgrade \
    ...
    --set dagsterCloud.agentQueues.additionalQueues={"special-queue"}
```

Or if you're using a `values.yaml` file:

```yaml
dagsterCloud:
  agentQueues:
    # Continue to handle requests for code locations that aren't
    # assigned to a specific agent queue
    includeDefaultQueue: true
    additionalQueues:
      - special-queue
```

</TabItem>
<TabItem value="Amazon ECS" label="Amazon ECS">

#### In Amazon ECS

Modify your ECS Cloud Formation template to add the following configuration to the `config.yaml` passed to the agent:

```yaml
agent_queues:
  # Continue to handle requests for code locations that aren't
  # assigned to a specific agent queue
  include_default_queue: true
  additional_queues:
    - special-queue
```

</TabItem>
</Tabs>