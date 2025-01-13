---
title: "Replicate CSV Files in S3 to Snowflake with Sling"
description: "This use case demonstrates how to transfer data from Snowflake to Amazon S3 using Dagster. The objective is to automate the extraction of data from Snowflake and store it in S3 for further processing or archival."
tags: ["snowflake", "s3", "sling"]
---

# Replicate CSV Files in S3 to Snowflake with Sling

This use case demonstrates how to replicate CSV files landing in an S3 bucket to Snowflake using Dagster's embedded ELT Sling integration. The objective is to automate the process of ingesting CSV files from S3 and loading them into Snowflake for further analysis or processing.

---

## What You'll Learn

You will learn how to:

- Define a Dagster asset that extracts data from an S3 bucket and writes it to Snowflake
- Configure Sling resources for S3 and Snowflake connections
- Implement a replication configuration for the data transfer

---

## Prerequisites

To follow the steps in this guide, you will need:

- To have Dagster installed. Refer to the [Dagster Installation Guide](https://docs.dagster.io/getting-started/installation) for instructions.
- A basic understanding of Dagster. Refer to the [Dagster Documentation](https://docs.dagster.io/getting-started/what-why-dagster) for more information.
- AWS S3 bucket with CSV files
- Snowflake account and database
- Environment variables set for AWS and Snowflake credentials

---

## Steps to Implement With Dagster

By following these steps, you will have a Dagster asset that successfully replicates CSV files from an S3 bucket to Snowflake.

### Step 1: Define Sling Connection Resources

First, define the Sling connection resources for S3 and Snowflake.

```python
from dagster import Definitions, EnvVar
from dagster_sling import SlingConnectionResource, SlingResource, sling_assets

S3_SOURCE_BUCKET = "elementl-data"


s3_connection = SlingConnectionResource(
    name="SLING_S3_SOURCE",
    type="s3",
    bucket=S3_SOURCE_BUCKET,  # type: ignore
    access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),  # type: ignore
    secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),  # type: ignore
)

snowflake_connection = SlingConnectionResource(
    name="SLING_SNOWFLAKE_DESTINATION",
    type="snowflake",
    host=EnvVar("SNOWFLAKE_ACCOUNT"),  # type: ignore
    user=EnvVar("SNOWFLAKE_USER"),  # type: ignore
    password=EnvVar("SNOWFLAKE_PASSWORD"),  # type: ignore
    warehouse=EnvVar("SNOWFLAKE_WAREHOUSE"),  # type: ignore
    database=EnvVar("SNOWFLAKE_DATABASE"),  # type: ignore
    schema=EnvVar("SNOWFLAKE_SCHEMA"),  # type: ignore
    role=EnvVar("SNOWFLAKE_ROLE"),  # type: ignore
)


sling_resource = SlingResource(connections=[s3_connection, snowflake_connection])
```

### Step 2: Create the Replication Configuration

Next, create the replication configuration that specifies the source and target for the data transfer.

```python
replication_config = {
    "source": "SLING_S3_SOURCE",
    "target": "SLING_SNOWFLAKE_DESTINATION",
    "defaults": {"mode": "full-refresh", "object": "{stream_schema}_{stream_table}"},
    "streams": {
        f"s3://{S3_SOURCE_BUCKET}/staging": {
            "object": "public.example_table",
            "primary_key": "id",
        },
    },
}
```

### Step 3: Define the Dagster Asset

Define the Dagster asset that uses the Sling resource and replication configuration to perform the data transfer.

```python
from dagster import Definitions, EnvVar
from dagster_sling import SlingConnectionResource, SlingResource, sling_assets

# ...

@sling_assets(replication_config=replication_config)
def replicate_csv_to_snowflake(context, sling: SlingResource):
    yield from sling.replicate(context=context)


defs = Definitions(assets=[replicate_csv_to_snowflake], resources={"sling": sling_resource})
```

---

## Expected Outcomes

By implementing this use case, you will have an automated pipeline that replicates CSV files from an S3 bucket to Snowflake. The data will be available in Snowflake for further analysis or processing.

---

## Troubleshooting

- Ensure that the AWS and Snowflake credentials are correctly set in the environment variables.
- Verify that the S3 bucket and Snowflake database are accessible and correctly configured.
- Check the replication configuration for any errors or mismatches in the source and target specifications.

---

## Next Steps

- Explore scheduling the replication job to run at regular intervals using Dagster schedules.
- Extend the pipeline to include data transformations or validations before loading into Snowflake.

---

## Additional Resources

- [Dagster Documentation](https://docs.dagster.io/)
- [Dagster Sling Documentation](https://docs.dagster.io/integrations/sling)
- [Sling Documentation](https://docs.slingdata.io/)
- [Snowflake Documentation](https://docs.snowflake.com/)
