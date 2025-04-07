from dagster import AssetSelection, MetadataValue, asset, define_asset_job
from dagster._core.definitions.new_freshness_policy import TimeWindowFreshnessPolicy


@asset(
    group_name="basic_assets", new_freshness_policy=TimeWindowFreshnessPolicy(time_window_minutes=5)
)
def basic_asset_1(): ...


@asset(group_name="basic_assets")
def basic_asset_2(basic_asset_1): ...


@asset(group_name="basic_assets")
def basic_asset_3(basic_asset_1): ...


@asset(group_name="basic_assets")
def basic_asset_4(basic_asset_2, basic_asset_3): ...


basic_assets_job = define_asset_job(
    "basic_assets_job",
    selection=AssetSelection.groups("basic_assets"),
    metadata={"owner": "data team", "link": MetadataValue.url(url="https://dagster.io")},
)
