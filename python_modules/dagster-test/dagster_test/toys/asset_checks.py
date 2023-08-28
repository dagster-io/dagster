import random
import time

from dagster import (
    AssetCheckResult,
    AssetCheckSeverity,
    AssetCheckSpec,
    MetadataValue,
    Output,
    asset,
    asset_check,
)


@asset(group_name="asset_checks")
def checked_asset():
    return 1


@asset_check(asset=checked_asset, description="A check that fails half the time.")
def random_fail_check():
    random.seed(time.time())
    return AssetCheckResult(
        success=random.choice([False, True]),
        metadata={"timestamp": MetadataValue.float(time.time())},
    )


@asset_check(
    asset=checked_asset, description="A check that always fails, and has several types of metadata."
)
def always_fail():
    return AssetCheckResult(
        success=False,
        metadata={
            "foo": MetadataValue.text("bar"),
            "asset_key": MetadataValue.asset(checked_asset.key),
        },
    )


@asset_check(asset=checked_asset, description="A check that sleeps 30s then succeeds.")
def slow_check():
    time.sleep(30)
    return AssetCheckResult(success=True)


@asset(
    group_name="asset_checks",
    check_specs=[
        AssetCheckSpec(
            name="random_fail_check",
            asset_key="asset_with_same_op_checks",
            description=(
                "An ERROR check calculated in the same op with the asset. It fails half the time."
            ),
            severity=AssetCheckSeverity.ERROR,
        )
    ],
)
def asset_with_check_in_same_op():
    yield Output(1)
    random.seed(time.time())
    yield AssetCheckResult(check_name="random_fail_check", success=random.choice([False, True]))


@asset(group_name="asset_checks", deps=[checked_asset, asset_with_check_in_same_op])
def downstream_asset():
    return 1


def get_checks_and_assets():
    return [
        checked_asset,
        random_fail_check,
        always_fail,
        slow_check,
        asset_with_check_in_same_op,
        downstream_asset,
    ]
