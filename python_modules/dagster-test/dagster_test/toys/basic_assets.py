from dagster import AssetSelection, MetadataValue, asset, define_asset_job
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)


@asset(group_name="basic_assets")
def basic_asset_1(): ...


@asset(group_name="basic_assets")
def basic_asset_2(basic_asset_1): ...


@asset(group_name="basic_assets")
def basic_asset_3(basic_asset_1): ...


@asset(group_name="basic_assets")
def basic_asset_4(basic_asset_2, basic_asset_3): ...


@asset(
    automation_condition=AutomationCondition.on_cron("* * * * *"),
    group_name="SLA_demo",
    check_specs=[
        AssetCheckSpec(
            name="my_favorite_check", asset="my_cron_asset", description="This is my favorite check"
        )
    ],
)
def my_cron_asset(): ...


@asset(group_name="SLA_demo")
def my_sensored_asset(): ...


basic_assets_job = define_asset_job(
    "basic_assets_job",
    selection=AssetSelection.groups("basic_assets"),
    metadata={"owner": "data team", "link": MetadataValue.url(url="https://dagster.io")},
)
