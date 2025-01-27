---
title: Manual provision setup
sidebar_position: 300
---

:::note
This guide is applicable to Dagster+.
:::

In this guide, you'll manually set up and deploy an Amazon Elastic Container Service (ECS) agent. Amazon ECS agents are used to launch user code in ECS tasks.

This method of setting up an Amazon ECS agent is a good option if you're comfortable with infrastructure management and want to fully define your agent.

## Prerequisites

To complete the steps in this guide, you'll need:

- **In Dagster+**:

  - **Your organization and deployment names.**
  - **Permissions in Dagster+ that allow you to manage agent tokens**. Refer to the [User permissions documentation](/dagster-plus/features/authentication-and-access-control/rbac/users) for more info.

- **Permissions in Amazon Web Services (AWS) that allow you to:**

  - Create and configure ECS services.
  - Create and configure IAM roles.

- **Familiarity with infrastructure management and tooling.**

## Step 1: Generate a Dagster+ agent token

In this step, you'll generate a token for the Dagster+ agent. The Dagster+ agent will use this to authenticate to the agent API.

1. Sign in to your Dagster+ instance.
2. Click the **user menu (your icon) > Organization Settings**.
3. In the **Organization Settings** page, click the **Tokens** tab.
4. Click the **+ Create agent token** button.
5. After the token has been created, click **Reveal token**.

Keep the token somewhere handy - you'll need it to complete the setup.

## Step 2: Create ECS IAM roles

To successfully run your ECS agent, you'll need to have the following IAM roles in your AWS account:

- [**Task execution IAM role**](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html) - This role allows ECS to interact with AWS resources on your behalf, such as pulling an image from ECR or pushing logs to CloudWatch.

  Amazon publishes a managed policy called `AmazonECSTaskExecutionRolePolicy` with the required permissions. Refer to the [AWS docs](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html#create-task-execution-role) for more info about creating this role.

- [**Task IAM role**](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html) - This role allows the containers running in the ECS task to interact with AWS.

  When creating this role, include the permissions required to describe and launch ECS tasks. For example:

  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "",
        "Effect": "Allow",
        "Action": [
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeRouteTables",
          "ecs:CreateService",
          "ecs:DeleteService",
          "ecs:DescribeServices",
          "ecs:DescribeTaskDefinition",
          "ecs:DescribeTasks",
          "ecs:ListAccountSettings",
          "ecs:ListServices",
          "ecs:ListTagsForResource",
          "ecs:ListTasks",
          "ecs:RegisterTaskDefinition",
          "ecs:RunTask",
          "ecs:StopTask",
          "ecs:TagResource",
          "ecs:UpdateService",
          "iam:PassRole",
          "logs:GetLogEvents",
          "secretsmanager:DescribeSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:ListSecrets",
          "servicediscovery:CreateService",
          "servicediscovery:DeleteService",
          "servicediscovery:ListServices",
          "servicediscovery:GetNamespace",
          "servicediscovery:ListTagsForResource",
          "servicediscovery:TagResource"
        ],
        "Resource": "*"
      }
    ]
  }
  ```

  You can also include any additional permissions required to run your ops, such as permissions to interact with an S3 bucket.

**Note**: Both roles must include a trust relationship that allows ECS to use them:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Step 3: Create an ECS service

1. Create an ECS service to run the agent. You can do this [in the Amazon ECS console](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/create-service-console-v2.html) or [via the CreateService API](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_CreateService.html).

   Use the [official dagster/dagster-cloud-agent image](https://hub.docker.com/r/dagster/dagster-cloud-agent) as the service's **Task definition**. This image can be used as-is or as a base layer for your own image.

2. Add a configured `dagster.yaml` file to your container. You can do this by:

   - Building it into your image
   - Echoing it to a file in your task definition's command **before starting the agent**

   Refer to the [ECS configuration reference](/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/configuration-reference#per-deployment-configuration) for more info about the required fields.

## Next steps

Now that you've got your agent running, what's next?

- **If you're getting Dagster+ set up**, the next step is to [add a code location](/dagster-plus/deployment/code-locations) using the agent.

- **If you're ready to load your Dagster code**, refer to the [Adding Code to Dagster+](/dagster-plus/deployment/code-locations) guide for more info.
