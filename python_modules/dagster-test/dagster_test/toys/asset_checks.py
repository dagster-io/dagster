import random

from dagster import AssetCheckResult, asset, asset_check
from dagster._core.definitions.metadata import MetadataValue


@asset(group_name="asset_checks")
def checked_asset():
    return 1


@asset_check(asset=checked_asset, description="A check that fails half the time.")
def random_fail_check(context):
    return AssetCheckResult(
        success=random.choice([True, False]),
        metadata={"foo": "bar"},
    )


@asset_check(
    asset=checked_asset, description="A check that always fails, and has several types of metadata."
)
def always_fail(context):
    return AssetCheckResult(
        success=False,
        metadata={
            "foo": MetadataValue.text("bar"),
            "asset_key": MetadataValue.asset(checked_asset.key),
        },
    )
