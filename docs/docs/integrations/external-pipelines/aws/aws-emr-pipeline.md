---
title: AWS EMR pipelines
description: 'Learn to integrate Dagster Pipes with AWS EMR to launch external code from Dagster assets.'
sidebar_position: 300
---

import ScaffoldProject from '@site/docs/partials/\_ScaffoldProject.md';

This article covers how to use [Dagster Pipes](/integrations/external-pipelines) with [AWS EMR](https://aws.amazon.com/emr).

The [dagster-aws](/integrations/libraries/aws) integration library provides the <PyObject section="libraries" integration="aws" object="pipes.PipesEMRClient" module="dagster_aws" /> resource, which can be used to launch AWS EMR jobs from Dagster assets and ops. Dagster can receive regular events such as logs, asset checks, or asset materializations from jobs launched with this client. Using it requires minimal code changes to your EMR jobs.

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
- In AWS, you'll need:
  - An existing AWS account
  - Prepared infrastructure such as S3 buckets, IAM roles, and other resources required for your EMR job

## Step 1: Install the dagster-pipes module in your EMR environment

Choose one of the [options](https://spark.apache.org/docs/latest/api/python/user_guide/python_packaging.html#python-package-management) to install `dagster-pipes` in the EMR environment.

For example, this `Dockerfile` can be used to package all required dependencies into a single [PEX](https://docs.pex-tool.org) file (in practice, the most straightforward way to package Python dependencies for EMR jobs):

```Dockerfile file=/guides/dagster/dagster_pipes/emr/Dockerfile
# this Dockerfile can be used to create a venv archive for PySpark on AWS EMR

FROM amazonlinux:2 AS builder

RUN yum install -y python3

WORKDIR /build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV VIRTUAL_ENV=/build/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN uv python install --python-preference only-managed 3.9.16 && uv python pin 3.9.16

RUN uv venv .venv

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install pex dagster-pipes boto3 pyspark

RUN pex dagster-pipes boto3 pyspark -o /output/venv.pex && chmod +x /output/venv.pex

# test imports
RUN /output/venv.pex -c "import dagster_pipes, pyspark, boto3;"

FROM scratch AS export

COPY --from=builder /output/venv.pex /venv.pex
```

The build can be launched with:

```shell
DOCKER_BUILDKIT=1 docker build --output type=local,dest=./output .
```

Then, upload the produced `output/venv.pix` file to an S3 bucket:

```shell
aws s3 cp output/venv.pex s3://your-bucket/venv.pex
```

Finally, use the `--files` and `spark.pyspark.python` options to specify the path to the PEX file in the `spark-submit` command:

```shell
spark-submit ... --files s3://your-bucket/venv.pex --conf spark.pyspark.python=./venv.pex
```

## Step 2: Add dagster-pipes to the EMR job script

Call `open_dagster_pipes` in the EMR script to create a context that can be used to send messages to Dagster:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/emr/script.py" />

:::tip

The metadata format shown above (`{"raw_value": value, "type": type}`) is part of Dagster Pipes' special syntax for specifying rich Dagster metadata. For a complete reference of all supported metadata types and their formats, see the [Dagster Pipes metadata reference](/integrations/external-pipelines/using-dagster-pipes/reference#passing-rich-metadata-to-dagster).

:::

## Step 3: Create an asset using the PipesEMRClient to launch the job

import ScaffoldAsset from '@site/docs/partials/\_ScaffoldAsset.md';

<ScaffoldAsset />

In the Dagster asset/op code, use the `PipesEMRClient` resource to launch the job:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/emr/dagster_code.py"
  title="src/<project_name>/defs/assets.py"
/>

This will launch the AWS EMR job and wait for it completion. If the job fails, the Dagster process will raise an exception. If the Dagster process is interrupted while the job is still running, the job will be terminated.

EMR application steps `stdout` and `stderr` will be forwarded to the Dagster process.

## Step 4: Create Dagster definitions

import ScaffoldResource from '@site/docs/partials/\_ScaffoldResource.md';

<ScaffoldResource />

Next, add the `PipesEMRClient` resource to your project's <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/emr/resources.py"
  title="src/<project_name>/defs/resources.py"
/>

Dagster will now be able to launch the AWS EMR job from the `emr_asset` asset, and receive logs and events from the job.
