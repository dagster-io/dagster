---
title: "Build pipelines with PySpark"
description: "Learn to integrate Dagster Pipes with PySpark to orchestrate PySpark jobs in a Dagster pipeline."
sidebar_position: 900
---

This tutorial is focused on using Dagster Pipes to launch & monitor general PySpark jobs. The [Spark integration page](/integrations/libraries/spark) provides more information on using Pipes with specific Spark providers, such as AWS EMR or Databricks.

Spark is often used with object stores such as Amazon S3. We are going to simulate this setup locally with [MinIO](https://min.io/), which has an API compatible with AWS S3. All communication between Dagster and the Spark job (metadata and logs collection) will happen through a MinIO bucket.

## Prerequisites

We are going to use [Docker](https://docs.docker.com/get-started/get-docker/) to emulate a typical Spark setup locally. Therefore, only Docker is required to reproduce this example.

## Production considerations

For demonstration purposes, this tutorial makes a few simplifications that you should consider when deploying in production:

- We are going to be running Spark in local mode, sharing the same container with Dagster. In production, consider having two separate environments:

  - **In the Dagster environment**, you'll need to have the following Python packages:

    - `dagster`
    - `dagster-webserver` --- to run the Dagster UI
    - `dagster-aws` --- when using S3

    You will also need to make the orchestration code available to Dagster (typically via a [code location](/guides/deploy/code-locations/)).

  - **In the PySpark environment**, you'll need to install the `dagster-pipes` Python package, and typically the Java AWS S3 SDK packages. For example:

    ```shell
    curl -fSL "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.5.1/hadoop-aws-3.5.1.jar" \
      -o /opt/bitnami/spark/jars/hadoop-aws-3.5.1.jar

    curl -fSL "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.780/aws-java-sdk-bundle-1.12.780.jar" \
      -o /opt/bitnami/spark/jars/aws-java-sdk-bundle-1.12.780.jar
    ```

    Make sure `hadoop-aws` JAR and AWS Java SDK versions are compatible with your Spark/Hadoop build.

- We are going to upload the PySpark script to the S3 bucket directly inside the Dagster asset. In production, consider doing this via CI/CD instead.

## Step 1: Writing the Dagster orchestration code (dagster_code.py)

We will set up a few non-default Pipes components to streamline the otherwise challenging problem of orchestrating Spark jobs.

1. Let's start by creating the asset and opening a Pipes session. We will be using S3 to pass Pipes messages from the Spark job to Dagster, so we will create `PipesS3MessageReader` and `PipesS3ContextInjector` objects. (Technically, it's not strictly required to use S3 for passing the Dagster context, but storing it there will decrease the CLI arguments size).

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/dagster_pipes/pyspark/dagster_code.py startafter=start_pipes_session_marker endbefore=end_pipes_session_marker
import os
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

import boto3
from dagster_aws.pipes import PipesS3ContextInjector, PipesS3MessageReader

import dagster as dg

LOCAL_SCRIPT_PATH = Path(__file__).parent / "script.py"


@dg.asset
def pipes_spark_asset(context: dg.AssetExecutionContext):
    s3_client = boto3.client("s3")

    bucket = os.environ["DAGSTER_PIPES_BUCKET"]

    # upload the script to S3
    # ideally, this should be done via CI/CD processes and not in the asset body
    # but for the sake of this example we are doing it here
    s3_script_path = f"{context.dagster_run.run_id}/pyspark_script.py"
    s3_client.upload_file(LOCAL_SCRIPT_PATH, bucket, s3_script_path)

    context_injector = PipesS3ContextInjector(
        client=s3_client,
        bucket=bucket,
    )

    message_reader = PipesS3MessageReader(
        client=s3_client,
        bucket=bucket,
        # the following setting will configure the Spark job to collect logs from the driver
        # and send them to Dagster via Pipes
        include_stdio_in_messages=True,
    )
```

Notice how `PipesS3MessageReader` has `include_stdio_in_messages=True`. This setting will configure the Pipes **message writer** in the Spark job to collect logs from the Spark driver and send them to Dagster via Pipes messages.

2. We will be using CLI arguments to pass the bootstrap information from Dagster to the Spark job. We will fetch them from the `session.get_bootstrap_cli_arguments` method. We pass these arguments to `spark-submit` along with a few other settings.

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/dagster_pipes/pyspark/dagster_code.py startafter=end_pipes_session_marker endbefore=start_definitions_marker
# pipes_spark_asset body continues below
    with dg.open_pipes_session(
        context=context,
        message_reader=message_reader,
        context_injector=context_injector,
    ) as session:
        dagster_pipes_args = " ".join(
            # prepare Pipes bootstrap CLI arguments
            [
                f"{key} {value}"
                for key, value in session.get_bootstrap_cli_arguments().items()
            ]
        )

        cmd = " ".join(
            [
                "spark-submit",
                # change --master and --deploy-mode according to specific Spark setup
                "--master",
                "local[*]",
                "--conf",
                "spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem",
                # custom S3 endpoint for MinIO
                "--conf",
                "spark.hadoop.fs.s3a.endpoint=http://minio:9000",
                "--conf",
                "spark.hadoop.fs.s3a.path.style.access=true",
                f"s3a://{bucket}/{s3_script_path}",
                dagster_pipes_args,
            ]
        )

        subprocess.run(
            # we do not forward stdio on purpose to demonstrate how Pipes collect logs from the driver
            cmd,
            shell=True,
            check=True,
        )

        return session.get_results()
```

:::note

In other Pipes workflows, passing the bootstrap information from Dagster to the remote Pipes session is typically done via environment variables, but setting environment variables for Spark jobs can be complicated (the exact way of doing this depends on the Spark deployment) or not possible at all. CLI arguments are a convenient alternative.

:::

## Step 2: Use Pipes in the PySpark job (script.py)

First, create a new file named `script.py`, then add the following code to create a context that can be used to send messages to Dagster:

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/dagster_pipes/pyspark/script.py startafter
import boto3
from dagster_pipes import (
    PipesCliArgsParamsLoader,
    PipesS3ContextLoader,
    PipesS3MessageWriter,
    open_dagster_pipes,
)
from pyspark.sql import SparkSession


def main():
    with open_dagster_pipes(
        message_writer=PipesS3MessageWriter(client=boto3.client("s3")),
        context_loader=PipesS3ContextLoader(client=boto3.client("s3")),
        params_loader=PipesCliArgsParamsLoader(),
    ) as pipes:
        print("Hello from the Spark driver!")

        pipes.log.info("I am logging a Dagster message from the Spark driver!")

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

Note how `PipesCliArgsParamsLoader` is used to load the CLI arguments passed by Dagster. This information will be used to automatically configure `PipesS3MessageWriter` and `PipesS3ContextLoader`.

Because the Dagster code has `include_stdio_in_messages=True`, the message writer will collect logs from the driver and send them to Dagster via Pipes messages.

## Step 3: Running the pipeline with Docker

1. Place the PySpark code for `script.py` and the Dagster orchestration code for `dagster_code.py` in the same directory.

2. Create a `Dockerfile`:

```dockerfile file=/guides/dagster/dagster_pipes/pyspark/Dockerfile
ARG SPARK_VERSION=3.5.1

FROM bitnami/spark:${SPARK_VERSION}

USER root

ARG SPARK_VERSION=3.4.1

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

RUN install_packages curl

RUN curl -fSL "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/$SPARK_VERSION/hadoop-aws-$SPARK_VERSION.jar" \
    -o /opt/bitnami/spark/jars/hadoop-aws-$SPARK_VERSION.jar

RUN curl -fSL "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.780/aws-java-sdk-bundle-1.12.780.jar" \
    -o /opt/bitnami/spark/jars/aws-java-sdk-bundle-1.12.780.jar

# install Python dependencies
RUN --mount=type=cache,target=/root/.cache/uv uv pip install --system dagster dagster-webserver dagster-aws pyspark

WORKDIR /src
ENV DAGSTER_HOME=/dagster_home
COPY dagster_code.py script.py ./
```

3. Create a `docker-compose.yml`:

{/* TODO convert to <CodeExample> */}
```yaml file=/guides/dagster/dagster_pipes/pyspark/docker-compose.yml
# this docker compose file creates a mini Spark cluster with 1 master and 2 workers to simulate a distributed environment

volumes:
  spark-logs:
  spark-data:
  minio-data:
  dagster_home:

networks:
  spark:

services:
  minio:
    image: bitnami/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio123
      MINIO_DEFAULT_BUCKETS: "dagster-pipes:public"
    volumes:
      - minio-data:/data
    networks:
      - spark

  dagster-dev:
    develop:
      watch:
        - action: sync
          path: .
          target: /src
    build:
      context: .
      dockerfile: Dockerfile
    command:
      - "dagster"
      - "dev"
      - "-f"
      - "/src/dagster_code.py"
      - "--host"
      - "0.0.0.0"
      - "--port"
      - "3000"
    ports:
      - "3000:3000"
    volumes:
      - spark-logs:/spark/logs
      - spark-data:/spark/data
      - dagster_home:/dagster_home
    environment:
      AWS_ACCESS_KEY_ID: minio
      AWS_SECRET_ACCESS_KEY: minio123
      AWS_ENDPOINT_URL: http://minio:9000
      DAGSTER_PIPES_BUCKET: dagster-pipes

    depends_on:
      - minio

    networks:
      - spark
```

4. Start the Dagster dev instance inside Docker:

```shell
docker compose up --build --watch
```

:::note

`--watch` will automatically sync the changes in the local filesystem to the
Docker container, which is useful for live code updates without volume mounts.

:::

5. Navigate to [http://localhost:3000](http://localhost:3000) to open the Dagster UI and materialize the asset. Metadata and stdio logs emitted in the PySpark job will become available in Dagster.

