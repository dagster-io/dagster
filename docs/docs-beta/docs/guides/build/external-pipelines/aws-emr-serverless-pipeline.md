---
title: Build pipelines with AWS EMR Serverless
description: "Learn to integrate Dagster Pipes with AWS EMR Serverless to launch external code from Dagster assets."
sidebar_position: 300
---

This article covers how to use [Dagster Pipes](/guides/build/external-pipelines/) with [AWS EMR Serverless](https://aws.amazon.com/emr-serverless/).

The [dagster-aws](/api/python-api/libraries/dagster-aws) integration library provides the <PyObject section="libraries" object="pipes.PipesEMRServerlessClient" module="dagster_aws" /> resource, which can be used to launch AWS EMR Serverless jobs from Dagster assets and ops. Dagster can receive regular events such as logs, asset checks, or asset materializations from jobs launched with this client. Using it requires minimal code changes to your EMR jobs.


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
    - An AWS EMR Serverless job. AWS CloudWatch logging has to be enabled in order to receive logs from the job:

    ```json
    {
        "monitoringConfiguration": {
        "cloudWatchLoggingConfiguration": { "enabled": true }
        }
    }
    ```

</details>

## Step 1: Install the dagster-pipes module in your EMR Serverless environment

There are a [few options](https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/using-python-libraries.html) available for shipping Python packages to a PySpark job. For example, [install it in your Docker image](https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/application-custom-image.html):

Install the `dagster-pipes` module in the image used for your EMR job. For example, you can install the dependency with `pip` in your image Dockerfile:

```Dockerfile
# start from EMR image
FROM public.ecr.aws/emr-serverless/spark/emr-7.2.0:latest

USER root

RUN python -m pip install dagster-pipes

# copy the job script
COPY . .

USER hadoop
```

## Step 2: Add dagster-pipes to the EMR Serverless job script

Call `open_dagster_pipes` in the EMR Serverless script to create a context that can be used to send messages to Dagster:

```python file=/guides/dagster/dagster_pipes/emr-serverless/script.py
from dagster_pipes import open_dagster_pipes
from pyspark.sql import SparkSession


def main():
    with open_dagster_pipes() as pipes:
        pipes.log.info("Hello from AWS EMR Serverless!")

        spark = SparkSession.builder.appName("HelloWorld").getOrCreate()

        df = spark.createDataFrame(
            [(1, "Alice", 34), (2, "Bob", 45), (3, "Charlie", 56)],
            ["id", "name", "age"],
        )

        # calculate a really important statistic
        avg_age = float(df.agg({"age": "avg"}).collect()[0][0])

        # attach it to the asset materialization in Dagster
        pipes.report_asset_materialization(
            metadata={"average_age": {"raw_value": avg_age, "type": "float"}},
            data_version="alpha",
        )

        spark.stop()


if __name__ == "__main__":
    main()
```

## Step 3: Create an asset using the PipesEMRServerlessClient to launch the job

In the Dagster asset/op code, use the `PipesEMRServerlessClient` resource to launch the job:

```python file=/guides/dagster/dagster_pipes/emr-serverless/dagster_code.py startafter=start_asset_marker endbefore=end_asset_marker
import os

import boto3
from dagster_aws.pipes import PipesEMRServerlessClient

from dagster import AssetExecutionContext, asset


@asset
def emr_serverless_asset(
    context: AssetExecutionContext,
    pipes_emr_serverless_client: PipesEMRServerlessClient,
):
    return pipes_emr_serverless_client.run(
        context=context,
        start_job_run_params={
            "applicationId": "<app-id>",
            "executionRoleArn": "<emr-role>",
            "clientToken": context.run_id,  # idempotency identifier for the job run
            "configurationOverrides": {
                "monitoringConfiguration": {
                    "cloudWatchLoggingConfiguration": {"enabled": True}
                }
            },
        },
    ).get_results()
```

This will launch the AWS EMR Serverless job and wait for it completion. If the job fails, the Dagster process will raise an exception. If the Dagster process is interrupted while the job is still running, the job will be terminated.

## Step 4: Create Dagster definitions

Next, add the `PipesEMRServerlessClient` resource to your project's <PyObject section="definitions" module="dagster" object="Definitions" /> object:

```python file=/guides/dagster/dagster_pipes/emr-serverless/dagster_code.py startafter=start_definitions_marker endbefore=end_definitions_marker
from dagster import Definitions  # noqa


defs = Definitions(
    assets=[emr_serverless_asset],
    resources={"pipes_emr_serverless_client": PipesEMRServerlessClient()},
)
```

Dagster will now be able to launch the AWS EMR Serverless task from the `emr_serverless_asset` asset, and receive logs and events from the job. If using the default `message_reader` `PipesCloudwatchLogReader`, driver logs will be forwarded to the Dagster process.
