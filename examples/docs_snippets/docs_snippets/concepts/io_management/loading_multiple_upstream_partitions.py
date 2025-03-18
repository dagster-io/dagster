from datetime import datetime

import pandas as pd

import dagster as dg

start = datetime(2022, 1, 1)

hourly_partitions = dg.HourlyPartitionsDefinition(start_date=f"{start:%Y-%m-%d-%H:%M}")
daily_partitions = dg.DailyPartitionsDefinition(start_date=f"{start:%Y-%m-%d}")


@dg.asset(partitions_def=hourly_partitions)
def upstream_asset(context: dg.AssetExecutionContext) -> pd.DataFrame:
    return pd.DataFrame({"date": [context.partition_key]})


@dg.asset(
    partitions_def=daily_partitions,
)
def downstream_asset(upstream_asset: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(list(upstream_asset.values()))


result = dg.materialize(
    [*upstream_asset.to_source_assets(), downstream_asset],
    partition_key=start.strftime(daily_partitions.fmt),
)
downstream_asset_data = result.output_for_node("downstream_asset", "result")
assert len(downstream_asset_data) == 24, (
    "downstream day should map to upstream 24 hours"
)
