---
description: Set up and deploy a Dagster+ Amazon ECS agent in a new VPC using CloudFormation
  with Dagster+.
sidebar_position: 100
title: New VPC setup
---

:::note
This guide is applicable to Dagster+.
:::

In this guide, you'll set up and deploy an Amazon Elastic Container Service (ECS) agent in a new VPC using CloudFormation. Amazon ECS agents are used to launch user code in ECS tasks.

Our CloudFormation templates allow you to quickly spin up the ECS agent stack from scratch in your AWS account.

1. [New VPC template with public subnets](https://s3.amazonaws.com/dagster.cloud/cloudformation/ecs-agent-vpc.yaml): this is the basic template for deploying the ECS agent in a new VPC. It creates a new VPC with public subnets and an ECS cluster to run the Dagster+ agent and tasks. This is the simplest setup.
2. [New VPC template with private subnets](https://s3.amazonaws.com/dagster.cloud/cloudformation/ecs-agent-vpc-private.yaml): a more secure version of the above template. This template creates a new VPC with private subnets and NAT gateways to allow the Dagster tasks to run without direct exposure to the Internet, as well as more granular roles and security groups configuration.

Refer to the [CloudFormation docs](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html) for more info about CloudFormation.

**For info about deploying an ECS agent in an existing VPC**, check out the [ECS agents in existing VPCs guide](/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/existing-vpc).

## Prerequisites

To complete the steps in this guide, you'll need:

- **In Dagster+**:

  - **Your organization and deployment names.**
  - **Permissions in Dagster+ that allow you to manage agent tokens**. Refer to the [User permissions documentation](/dagster-plus/features/authentication-and-access-control/rbac/users) for more info.

- **In Amazon Web Services (AWS), you'll need an account**:

  - **Under its VPC quota limit in the region where you're spinning up the agent.** By default, AWS allows **five VPCs per region**. If you're already at your limit, refer to the [AWS VPC quotas documentation](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html) for info on requesting a quota increase.

  - **With an ECS service-linked IAM role**. This role is required to complete the setup in ECS. AWS will automatically create the role in your account the first time you create an ECS cluster in the console. However, the IAM role isn't automatically created when ECS clusters are created via CloudFormation.

    If your account doesn't have this IAM role, running the CloudFormation template may fail.

    If you haven't created an ECS cluster before, complete one of the following before proceeding:

    - Create one using the [first run wizard](https://console.aws.amazon.com/ecs/home#/firstRun), or
    - Create the IAM role using the [AWS CLI](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using-service-linked-roles.html#create-service-linked-role)

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

[<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png"/>](https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?templateURL=https://s3.amazonaws.com/dagster.cloud/cloudformation/ecs-agent-vpc.yaml)

**Note**: Creating the CloudFormation stack may take a few minutes. Refresh the [AWS console **Stacks** page](https://console.aws.amazon.com/cloudformation/home#/stacks) to check the status.

If the installation fails, verify that your AWS account [meets the requirements listed above](#prerequisites).

## Step 3: Configure the agent

After the stack is installed, you'll be prompted to configure it. In the ECS wizard, fill in the following fields:

- **Dagster+ Organization**: Enter the name of your Dagster+ organization.
- **Dagster+ Deployment**: Enter the name of the Dagster+ deployment you want to use. Leave this field empty if the agent will only serve Branch deployments.
- **Enable Branch Deployments**: Whether to have this agent serve your ephemeral [Branch deployments](/dagster-plus/features/ci-cd/branch-deployments). Only a single agent should have this setting enabled.
- **Agent Token**: Paste the agent token you generated in [Step 1](#step-1-generate-a-dagster-agent-token).

The page should look similar to the following image. In this example, our organization name is `hooli` and our deployment is `prod`:

![Example Configuration for the ECS Agent CloudFormation Template](/images/dagster-plus/deployment/agents/aws-ecs-stack-wizard-new.png)

After you've finished configuring the stack in AWS, you can view the agent in Dagster+. To do so, navigate to the **Status** page and click the **Agents** tab. You should see the agent running in the **Agent statuses** section:

![Instance Status](/images/dagster-plus/deployment/agents/dagster-cloud-instance-status.png)

## Next steps

Now that you've got your agent running, what's next?

- **If you're getting Dagster+ set up**, the next step is to [add a code location](/dagster-plus/deployment/code-locations) using the agent.

- **If you're ready to load your Dagster code**, refer to the [Adding Code to Dagster+](/dagster-plus/deployment/code-locations) guide for more info.

If you need to upgrade your ECS agent's CloudFormation template, refer to the [upgrade guide](/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/upgrading-cloudformation) for more info.
