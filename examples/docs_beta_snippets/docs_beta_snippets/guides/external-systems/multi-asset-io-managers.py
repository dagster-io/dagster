from collections.abc import Iterator
from typing import Union

from dagster_aws.s3 import S3PickleIOManager, S3Resource
from dagster_snowflake_pandas import SnowflakePandasIOManager

import dagster as dg


def clean_customer_data(): ...
def clean_order_data(): ...
def clean_product_data(): ...
def clean_country_data(): ...


@dg.multi_asset(
    specs=[
        # Use snowflake IO manager for cleaned customer data
        dg.AssetSpec("cleaned_customer_data").with_io_manager_key("snowflake"),
        # Use s3 IO manager for cleaned order data
        dg.AssetSpec("cleaned_order_data").with_io_manager_key("s3"),
        # Don't store cleaned product data at all
        dg.AssetSpec("cleaned_product_data"),
        # Use default IO manager for cleaned country data
        dg.AssetSpec("cleaned_country_data"),
    ]
)
def clean_data() -> Iterator[Union[dg.Output, dg.AssetMaterialization]]:
    yield dg.Output(output_name="cleaned_customer_data", value=clean_customer_data())
    yield dg.Output(output_name="cleaned_order_data", value=clean_order_data())
    yield dg.Output(output_name="cleaned_country_data", value=clean_country_data())
    # We're not yielding any output value for cleaned_product_data, so it will not be stored
    yield dg.AssetMaterialization(
        asset_key="cleaned_product_data", description="Product data cleaned"
    )


# Define the requisite IO managers
defs = dg.Definitions(
    assets=[clean_data],
    # Define the additional IO managers
    resources={
        "snowflake": SnowflakePandasIOManager(
            database=dg.EnvVar("SNOWFLAKE_DATABASE"),
            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
            user=dg.EnvVar("SNOWFLAKE_USER"),
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
        ),
        "s3": S3PickleIOManager(s3_resource=S3Resource(), s3_bucket="my-bucket"),
    },
)
