---
title: "Automatically Process Files Landing in AWS S3"
description: "This use case demonstrates how to automate the process of processing files being written to an S3 bucket."
tags: ["s3", "automation"]
---

# Automatically Process Files Landing in AWS S3

This use case demonstrates how to automate the process of copying a file from one S3 bucket to another using Dagster. The objective is to detect new files in a source S3 bucket and back them up to a destination S3 bucket.

---

## What You'll Learn

You will learn how to:

- Define a Dagster sensor that detects new files in an S3 bucket.
- Define a Dagster asset that reads and processes a file in S3.
- Configure S3 resources in Dagster.
- Configure a `RunRequest` in Dagster.

---

## Prerequisites

To follow the steps in this guide, you will need:

- To have Dagster installed. Refer to the [Dagster Installation Guide](https://docs.dagster.io/getting-started/installation) for instructions.
- A basic understanding of Dagster. Refer to the [Dagster Documentation](https://docs.dagster.io/getting-started/what-why-dagster) for more information.
- AWS credentials with access to the S3 buckets.
- An S3 buckets containing files you would like to process.

---

## Steps to Implement With Dagster

By following these steps, you will have a Dagster setup that detects new files in a source S3 bucket and processes them.

### Step 1: Define the S3 Resources

First, define the S3 resources that will be used to interact with the S3 buckets.

```python
from dagster import Definitions, EnvVar
from dagster_aws.s3 import S3Resource

s3_resource = S3Resource(
    aws_access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=EnvVar("AWS_SESSION_TOKEN"),
    region_name="us-west-2",
)

defs = Definitions(
    resources={
        "s3": s3_resource,
    },
)
```

### Step 2: Create a Sensor to Detect New Files

Next, create a sensor that detects new files in the source S3 bucket.

```python
from dagster import (
    Config,
    Definitions,
    RunConfig,
    RunRequest,
    SkipReason,
    sensor,
)
from dagster_aws.s3 import S3Resource
from dagster_aws.s3.sensor import get_s3_keys

AWS_S3_BUCKET = "example-source-bucket"
AWS_S3_OBJECT_PREFIX = "example-source-prefix"

class ObjectConfig(Config):
    key: str


@sensor(target=s3_file_backup)
def s3_backup_sensor(context):
    latest_key = context.cursor or None
    unprocessed_object_keys = get_s3_keys(
        bucket=AWS_S3_BUCKET, prefix=AWS_S3_OBJECT_PREFIX, since_key=latest_key
    )

    for key in unprocessed_object_keys:
        yield RunRequest(
            run_key=key, run_config=RunConfig(ops={"s3_file_backup": ObjectConfig(key=key)})
        )

    if not unprocessed_object_keys:
        return SkipReason("No new s3 files found for bucket source-bucket.")

    last_key = unprocessed_object_keys[-1]
    context.update_cursor(last_key)


defs = Definitions(
    assets=[s3_file_backup],
    resources={
        "s3": s3_resource,
    },
    sensors=[s3_backup_sensor],
)
```

### Step 3: Define the Asset to Process the File

Define an asset that copies files from the source S3 bucket to the backup S3 bucket.

```python
from dagster import (
    AssetExecutionContext,
    Config,
    Definitions,
    EnvVar,
    RunConfig,
    RunRequest,
    SkipReason,
    asset,
    sensor,
)
from dagster_aws.s3 import S3Resource
from dagster_aws.s3.sensor import get_s3_keys

AWS_S3_BUCKET = "example-source-bucket"
AWS_S3_OBJECT_PREFIX = "example-source-prefix"

s3_resource = S3Resource(
    aws_access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=EnvVar("AWS_SESSION_TOKEN"),
    region_name="us-west-2",
)


class ObjectConfig(Config):
    key: str


@asset()
def s3_file_backup(context: AssetExecutionContext, s3: S3Resource, config: ObjectConfig):
    s3 = context.resources.s3
    context.log.info(f"Reading {config.key}")
    _ = s3.get_object(Bucket=AWS_S3_BUCKET, Key=config.key)  # process object here


@sensor(target=s3_file_backup)
def s3_backup_sensor(context):
    latest_key = context.cursor or None
    unprocessed_object_keys = get_s3_keys(
        bucket=AWS_S3_BUCKET, prefix=AWS_S3_OBJECT_PREFIX, since_key=latest_key
    )

    for key in unprocessed_object_keys:
        yield RunRequest(
            run_key=key, run_config=RunConfig(ops={"s3_file_backup": ObjectConfig(key=key)})
        )

    if not unprocessed_object_keys:
        return SkipReason("No new s3 files found for bucket source-bucket.")

    last_key = unprocessed_object_keys[-1]
    context.update_cursor(last_key)


defs = Definitions(
    assets=[s3_file_backup],
    resources={
        "s3": s3_resource,
    },
    sensors=[s3_backup_sensor],
)
```

---

## Expected Outcomes

By implementing this use case, you will have an automated system that detects new files in a source S3 bucket and processes them.

---

## Troubleshooting

- **Sensor is not detecting new files:** Ensure that your AWS credentials have the necessary permissions and that your bucket and prefix are spelled correctly.

---

## Next Steps

After setting up your file sensor, you can explore other Dagster features such as monitoring and alerting to enhance your data pipeline.

---

## Additional Resources

- [Dagster Documentation](https://docs.dagster.io/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/index.html)
- [Dagster AWS Integration](https://docs.dagster.io/_apidocs/libraries/dagster-aws)
