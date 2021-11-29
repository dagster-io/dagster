import os

from dagster import ResourceDefinition
from dagster_aws.s3 import s3_resource
from dagster_pyspark import pyspark_resource
from dagstermill.io_managers import local_output_notebook_io_manager

from .common_bucket_s3_pickle_io_manager import common_bucket_s3_pickle_io_manager
from .parquet_io_manager import (
    local_partitioned_parquet_io_manager,
    s3_partitioned_parquet_io_manager,
)
from .s3_notebook_io_manager import s3_notebook_io_manager
from .snowflake_io_manager import snowflake_io_manager

configured_pyspark = pyspark_resource.configured(
    {
        "spark_conf": {
            "spark.jars.packages": ",".join(
                [
                    "net.snowflake:snowflake-jdbc:3.8.0",
                    "net.snowflake:spark-snowflake_2.12:2.8.2-spark_3.0",
                    "com.amazonaws:aws-java-sdk:1.7.4,org.apache.hadoop:hadoop-aws:2.7.7",
                ]
            ),
            "spark.hadoop.fs.s3.impl": "org.apache.hadoop.fs.s3native.NativeS3FileSystem",
            "spark.hadoop.fs.s3.awsAccessKeyId": os.getenv("AWS_ACCESS_KEY_ID", ""),
            "spark.hadoop.fs.s3.awsSecretAccessKey": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            "spark.hadoop.fs.s3.buffer.dir": "/tmp",
        }
    }
)


snowflake_io_manager_prod = snowflake_io_manager.configured({"database": "DEMO_DB"})

RESOURCES_PROD = {
    "s3_bucket": ResourceDefinition.hardcoded_resource("hackernews-elementl-prod"),
    "io_manager": common_bucket_s3_pickle_io_manager,
    "s3": s3_resource,
    "parquet_io_manager": s3_partitioned_parquet_io_manager,
    "warehouse_io_manager": snowflake_io_manager_prod,
    "pyspark": configured_pyspark,
    "warehouse_loader": snowflake_io_manager_prod,
    "output_notebook_io_manager": s3_notebook_io_manager,
}

snowflake_io_manager_staging = snowflake_io_manager.configured({"database": "DEMO_DB_STAGING"})


RESOURCES_STAGING = {
    "s3_bucket": ResourceDefinition.hardcoded_resource("hackernews-elementl-dev"),
    "io_manager": common_bucket_s3_pickle_io_manager,
    "s3": s3_resource,
    "parquet_io_manager": s3_partitioned_parquet_io_manager,
    "warehouse_io_manager": snowflake_io_manager_staging,
    "pyspark": configured_pyspark,
    "warehouse_loader": snowflake_io_manager_staging,
    "output_notebook_io_manager": s3_notebook_io_manager,
}


RESOURCES_LOCAL = {
    "parquet_io_manager": local_partitioned_parquet_io_manager,
    "warehouse_io_manager": local_partitioned_parquet_io_manager,
    "pyspark": configured_pyspark,
    "warehouse_loader": snowflake_io_manager_prod,
    "output_notebook_io_manager": local_output_notebook_io_manager,
}
