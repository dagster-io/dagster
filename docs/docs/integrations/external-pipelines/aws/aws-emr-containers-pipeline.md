---
title: AWS EMR on EKS pipelines
description: 'Learn to integrate Dagster Pipes with AWS EMR Containers to launch external code from Dagster assets.'
sidebar_position: 200
---

import Preview from '@site/docs/partials/\_Preview.md';
import ScaffoldProject from '@site/docs/partials/\_ScaffoldProject.md';

<Preview />

This tutorial gives a short overview on how to use [Dagster Pipes](/integrations/external-pipelines) with [AWS EMR on EKS](https://aws.amazon.com/emr/features/eks) (the corresponding AWS API is called `emr-containers`).

The [dagster-aws](/integrations/libraries/aws) integration library provides the <PyObject section="libraries" integration="aws" object="pipes.PipesEMRContainersClient" module="dagster_aws" /> resource, which can be used to launch EMR jobs from Dagster assets and ops. Dagster can receive regular events such as logs, asset checks, or asset materializations from jobs launched with this client. Using it requires minimal code changes to your EMR jobs.

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

- Configure AWS authentication credentials: If you don't have these set up already, refer to the [boto3 quickstart](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html).
- In AWS:
  - An existing AWS account
  - An [EMR Virtual Cluster](https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/virtual-cluster.html) set up

## Step 1: Install the dagster-pipes module in your EMR environment

There are [a few options](https://aws.github.io/aws-emr-containers-best-practices/submit-applications/docs/spark/pyspark/#python-code-with-python-dependencies) for deploying Python code & dependencies for PySpark jobs. In this tutorial, we are going to build a custom Docker image for this purpose.

Install `dagster-pipes`, `dagster-aws` and `boto3` Python packages in your image:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/emr-containers/Dockerfile" />

:::note

It's also recommended to upgrade the default Python version included in the base EMR image (as it has been done in the `Dockerfile` above)

:::

We copy the EMR job script (`script.py`) to the image in the last step.

## Step 2: Invoke dagster-pipes in the EMR job script

Call `open_dagster_pipes` in the EMR script to create a context that can be used to send messages to Dagster:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/emr-containers/script.py" />

:::note

It's best to use the `PipesS3MessageWriter` with EMR on EKS, because this message writer has the ability to capture the Spark driver logs and send them to Dagster.

:::

## Step 3: Create an asset using the PipesEMRcontainersClient to launch the job

import ScaffoldAsset from '@site/docs/partials/\_ScaffoldAsset.md';

<ScaffoldAsset />

In the Dagster asset/op code, use the `PipesEMRcontainersClient` resource to launch the job:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/emr-containers/dagster_code.py"
  title="src/<project_name>/defs/assets.py"
/>

:::note

Setting `include_stdio_in_messages` to `True` in the `PipesS3MessageReader` will allow the driver logs to be forwarded to the Dagster process.

:::

Materializing this asset will launch the AWS on EKS job and wait for it to complete. If the job fails, the Dagster process will raise an exception. If the Dagster process is interrupted while the job is still running, the job will be terminated.

## Step 4: Create Dagster definitions

import ScaffoldResource from '@site/docs/partials/\_ScaffoldResource.md';

<ScaffoldResource />

Next, add the `PipesEMRContainersClient` resource to your project's <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/emr-containers/resources.py"
  title="src/<project_name>/defs/resources.py"
/>

Dagster will now be able to launch the AWS EMR Containers job from the `emr_containers_asset` asset, and receive logs and events from the job. If `include_stdio_in_messages` is set to `True`, the logs will be forwarded to the Dagster process.
