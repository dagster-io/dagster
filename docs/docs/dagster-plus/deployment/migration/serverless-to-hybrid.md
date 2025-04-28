---
title: Migrating from Serverless to Hybrid
sidebar_label: Serverless to Hybrid
sidebar_position: 100
---

After utilizing a Dagster+ [Serverless](/dagster-plus/deployment/deployment-types/serverless) deployment, you may decide to leverage your own infrastructure to execute your code. Transitioning to a Hybrid deployment requires only a few steps and can be done without any loss of execution history or metadata, allowing you to maintain continuity and control over your operations.

:::warning
Transitioning from Serverless to Hybrid requires some downtime, as your Dagster+ deployment won't have an agent to execute user code.
:::

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- **Organization Admin** permissions in your Dagster+ account

</details>

## Step 1: Deactivate your Serverless agent

1. In the Dagster+ UI, navigate to the **Deployment > Agents** page.
2. Click the drop down arrow on the right of the page and select **Switch to Hybrid**.

![PRODUCT NOTE - this arrow drop down is pretty small and easy to confuse with the one in the row for the agent](/images/dagster-plus/deployment/switch-agent-to-hybrid.png)

It may take a few minutes for the agent to deactivate and be removed from the list of agents.

## Step 2: Create a Hybrid agent

Next, you'll need to create a Hybrid agent to execute your code. Follow the setup instructions for the agent of your choice:

- **[Amazon Web Services (AWS)](/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs)**, which launches user code as Amazon Elastic Container Service (ECS) tasks.
- **[Docker](/dagster-plus/deployment/deployment-types/hybrid/docker)**, which launches user code in Docker containers on your machine
- **[Kubernetes](/dagster-plus/deployment/deployment-types/hybrid/kubernetes)**, which launches user code on a Kubernetes cluster
- **[Local](/dagster-plus/deployment/deployment-types/hybrid/local)**, which launches user code in operating system subprocesses on your machine

## Step 3: Confirm successful setup

Once you've set up a Hybrid agent, navigate to the **Deployment > Agents** page in the UI. The new agent should display in the list with a `RUNNING` status:

![Screenshot](/images/dagster-plus/deployment/running-agent.png)

## Next steps

- Learn about the configuration options for [dagster.yaml](/guides/deploy/dagster-yaml)
