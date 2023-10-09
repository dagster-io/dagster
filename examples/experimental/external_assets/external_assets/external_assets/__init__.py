import datetime

from dagster import AssetCheckResult, AssetKey, TimeWindowPartitionsDefinition, asset_check
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.external_asset import (
    external_assets_from_specs,
)

external_asset_defs = external_assets_from_specs(
    specs=[
        AssetSpec(
            key=AssetKey(["cdn", "raw_logs"]),
            group_name="external_assets",
            partitions_def=TimeWindowPartitionsDefinition(
                start=datetime.datetime.today() - datetime.timedelta(days=100),
                end=datetime.datetime.today(),
                cron_schedule="0 0 * * *",
                fmt="%Y-%m-%d",
            ),
        ),
        AssetSpec(
            key=AssetKey(["cdn", "processed_logs"]),
            deps=[AssetKey(["cdn", "raw_logs"])],
            group_name="external_assets",
            partitions_def=TimeWindowPartitionsDefinition(
                start=datetime.datetime.today() - datetime.timedelta(days=100),
                end=datetime.datetime.today(),
                cron_schedule="0 0 * * *",
                fmt="%Y-%m-%d",
            ),
        ),
    ]
)


@asset_check(
    asset=AssetKey(["cdn", "processed_logs"]), description="Check that my cdn logs asset is valid"
)
def external_asset_check() -> AssetCheckResult:
    return AssetCheckResult(passed=True, metadata={"valid": True})
