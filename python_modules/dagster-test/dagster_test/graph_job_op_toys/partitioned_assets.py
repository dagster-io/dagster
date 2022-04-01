# pylint: disable=redefined-outer-name
from dagster import AssetGroup, DailyPartitionsDefinition, asset

daily_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")


@asset(partitions_def=daily_partitions_def)
def upstream_daily_partitioned_asset():
    raise Exception("foo")
    pass


@asset(partitions_def=daily_partitions_def)
def downstream_daily_partitioned_asset(upstream_daily_partitioned_asset):
    pass


@asset(partitions_def=daily_partitions_def)
def aodisj(downstream_daily_partitioned_asset):
    pass


partitioned_asset_group = AssetGroup.from_current_module()
