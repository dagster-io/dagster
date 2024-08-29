---
title: "Transitioning to Hybrid"
displayed_sidebar: "dagsterPlus"
sidebar_position: 50
---

After using a Dagster+ Serverless deployment, you may decide that you want to switch to a Hybrid deployment. A Hybrid deployment lets you use your own infrastructure to execute your code. You can switch from Serverless to Hybrid without loosing any of your execution history or metadata.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- **Organization Admin** permissions in your Dagster+ account.

</details>

## Step 1: Deactivate your Serverless agent
To deactivate the Serverless agent, navigate to the **Deployment -> Agents** page. Click the drop down arrow on the right of the page and select **Switch to hybrid**. This will deactivate the agent.

## Step 2: Create a Hybrid agent
In order to continue to use your Dagster+ account, you'll need to create a Hybrid agent to execute your code. There are many options for Hybrid agents. Follow the instructions for the agent of your choice to set up a Hybrid agent.

- **Amazon Web Services agents:**
    - [Amazon ECS agent in a new VPC](/dagster-plus/deployment/hybrid/agents/amazon-ecs-new-vpc)
    - [Amazon ECS agent in an existing VPC](/dagster-plus/deployment/hybrid/agents/amazon-ecs-existing-vpc)
- **[Docker agent](/dagster-plus/deployment/hybrid/agents/docker)**
- **[Kubernetes agent](/dagster-plus/deployment/hybrid/agents/kubernetes)**
- **[Local agent](/dagster-plus/deployment/hybrid/agents/local)**


## Step 3: Confirm successful setup

Once you have set up your Hybrid agent, navigate to the **Deployment -> Agents** page. You should see your new agent with the `RUNNING` status.
