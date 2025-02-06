---
title: Upgrading CloudFormation for an Amazon ECS agent
sidebar_label: Upgrading CloudFormation
sidebar_position: 500
---

:::note
This guide is applicable to Dagster+.
:::

In this guide, we'll show you how to upgrade an existing [Amazon Elastic Container Services (ECS) agent](/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/new-vpc)'s CloudFormation template.

**Note**: To complete the steps in this guide, you'll need [permissions in Amazon Web Services (AWS) that allow you to manage ECS agents](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-iam-awsmanpol.html).

1. Sign in to your AWS console.

2. Navigate to the deployed stack and click **Update**.

3. Select **Replace current template**. You can specify a specific Dagster+ version or upgrade to the latest template.

   **If you have deployed your agent into [its own VPC](/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/new-vpc), use the following:**

   To use the [latest template](https://s3.amazonaws.com/dagster.cloud/cloudformation/ecs-agent-vpc.yaml)

   To specify a [version](https://s3.amazonaws.com/dagster.cloud/cloudformation/ecs-agent-vpc-1-0-3.yaml)

   **If you are deploying the agent into an [existing VPC](/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/existing-vpc), use the following:**

   To use the [latest template](https://s3.amazonaws.com/dagster.cloud/cloudformation/ecs-agent.yaml)

   To specify a [version](https://s3.amazonaws.com/dagster.cloud/cloudformation/ecs-agent-1-0-3.yaml)

4. Proceed through the remaining steps in the wizard.

When finished, the agent will be re-deployed using the newest image and Dagster version.