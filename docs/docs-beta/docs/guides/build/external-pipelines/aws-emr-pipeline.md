---
title: Build pipelines with AWS EMR
description: "Learn to integrate Dagster Pipes with AWS EMR to launch external code from Dagster assets."
sidebar_position: 300
---

This article covers how to use [Dagster Pipes](/guides/build/external-pipelines/) with [AWS EMR](https://aws.amazon.com/emr/).

The [dagster-aws](/api/python-api/libraries/dagster-aws) integration library provides the <PyObject section="libraries" object="pipes.PipesEMRClient" module="dagster_aws" /> resource, which can be used to launch AWS EMR jobs from Dagster assets and ops. Dagster can receive regular events such as logs, asset checks, or asset materializations from jobs launched with this client. Using it requires minimal code changes to your EMR jobs.


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
    - Prepared infrastructure such as S3 buckets, IAM roles, and other resources required for your EMR job

</details>

## Step 1: Install the dagster-pipes module in your EMR environment

Choose one of the [options](https://spark.apache.org/docs/latest/api/python/user_guide/python_packaging.html#python-package-management) to install `dagster-pipes` in the EMR environment.

For example, this `Dockerfile` can be used to package all required dependencies into a single [PEX](https://docs.pex-tool.org/) file (in practice, the most straightforward way to package Python dependencies for EMR jobs):

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

```python file=/guides/dagster/dagster_pipes/emr/script.py
import boto3
from dagster_pipes import PipesS3MessageWriter, open_dagster_pipes
from pyspark.sql import SparkSession


def main():
    with open_dagster_pipes(
        message_writer=PipesS3MessageWriter(client=boto3.client("s3"))
    ) as pipes:
        pipes.log.info("Hello from AWS EMR!")

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

        print("Hello from stdout!")


if __name__ == "__main__":
    main()
```

## Step 3: Create an asset using the PipesEMRClient to launch the job

In the Dagster asset/op code, use the `PipesEMRClient` resource to launch the job:

```python file=/guides/dagster/dagster_pipes/emr/dagster_code.py startafter=start_asset_marker endbefore=end_asset_marker
import os

import boto3
from dagster_aws.pipes import PipesEMRClient, PipesS3MessageReader
from mypy_boto3_emr.type_defs import InstanceFleetTypeDef

from dagster import AssetExecutionContext, asset


@asset
def emr_pipes_asset(context: AssetExecutionContext, pipes_emr_client: PipesEMRClient):
    return pipes_emr_client.run(
        context=context,
        # see full reference here: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/emr/client/run_job_flow.html#EMR.Client.run_job_flow
        run_job_flow_params={},
    ).get_materialize_result()
```

This will launch the AWS EMR job and wait for it completion. If the job fails, the Dagster process will raise an exception. If the Dagster process is interrupted while the job is still running, the job will be terminated.

EMR application steps `stdout` and `stderr` will be forwarded to the Dagster process.

## Step 4: Create Dagster definitions

Next, add the `PipesEMRClient` resource to your project's <PyObject section="definitions" module="dagster" object="Definitions" /> object:

```python file=/guides/dagster/dagster_pipes/emr/dagster_code.py startafter=start_definitions_marker endbefore=end_definitions_marker
from dagster import Definitions  # noqa


defs = Definitions(
    assets=[emr_pipes_asset],
    resources={
        "pipes_emr_client": PipesEMRClient(
            message_reader=PipesS3MessageReader(
                client=boto3.client("s3"), bucket=os.environ["DAGSTER_PIPES_BUCKET"]
            )
        )
    },
)
```

Dagster will now be able to launch the AWS EMR job from the `emr_asset` asset, and receive logs and events from the job.
