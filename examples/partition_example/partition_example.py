import datetime
import random
from typing import Dict, List

import pandas as pd
import pytz
from dagster import (
    AssetExecutionContext,
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    MetadataValue,
    MonthlyPartitionsDefinition,
    Output,
    WeeklyPartitionsDefinition,
    asset,
)


class Salesforce:
    def __init__(self, *args, **kwargs):
        ...

    def query(self, *args, **kwargs):
        ...


def relativedelta(*args, **kwargs):
    ...


@asset(
    partitions_def=MonthlyPartitionsDefinition(start_date="2022-01-01"),
    metadata={"partition_expr": "LastModifiedDate"},
)
def salesforce_customers(context: AssetExecutionContext) -> pd.DataFrame:
    start_date_str = context.asset_partition_key_for_output()

    timezone = pytz.timezone("GMT")  # Replace 'Your_Timezone' with the desired timezone
    start_obj = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=timezone)
    end_obj = start_obj + relativedelta(months=1)  # Add one month to start_obj

    start_obj_str = start_obj.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    end_obj_str = end_obj.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    sf = Salesforce(username="xxxxxx", password="xxxxx", security_token="xxxx")
    sf_result = sf.query(
        f"SELECT FIELDS(STANDARD)  FROM Account where LastModifiedDate >= {start_obj_str} and LastModifiedDate < {end_obj_str}"
    )
    if sf_result["totalSize"] == 0:
        return None
    account = pd.DataFrame(sf_result["records"]).drop(["attributes"], axis=1)
    return account


daily_partition = DailyPartitionsDefinition(start_date="2023-01-01")


def all_realvols(*args, **kwargs):
    ...


@asset(partitions_def=daily_partition)
def realized_vol(context: AssetExecutionContext, orats_daily_prices: pd.DataFrame):
    """This function calculates the realized volatility for a given asset using the Orats daily prices.
    The volatility is calculated using various methods such as close-to-close, Parkinson, Hodges-Tompkins, and Yang-Zhang.
    The function returns a DataFrame with the calculated volatilities.
    """
    trade_date = context.asset_partition_key_for_output()
    ticker_id = 1

    df = all_realvols(orats_daily_prices, ticker_id, trade_date)

    context.add_output_metadata({"preview": MetadataValue.md(df.to_markdown())})

    return df


hourly_partitions = HourlyPartitionsDefinition(start_date="2024-01-01")


@asset(io_manager_def="parquet_io_manager", partitions_def=hourly_partitions)
def my_custom_df(context: AssetExecutionContext) -> pd.DataFrame:
    start, end = context.asset_partitions_time_window_for_output()

    df = pd.DataFrame({"timestamp": pd.date_range(start, end, freq="5T")})
    df["count"] = df["timestamp"].map(lambda a: random.randint(1, 1000))
    return df


def fetch_blog_posts_from_external_api(*args, **kwargs):
    ...


@asset(partitions_def=HourlyPartitionsDefinition(start_date="2022-01-01-00:00"))
def blog_posts(context: AssetExecutionContext) -> List[Dict]:
    partition_datetime_str = context.asset_partition_key_for_output()
    hour = datetime.datetime.fromisoformat(partition_datetime_str)
    posts = fetch_blog_posts_from_external_api(hour_when_posted=hour)
    return posts


@asset(
    io_manager_key="snowflake_io_manager",
    required_resource_keys={"eldermark"},
    partitions_def=WeeklyPartitionsDefinition(start_date="2022-11-01"),
    key_prefix=["snowflake", "eldermark_proxy"],
)
def resident(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    start, end = context.asset_partitions_time_window_for_output()
    filter_str = f"LastMod_Stamp >= {start.timestamp()} AND LastMod_Stamp < {end.timestamp()}"

    records = context.resources.eldermark.fetch_obj(obj="Resident", filter=filter_str)

    df = pd.DataFrame(list(records), columns=["src"], dtype="string")

    yield Output(df, metadata={"partition_expr": "PARSE_JSON(SRC):LASTMOD_STAMP::TIMESTAMP"})
