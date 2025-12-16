from dagster import Definitions, EnvVar

from .assets.composable_resources import extract_api_data, extract_customer_data, load_to_storage
from .assets.elt_pipeline import (
    extract_raw_clickstream,
    load_raw_to_warehouse,
    transform_in_warehouse,
)
from .assets.etl_pipeline import (
    extract_sales_data,
    load_to_warehouse as etl_load_to_warehouse,
    transform_sales_data,
)
from .assets.lakehouse_pipeline import (
    aggregate_gold_layer,
    extract_sensor_data,
    load_bronze_layer,
    process_silver_layer,
)
from .resources import PostgresResource, RESTAPIResource, S3Resource, SnowflakeResource

definitions = Definitions(
    assets=[
        extract_sales_data,
        transform_sales_data,
        etl_load_to_warehouse,
        extract_raw_clickstream,
        load_raw_to_warehouse,
        transform_in_warehouse,
        extract_sensor_data,
        load_bronze_layer,
        process_silver_layer,
        aggregate_gold_layer,
        extract_customer_data,
        extract_api_data,
        load_to_storage,
    ],
    resources={
        "database": PostgresResource(
            host=EnvVar("POSTGRES_HOST").get_value() or "localhost",
            port=int(EnvVar("POSTGRES_PORT").get_value() or "5432"),
            user=EnvVar("POSTGRES_USER").get_value() or "dagster",
            password=EnvVar("POSTGRES_PASSWORD").get_value() or "dagster",
            database=EnvVar("POSTGRES_DATABASE").get_value() or "demo",
        ),
        "api": RESTAPIResource(
            base_url=EnvVar("API_BASE_URL").get_value() or "http://localhost:8000",
            api_key=EnvVar("API_KEY").get_value(),
        ),
        "snowflake": SnowflakeResource(
            account=EnvVar("SNOWFLAKE_ACCOUNT").get_value() or "",
            user=EnvVar("SNOWFLAKE_USER").get_value() or "",
            password=EnvVar("SNOWFLAKE_PASSWORD").get_value() or "",
            database=EnvVar("SNOWFLAKE_DATABASE").get_value() or "",
            warehouse=EnvVar("SNOWFLAKE_WAREHOUSE").get_value() or "",
            schema_name=EnvVar("SNOWFLAKE_SCHEMA").get_value() or "PUBLIC",
        ),
        "storage": S3Resource(
            bucket=EnvVar("S3_BUCKET").get_value() or "",
            region=EnvVar("AWS_REGION").get_value() or "us-east-1",
            access_key_id=EnvVar("AWS_ACCESS_KEY_ID").get_value(),
            secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY").get_value(),
        ),
    },
)
