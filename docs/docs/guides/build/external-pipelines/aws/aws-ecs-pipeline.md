---
title: Build pipelines with AWS ECS
description: "Learn to integrate Dagster Pipes with AWS ECS to launch external code from Dagster assets."
sidebar_position: 100
---

This article covers how to use [Dagster Pipes](/guides/build/external-pipelines/) with [AWS ECS](https://aws.amazon.com/ecs/).

The [dagster-aws](/api/python-api/libraries/dagster-aws) integration library provides the <PyObject section="libraries" object="pipes.PipesECSClient" module="dagster_aws" /> resource which can be used to launch AWS ECS tasks from Dagster assets and ops. Dagster can receive regular events like logs, asset checks, or asset materializations from jobs launched with this client. Using it requires minimal code changes on the task side.

<details>
  <summary>Prerequisites</summary>

    - **In the Dagster environment**, you'll need to:

    - Install the following packages:

        ```shell
        pip install dagster dagster-webserver dagster-aws
        ```

        Refer to the [Dagster installation guide](/getting-started/installation) for more info.

    - **Configure AWS authentication credentials.** If you don't have this set up already, refer to the [boto3 quickstart](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html).

    - **In AWS**, you'll need:

    - An existing AWS account
    - An AWS ECS task. To receive logs and events from a task container, it must have `"logDriver"` set to `"awslogs"` in `"logConfiguration"`.

</details>


## Step 1: Install the dagster-pipes module in your ECS environment

Install the `dagster-pipes` module in the image used for your ECS task. For example, you can install the dependency with `pip` in your image Dockerfile:

```Dockerfile
FROM python:3.11-slim

RUN python -m pip install dagster-pipes

# copy the task script
COPY . .
```

## Step 2: Add dagster-pipes to the ECS task script

Call `open_dagster_pipes` in the ECS task script to create a context that can be used to send messages to Dagster:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/ecs/task.py" />

:::tip

The metadata format shown above (`{"raw_value": value, "type": type}`) is part of Dagster Pipes' special syntax for specifying rich Dagster metadata. For a complete reference of all supported metadata types and their formats, see the [Dagster Pipes metadata reference](/guides/build/external-pipelines/using-dagster-pipes/reference#passing-rich-metadata-to-dagster).

:::

## Step 3: Create an asset using the PipesECSClient to launch the task

In the Dagster asset/op code, use the `PipesECSClient` resource to launch the job:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/ecs/dagster_code.py" startAfter="start_asset_marker" endBefore="=end_asset_marker" />

This will launch the AWS ECS task and wait until it reaches `"STOPPED"` status. If any of the tasks's containers fail, the Dagster process will raise an exception. If the Dagster process is interrupted while the task is still running, the task will be terminated.

## Step 4: Create Dagster definitions

Next, add the `PipesECSClient` resource to your project's <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/ecs/dagster_code.py" startAfter="start_definitions_marker" endBefore="=end_definitions_marker" />

Dagster will now be able to launch the AWS ECS task from the `ecs_pipes_asset` asset, and receive logs and events from the task. If using the default `message_reader` `PipesCloudwatchLogReader`, logs will be read from the Cloudwatch log group specified in the container `"logConfiguration"` field definition. Logs from all containers in the task will be read.
