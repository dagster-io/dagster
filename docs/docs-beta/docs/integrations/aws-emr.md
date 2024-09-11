---
layout: Integration
status: published
name: AWS EMR
title: Dagster & AWS EMR
sidebar_label: AWS EMR
excerpt: The AWS EMR integration allows you to seamlessly integrate AWS EMR into your Dagster pipelines for petabyte-scale data processing using open source tools like Apache Spark, Hive, Presto, and more.
date: 2024-06-21
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-aws
docslink: 
partnerlink: https://aws.amazon.com/
logo: /integrations/aws-emr.svg
categories:
  - Compute
enabledBy:
enables:
---

### About this integration

The `dagster-aws` integration provides ways orchestrating data pipelines that leverage AWS services, including AWS EMR (Elastic MapReduce). This integration allows you to run and scale big data workloads using open source tools such as Apache Spark, Hive, Presto, and more.

Using this integration, you can:

- Seamlessly integrate AWS EMR into your Dagster pipelines.
- Utilize EMR for petabyte-scale data processing.
- Easily manage and monitor EMR clusters and jobs from within Dagster.
- Leverage Dagster's orchestration capabilities to handle complex data workflows involving EMR.

### Installation

```bash
pip install dagster-aws
```

### Examples

```python
from pathlib import Path
from typing import Any

from dagster import Definitions, ResourceParam, asset
from dagster_aws.emr import emr_pyspark_step_launcher
from dagster_aws.s3 import S3Resource
from dagster_pyspark import PySparkResource
from pyspark.sql import DataFrame, Row
from pyspark.sql.types import IntegerType, StringType, StructField, StructType


emr_pyspark = PySparkResource(spark_config={"spark.executor.memory": "2g"})


@asset
def people(
    pyspark: PySparkResource, pyspark_step_launcher: ResourceParam[Any]
) -> DataFrame:
    schema = StructType(
        [StructField("name", StringType()), StructField("age", IntegerType())]
    )
    rows = [
        Row(name="Thom", age=51),
        Row(name="Jonny", age=48),
        Row(name="Nigel", age=49),
    ]
    return pyspark.spark_session.createDataFrame(rows, schema)


@asset
def people_over_50(
    pyspark_step_launcher: ResourceParam[Any], people: DataFrame
) -> DataFrame:
    return people.filter(people["age"] > 50)


defs = Definitions(
    assets=[people, people_over_50],
    resources={
        "pyspark_step_launcher": emr_pyspark_step_launcher.configured(
            {
                "cluster_id": {"env": "EMR_CLUSTER_ID"},
                "local_pipeline_package_path": str(Path(__file__).parent),
                "deploy_local_pipeline_package": True,
                "region_name": "us-west-1",
                "staging_bucket": "my_staging_bucket",
                "wait_for_logs": True,
            }
        ),
        "pyspark": emr_pyspark,
        "s3": S3Resource(),
    },
)
```

### About AWS EMR

**AWS EMR** (Elastic MapReduce) is a cloud big data platform for processing vast amounts of data using open source tools such as Apache Spark, Apache Hive, Apache HBase, Apache Flink, Apache Hudi, and Presto. It simplifies running big data frameworks, allowing you to process and analyze large datasets quickly and cost-effectively. AWS EMR provides the scalability, flexibility, and reliability needed to handle complex data processing tasks, making it an ideal choice for data engineers and scientists.
