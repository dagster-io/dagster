# pylint: disable=redefined-outer-name
from datetime import datetime

from dagster import AssetGroup, DailyPartitionsDefinition, HourlyPartitionsDefinition, asset

daily_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")


@asset(partitions_def=daily_partitions_def)
def upstream_daily_partitioned_asset():
    pass


@asset(partitions_def=daily_partitions_def)
def downstream_daily_partitioned_asset(upstream_daily_partitioned_asset):
    assert upstream_daily_partitioned_asset is None


@asset(partitions_def=HourlyPartitionsDefinition(start_date=datetime(2022, 3, 12, 0, 0)))
def hourly_partitioned_asset():
    pass


@asset
def unpartitioned_asset():
    pass


partitioned_asset_group = AssetGroup.from_current_module()
