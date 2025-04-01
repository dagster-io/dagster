---
title: Build pipelines with AWS EMR Serverless
description: "Learn to integrate Dagster Pipes with AWS EMR Serverless to launch external code from Dagster assets."
sidebar_position: 400
---

This article covers how to use [Dagster Pipes](/guides/build/external-pipelines/) with [AWS EMR Serverless](https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/getting-started.html).

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

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/emr-serverless/script.py" />

:::tip

The metadata format shown above (`{"raw_value": value, "type": type}`) is part of Dagster Pipes' special syntax for specifying rich Dagster metadata. For a complete reference of all supported metadata types and their formats, see the [Dagster Pipes metadata reference](/guides/build/external-pipelines/using-dagster-pipes/reference#passing-rich-metadata-to-dagster).

:::

## Step 3: Create an asset using the PipesEMRServerlessClient to launch the job

In the Dagster asset/op code, use the `PipesEMRServerlessClient` resource to launch the job:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/emr-serverless/dagster_code.py" startAfter="start_asset_marker" endBefore="=end_asset_marker" />

This will launch the AWS EMR Serverless job and wait for it completion. If the job fails, the Dagster process will raise an exception. If the Dagster process is interrupted while the job is still running, the job will be terminated.

## Step 4: Create Dagster definitions

Next, add the `PipesEMRServerlessClient` resource to your project's <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/emr-serverless/dagster_code.py" startAfter="start_definitions_marker" endBefore="=end_definitions_marker"/>

Dagster will now be able to launch the AWS EMR Serverless task from the `emr_serverless_asset` asset, and receive logs and events from the job. If using the default `message_reader` `PipesCloudwatchLogReader`, driver logs will be forwarded to the Dagster process.
