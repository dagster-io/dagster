# pylint: disable=redefined-outer-name
from datetime import datetime

from dagster import DailyPartitionsDefinition, HourlyPartitionsDefinition, MetadataValue, asset
from dagster._legacy import AssetGroup

daily_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")


@asset(
    metadata={"owner": "alice@example.com"},
    compute_kind="ipynb",
    partitions_def=daily_partitions_def,
)
def upstream_daily_partitioned_asset():
    pass


@asset(
    metadata={"owner": "alice@example.com"},
    compute_kind="sql",
    partitions_def=daily_partitions_def,
)
def downstream_daily_partitioned_asset(upstream_daily_partitioned_asset):
    assert upstream_daily_partitioned_asset is None


@asset(
    metadata={"owner": "alice@example.com"},
    partitions_def=HourlyPartitionsDefinition(start_date=datetime(2022, 3, 12, 0, 0)),
)
def hourly_partitioned_asset():
    pass


@asset(
    metadata={
        "owner": "bob@example.com",
        "text_metadata": "Text-based metadata about this asset",
        "path": MetadataValue.path("/unpartitioned/asset"),
        "dashboard_url": MetadataValue.url("http://mycoolsite.com/url_for_my_asset"),
    },
)
def unpartitioned_asset():
    pass


partitioned_asset_group = AssetGroup.from_current_module()
