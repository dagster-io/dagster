---
title: Existing VPC setup
sidebar_position: 200
---

:::note
This guide is applicable to Dagster+.
:::

In this guide, you'll set up and deploy an Amazon Elastic Container Service (ECS) agent in an existing VPC using CloudFormation. Amazon ECS agents are used to launch user code in ECS tasks.

Our CloudFormation template allows you to quickly spin up the ECS agent stack in an existing VPC. It also supports using a new or existing ECS cluster. The template code can be found [here](https://s3.amazonaws.com/dagster.cloud/cloudformation/ecs-agent.yaml). Refer to the [CloudFormation docs](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html) for more info about CloudFormation.

**For info about deploying an ECS agent in a new VPC**, check out the [ECS agents in new VPCs guide](/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/new-vpc).

## Prerequisites

To complete the steps in this guide, you'll need:

- **In Dagster+**:

  - **Your organization and deployment names.**
  - **Permissions in Dagster+ that allow you to manage agent tokens**. Refer to the [User permissions documentation](/dagster-plus/features/authentication-and-access-control/rbac/users) for more info.

- **In Amazon Web Services (AWS)**:
  - **An existing VPC with the following:**
    - **Subnets with access to the public internet**. Refer to the [AWS Work with VPCs guide](https://docs.aws.amazon.com/vpc/latest/userguide/working-with-vpcs.html) for more info.
    - **Enabled `enableDnsHostnames` and `enableDnsSupport` DNS attributes**. Refer to the [AWS DNS attributes documentation](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-dns.html#vpc-dns-support) for more info.
  - **Optional**: An existing ECS cluster with a [Fargate or EC2 capacity provider](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cluster-capacity-providers.html). The CloudFormation template will create a cluster for you if one isn't specified.

## Step 1: Generate a Dagster+ agent token

In this step, you'll generate a token for the Dagster+ agent. The Dagster+ agent will use this to authenticate to the agent API.

1. Sign in to your Dagster+ instance.
2. Click the **user menu (your icon) > Organization Settings**.
3. In the **Organization Settings** page, click the **Tokens** tab.
4. Click the **+ Create agent token** button.
5. After the token has been created, click **Reveal token**.

Keep the token somewhere handy - you'll need it to complete the setup.

## Step 2: Install the CloudFormation stack in AWS

Click the **Launch Stack** button to install the CloudFormation stack in your AWS account:

[<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png"/>](https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?templateURL=https://s3.amazonaws.com/dagster.cloud/cloudformation/ecs-agent.yaml)

**Note**: Creating the CloudFormation stack may take a few minutes. Refresh the [AWS console **Stacks** page](https://console.aws.amazon.com/cloudformation/home#/stacks) to check the status.

## Step 3: Configure the agent

After the stack is installed, you'll be prompted to configure it. In the ECS wizard, fill in the following fields:

- **Dagster+ Organization**: Enter the name of your Dagster+ organization.
- **Dagster+ Deployment**: Enter the name of the Dagster+ deployment you want to use. Leave this field empty if the agent will only serve Branch deployments.
- **Enable Branch Deployments**: Whether to have this agent serve your ephemeral [Branch deployments](/dagster-plus/features/ci-cd/branch-deployments). Only a single agent should have this setting enabled.
- **Agent Token**: Paste the agent token you generated in [Step 1](#step-1-generate-a-dagster-agent-token).
- **Deploy VPC**: The existing VPC to deploy the agent into.
- **Deploy VPC Subnet**: A public subnet of the existing VPC to deploy the agent into.
- **Existing ECS Cluster**: Optionally, the name of an existing ECS cluster to deploy the agent in. Leave blank to create a new cluster
- **Task Launch Type**: Optionally, the launch type to use for new tasks created by the agent (FARGATE or EC2). Defaults to FARGATE.

The page should look similar to the following image. In this example, our organization name is `hooli` and our deployment is `prod`:

![Example Configuration for the ECS Agent CloudFormation Template](/images/dagster-cloud/agents/aws-ecs-stack-wizard-existing.png)

After you've finished configuring the stack in AWS, you can view the agent in Dagster+. To do so, navigate to the **Status** page and click the **Agents** tab. You should see the agent running in the **Agent statuses** section:

![Instance Status](/images/dagster-cloud/agents/dagster-cloud-instance-status.png)

## Next steps

Now that you've got your agent running, what's next?

- **If you're getting Dagster+ set up**, the next step is to [add a code location](/dagster-plus/deployment/code-locations) using the agent.

- **If you're ready to load your Dagster code**, refer to the [Adding Code to Dagster+](/dagster-plus/deployment/code-locations) guide for more info.

If you need to upgrade your ECS agent's CloudFormation template, refer to the [upgrade guide](/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/upgrading-cloudformation) for more info.
