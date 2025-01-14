---
title: Build pipelines with AWS ECS
description: "Learn to integrate Dagster Pipes with AWS ECS to launch external code from Dagster assets."
sidebar_position: 200
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

```python file=/guides/dagster/dagster_pipes/ecs/task.py
from dagster_pipes import (
    PipesEnvVarParamsLoader,
    PipesS3ContextLoader,
    open_dagster_pipes,
)


def main():
    with open_dagster_pipes() as pipes:
        pipes.log.info("Hello from AWS ECS task!")
        pipes.report_asset_materialization(
            metadata={"some_metric": {"raw_value": 0, "type": "int"}},
            data_version="alpha",
        )


if __name__ == "__main__":
    main()
```

## Step 3: Create an asset using the PipesECSClient to launch the task

In the Dagster asset/op code, use the `PipesECSClient` resource to launch the job:

```python file=/guides/dagster/dagster_pipes/ecs/dagster_code.py startafter=start_asset_marker endbefore=end_asset_marker
import os

# dagster_glue_pipes.py
import boto3
from dagster_aws.pipes import PipesECSClient
from docutils.nodes import entry

from dagster import AssetExecutionContext, asset


@asset
def ecs_pipes_asset(context: AssetExecutionContext, pipes_ecs_client: PipesECSClient):
    return pipes_ecs_client.run(
        context=context,
        run_task_params={
            "taskDefinition": "my-task",
            "count": 1,
        },
    ).get_materialize_result()
```

This will launch the AWS ECS task and wait until it reaches `"STOPPED"` status. If any of the tasks's containers fail, the Dagster process will raise an exception. If the Dagster process is interrupted while the task is still running, the task will be terminated.

## Step 4: Create Dagster definitions

Next, add the `PipesECSClient` resource to your project's <PyObject section="definitions" module="dagster" object="Definitions" /> object:

```python file=/guides/dagster/dagster_pipes/ecs/dagster_code.py startafter=start_definitions_marker endbefore=end_definitions_marker
from dagster import Definitions  # noqa
from dagster_aws.pipes import PipesS3MessageReader


defs = Definitions(
    assets=[ecs_pipes_asset],
    resources={"pipes_ecs_client": PipesECSClient()},
)
```

Dagster will now be able to launch the AWS ECS task from the `ecs_pipes_asset` asset, and receive logs and events from the task. If using the default `message_reader` `PipesCloudwatchLogReader`, logs will be read from the Cloudwatch log group specified in the container `"logConfiguration"` field definition. Logs from all containers in the task will be read.
