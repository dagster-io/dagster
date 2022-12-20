import os

from dagster_aws.s3.io_manager import PickledObjectS3IOManager
from dagster_pyspark.resources import PySparkResource
from project_fully_featured.resources.hn_resource import HNAPIClient, HNAPISubsampleClient

from dagster._seven.temp_dir import get_system_temp_directory
from dagster._utils import file_relative_path

from .common_utils_to_move_to_libraries import DbtCliResource, build_s3_session, deferred_io_manager
from .duckdb_parquet_io_manager import DuckDBPartitionedParquetIOManager
from .parquet_io_manager import PartitionedParquetIOManager
from .snowflake_io_manager import SnowflakeIOManager

DBT_PROJECT_DIR = file_relative_path(__file__, "../../dbt_project")
DBT_PROFILES_DIR = DBT_PROJECT_DIR + "/config"


configured_pyspark = PySparkResource(
    spark_conf={
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
)

SHARED_SNOWFLAKE_CONF = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": os.getenv("SNOWFLAKE_USER", ""),
    "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
    "warehouse": "TINY_WAREHOUSE",
}

s3_session = build_s3_session()

s3_prod_bucket = "hackernews-elementl-prod"

RESOURCES_PROD = {
    "io_manager": deferred_io_manager(
        lambda: PickledObjectS3IOManager(s3_bucket=s3_prod_bucket, s3_session=s3_session)
    ),
    "parquet_io_manager": PartitionedParquetIOManager(
        base_path="s3://" + s3_prod_bucket,
        pyspark_resource=configured_pyspark,
    ),
    "warehouse_io_manager": SnowflakeIOManager(dict(database="DEMO_DB", **SHARED_SNOWFLAKE_CONF)),
    "hn_client": HNAPISubsampleClient(subsample_rate=10),
    "dbt": DbtCliResource(
        profiles_dir=DBT_PROFILES_DIR, project_dir=DBT_PROJECT_DIR, target="prod"
    ),
}

s3_staging_bucket = "hackernews-elementl-dev"

RESOURCES_STAGING = {
    "io_manager": deferred_io_manager(
        lambda: PickledObjectS3IOManager(s3_bucket=s3_staging_bucket, s3_session=s3_session)
    ),
    "parquet_io_manager": PartitionedParquetIOManager(
        base_path="s3://" + s3_staging_bucket,
        pyspark_resource=configured_pyspark,
    ),
    "warehouse_io_manager": SnowflakeIOManager(
        dict(database="DEMO_DB_STAGING", **SHARED_SNOWFLAKE_CONF)
    ),
    "hn_client": HNAPISubsampleClient(subsample_rate=10),
    "dbt": DbtCliResource(
        profiles_dir=DBT_PROFILES_DIR, project_dir=DBT_PROJECT_DIR, target="staging"
    ),
}


RESOURCES_LOCAL = {
    "parquet_io_manager": PartitionedParquetIOManager(
        base_path=get_system_temp_directory(),
        pyspark_resource=configured_pyspark,
    ),
    "warehouse_io_manager": DuckDBPartitionedParquetIOManager(
        base_path=get_system_temp_directory(),
        duckdb_path=os.path.join(DBT_PROJECT_DIR, "hackernews.duckdb"),
        pyspark_resource=configured_pyspark,
    ),
    "hn_client": HNAPIClient(),
    "dbt": DbtCliResource(
        profiles_dir=DBT_PROFILES_DIR, project_dir=DBT_PROJECT_DIR, target="local"
    ),
}
