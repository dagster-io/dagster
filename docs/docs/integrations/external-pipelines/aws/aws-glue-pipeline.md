---
title: AWS Glue pipelines
description: 'Learn to integrate Dagster Pipes with AWS Glue to launch external code from Dagster assets.'
sidebar_position: 500
---

import ScaffoldProject from '@site/docs/partials/\_ScaffoldProject.md';

# AWS Glue & Dagster Pipes

This article covers how to use [Dagster Pipes](/integrations/external-pipelines) with [AWS Glue](https://aws.amazon.com/glue).

The [dagster-aws](/integrations/libraries/aws) integration library provides the <PyObject section="libraries" integration="aws" object="pipes.PipesGlueClient" module="dagster_aws" /> resource which can be used to launch AWS Glue jobs from Dagster assets and ops. Dagster can receive regular events like logs, asset checks, or asset materializations from jobs launched with this client. Using it requires minimal code changes on the job side.

## Prerequisites

To run the examples, you'll need to:

- Create a new Dagster project:
  <ScaffoldProject />
- Install the necessary Python libraries:

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      Install the required dependencies:

         ```shell
         uv add dagster-aws
         ```

   </TabItem>

   <TabItem value="pip" label="pip">
      Install the required dependencies:

         ```shell
         pip install dagster-aws
         ```

   </TabItem>
</Tabs>

- Configure AWS authentication credentials. If you don't have this set up already, refer to the [boto3 quickstart](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html).
- **In AWS**, you'll need:
  - An existing AWS account
  - An AWS Glue job with a Python 3.9+ runtime environment

## Step 1: Provide the dagster-pipes module in your Glue environment

Provide the `dagster-pipes` module to the AWS Glue job either by installing it in the Glue job environment or packaging it along with the job script.

## Step 2: Add dagster-pipes to the Glue job

Call `open_dagster_pipes` in the Glue job script to create a context that can be used to send messages to Dagster:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/glue/glue_script.py" />

:::tip

The metadata format shown above (`{"raw_value": value, "type": type}`) is part of Dagster Pipes' special syntax for specifying rich Dagster metadata. For a complete reference of all supported metadata types and their formats, see the [Dagster Pipes metadata reference](/integrations/external-pipelines/using-dagster-pipes/reference#passing-rich-metadata-to-dagster).

:::

## Step 3: Add the PipesGlueClient to Dagster code

import ScaffoldAsset from '@site/docs/partials/\_ScaffoldAsset.md';

<ScaffoldAsset />

In the Dagster asset/op code, use the `PipesGlueClient` resource to launch the job:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/glue/dagster_code.py"
  title="src/<project_name>/defs/assets.py"
/>

This will launch the AWS Glue job and monitor its status until it either fails or succeeds. A job failure will also cause the Dagster run to fail with an exception.

## Step 4: Create Dagster definitions

import ScaffoldResource from '@site/docs/partials/\_ScaffoldResource.md';

<ScaffoldResource />

Next, add the `PipesGlueClient` resource to your project's <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/glue/resources.py"
  title="src/<project_name>/defs/resources.py"
/>

Dagster will now be able to launch the AWS Glue job from the `glue_pipes_asset` asset.

By default, the client uses the CloudWatch log stream (`.../output/<job-run-id>`) created by the Glue job to receive Dagster events. The client will also forward the stream to `stdout`.

To customize this behavior, the client can be configured to use <PyObject section="libraries" integration="aws" object="pipes.PipesS3MessageReader" module="dagster_aws" />, and the Glue job to use <PyObject section="libraries" integration="pipes" object="PipesS3MessageWriter" module="dagster_pipes" /> .
