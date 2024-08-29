---
title: "Transitioning to Hybrid"
displayed_sidebar: "dagsterPlus"
sidebar_position: 50
---

After using a Dagster+ Serverless deployment, you may decide that you want to switch to a Hybrid deployment. A Hybrid deployment lets you use your own infrastructure to execute your code. You can switch from Serverless to Hybrid without loosing any of your execution history or metadata.

:::warning
Transitioning from Serverless to Hybrid requires some downtime when your Dagster+ deployment won't have an agent to execute user code.
:::

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- **Organization Admin** permissions in your Dagster+ account.

</details>

## Step 1: Deactivate your Serverless agent
To deactivate the Serverless agent, navigate to the **Deployment -> Agents** page. Click the drop down arrow on the right of the page and select **Switch to hybrid**. It may take a few minutes for the agent to deactivate and be removed from the list of agents.

PRODUCT NOTE - this arrow drop down is pretty small and easy to confuse with the one in the row for the agent

## Step 2: Create a Hybrid agent
Next, you'll need to create a Hybrid agent to execute your code. There are several options for Hybrid agents. Follow the instructions for the agent of your choice to set up a Hybrid agent.

- **Amazon Web Services agents**. AWS agents launch user code as Amazon Elastic Container Service (ECS) tasks.
    - [Amazon ECS agent in a new VPC](/dagster-plus/deployment/hybrid/agents/amazon-ecs-new-vpc)
    - [Amazon ECS agent in an existing VPC](/dagster-plus/deployment/hybrid/agents/amazon-ecs-existing-vpc)
- **[Docker agent](/dagster-plus/deployment/hybrid/agents/docker)**. Docker agents launch user code in Docker containers on your machine.
- **[Kubernetes agent](/dagster-plus/deployment/hybrid/agents/kubernetes)**. Kubernetes agents launch user code on a Kubernetes cluster.
- **[Local agent](/dagster-plus/deployment/hybrid/agents/local)**. Local agents launch user code in operating system subprocesses on your machine.


## Step 3: Confirm successful setup

Once you have set up your Hybrid agent, navigate to the **Deployment -> Agents** page. You should see your new agent with the `RUNNING` status.

SCREENSHOT

## Next steps

- See all of the configuration options for [dagster.yaml](/todo).
