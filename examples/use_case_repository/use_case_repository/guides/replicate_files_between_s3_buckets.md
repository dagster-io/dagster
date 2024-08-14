---
title: "Automate Object Backup Between Buckets in S3"
description: "This use case demonstrates how to automate the process of copying a file from one S3 bucket to another using Dagster. The objective is to detect new files in a source S3 bucket and back them up to a destination S3 bucket."
tags: ["s3", "automation"]
---

# Automate Object Backup Between Buckets in S3utomate File Backup Between S3 Buckets with Dagster

This use case demonstrates how to automate the process of copying a file from one S3 bucket to another using Dagster. The objective is to detect new files in a source S3 bucket and back them up to a destination S3 bucket.

---

## What You'll Learn

You will learn how to:

- Define a Dagster sensor that detects new files in an S3 bucket.
- Define a Dagster asset that copies files between S3 buckets.
- Configure S3 resources in Dagster.

---

## Prerequisites

To follow the steps in this guide, you will need:

- To have Dagster installed. Refer to the [Dagster Installation Guide](https://docs.dagster.io/getting-started/installation) for instructions.
- A basic understanding of Dagster. Refer to the [Dagster Documentation](https://docs.dagster.io/getting-started/what-why-dagster) for more information.
- AWS credentials with access to the S3 buckets.
- Two S3 buckets: one for the source files and one for the backup.

---

## Steps to Implement With Dagster

By following these steps, you will have a Dagster setup that detects new files in a source S3 bucket and copies them to a backup S3 bucket.

### Step 1: Define the S3 Resources

First, define the S3 resources that will be used to interact with the S3 buckets.

```python
from dagster_aws.s3 import S3Resource
from dagster import Definitions

s3_resource = S3Resource()

defs = Definitions(
    resources={
        "s3": s3_resource,
    }
)
```

### Step 2: Create a Sensor to Detect New Files

Next, create a sensor that detects new files in the source S3 bucket.

```python
from dagster import Definitions, RunRequest, SkipReason, sensor
from dagster_aws.s3.sensor import get_s3_keys

S3_SOURCE_BUCKET = "source-bucket"
S3_DESTINATION_BUCKET = "destination-bucket"


@sensor(target=s3_file_backup)
def s3_backup_sensor(context):
    since_key = context.cursor or None
    new_s3_keys = get_s3_keys(S3_SOURCE_BUCKET, since_key=since_key)

    for key in new_s3_keys:
        yield RunRequest(run_key=key)

    if not new_s3_keys:
        yield SkipReason("No new s3 files found for bucket source-bucket.")

    last_key = new_s3_keys[-1]
    context.update_cursor(last_key)


defs = Definitions(
    resources={
        "s3": s3_resource,
    },
    sensors=[s3_backup_sensor],
)
```

### Step 3: Define the Asset to Copy Files

Define an asset that copies files from the source S3 bucket to the backup S3 bucket.

```python
from dagster import AssetExecutionContext, Definitions, RunRequest, SkipReason, asset, sensor
from dagster_aws.s3 import S3Resource
from dagster_aws.s3.sensor import get_s3_keys


@asset(required_resource_keys={"s3"})
def s3_file_backup(context: AssetExecutionContext):
    s3 = context.resources.s3
    s3_key = context.run.run_id
    s3.meta.client.copy({"Bucket": S3_SOURCE_BUCKET, "Key": s3_key}, S3_DESTINATION_BUCKET, s3_key)
    context.log.info(f"Copied {s3_key} from source-bucket to backup-bucket")


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

By implementing this use case, you will have an automated system that detects new files in a source S3 bucket and copies them to a backup S3 bucket. This ensures that your files are backed up as soon as they are added to the source bucket.

---

## Troubleshooting

- **Sensor is not detecting new files:** Ensure that your AWS credentials have the necessary permissions to list and read files in the source S3 bucket.
- **Object is not being copied to bucket:** Verify that your AWS credentials have the necessary permissions to write to the backup S3 bucket.

---

## Next Steps

After setting up the file backup system, you can explore other Dagster features such as monitoring and alerting to enhance your data pipeline.

---

## Additional Resources

- [Dagster Documentation](https://docs.dagster.io/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/index.html)
- [Dagster AWS Integration](https://docs.dagster.io/_apidocs/libraries/dagster-aws)
