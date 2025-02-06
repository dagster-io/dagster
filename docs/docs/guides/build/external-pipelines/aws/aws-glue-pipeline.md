---
title: Build pipelines with AWS Glue
description: "Learn to integrate Dagster Pipes with AWS Glue to launch external code from Dagster assets."
sidebar_position: 500
---

# AWS Glue & Dagster Pipes

This article covers how to use [Dagster Pipes](/guides/build/external-pipelines/) with [AWS Glue](https://aws.amazon.com/glue/).

The [dagster-aws](/api/python-api/libraries/dagster-aws) integration library provides the <PyObject section="libraries" object="pipes.PipesGlueClient" module="dagster_aws" /> resource which can be used to launch AWS Glue jobs from Dagster assets and ops. Dagster can receive regular events like logs, asset checks, or asset materializations from jobs launched with this client. Using it requires minimal code changes on the job side.

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
    - An AWS Glue job with a Python 3.9+ runtime environment

</details>

## Step 1: Provide the dagster-pipes module in your Glue environment

Provide the `dagster-pipes` module to the AWS Glue job either by installing it in the Glue job environment or packaging it along with the job script.

## Step 2: Add dagster-pipes to the Glue job

Call `open_dagster_pipes` in the Glue job script to create a context that can be used to send messages to Dagster:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/glue/glue_script.py" />

:::tip

The metadata format shown above (`{"raw_value": value, "type": type}`) is part of Dagster Pipes' special syntax for specifying rich Dagster metadata. For a complete reference of all supported metadata types and their formats, see the [Dagster Pipes metadata reference](/guides/build/external-pipelines/using-dagster-pipes/reference#passing-rich-metadata-to-dagster).

:::

## Step 3: Add the PipesGlueClient to Dagster code

In the Dagster asset/op code, use the `PipesGlueClient` resource to launch the job:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/glue/dagster_code.py" startAfter="start_asset_marker" endBefore="end_asset_marker" />

This will launch the AWS Glue job and monitor its status until it either fails or succeeds. A job failure will also cause the Dagster run to fail with an exception.

## Step 4: Create Dagster definitions

Next, add the `PipesGlueClient` resource to your project's <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/glue/dagster_code.py" startAfter="start_definitions_marker" endBefore="end_definitions_marker" />

Dagster will now be able to launch the AWS Glue job from the `glue_pipes_asset` asset.

By default, the client uses the CloudWatch log stream (`.../output/<job-run-id>`) created by the Glue job to receive Dagster events. The client will also forward the stream to `stdout`.

To customize this behavior, the client can be configured to use <PyObject section="libraries" object="pipes.PipesS3MessageReader" module="dagster_aws" />, and the Glue job to use <PyObject section="libraries" object="PipesS3MessageWriter" module="dagster_pipes" /> .
