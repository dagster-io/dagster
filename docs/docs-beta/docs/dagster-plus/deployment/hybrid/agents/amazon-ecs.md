---
title: "Running Dagster+ agents on Amazon ECS"
displayed_sidebar: "dagsterPlus"
sidebar_position: 11
sidebar_label: "Amazon ECS"
---

# Running Dagster+ agents on Amazon ECS

This page provides instructions for running the [Dagster+ agent](dagster-plus/getting-started/whats-dagster-plus#Agents) on an [Amazon ECS](https://aws.amazon.com/ecs/) cluster.

## Installation

You can install the Dagster+ agent using one of our [CloudFormation](https://aws.amazon.com/cloudformation/) templates.

To install into a new [VPC](https://aws.amazon.com/vpc/):

[<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png"/>](https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?templateURL=https://s3.amazonaws.com/dagster.cloud/cloudformation/ecs-agent.yaml)

For more flexibility, you can install into an existing VPC:

[<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png"/>](https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?templateURL=https://s3.amazonaws.com/dagster.cloud/cloudformation/ecs-agent-vpc.yaml)

For even more flexibility, you can edit these templates or use them as a guide for managing your own infrastructure.
