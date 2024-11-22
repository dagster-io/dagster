from datetime import datetime
from typing import Dict

import pandas as pd

from dagster import (
    AssetExecutionContext,
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    asset,
    materialize,
)

start = datetime(2022, 1, 1)

hourly_partitions = HourlyPartitionsDefinition(start_date=f"{start:%Y-%m-%d-%H:%M}")
daily_partitions = DailyPartitionsDefinition(start_date=f"{start:%Y-%m-%d}")


@asset(partitions_def=hourly_partitions)
def upstream_asset(context: AssetExecutionContext) -> pd.DataFrame:
    return pd.DataFrame({"date": [context.partition_key]})


@asset(
    partitions_def=daily_partitions,
)
def downstream_asset(upstream_asset: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(list(upstream_asset.values()))


result = materialize(
    [*upstream_asset.to_source_assets(), downstream_asset],
    partition_key=start.strftime(daily_partitions.fmt),
)
downstream_asset_data = result.output_for_node("downstream_asset", "result")
assert (
    len(downstream_asset_data) == 24
), "downstream day should map to upstream 24 hours"
