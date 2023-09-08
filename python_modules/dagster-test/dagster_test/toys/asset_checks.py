import random
import time

from dagster import (
    AssetCheckResult,
    AssetCheckSeverity,
    AssetCheckSpec,
    AssetKey,
    AssetOut,
    DailyPartitionsDefinition,
    MetadataValue,
    Output,
    asset,
    asset_check,
    multi_asset,
)


@asset(key_prefix="test_prefix", group_name="asset_checks")
def checked_asset():
    return 1


@asset_check(asset=checked_asset, description="A check that fails half the time.")
def random_fail_check(checked_asset):
    random.seed(time.time())
    return AssetCheckResult(
        success=random.choice([False, True]),
        metadata={"timestamp": MetadataValue.float(time.time())},
    )


@asset_check(
    asset=checked_asset,
    description="A check that fails half the time.",
)
def severe_random_fail_check():
    random.seed(time.time())
    return AssetCheckResult(
        success=random.choice([False, True]),
        metadata={"timestamp": MetadataValue.float(time.time())},
        severity=AssetCheckSeverity.ERROR,
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
        severity=AssetCheckSeverity.WARN,
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
            asset="asset_with_check_in_same_op",
            description=(
                "An ERROR check calculated in the same op with the asset. It fails half the time."
            ),
        )
    ],
)
def asset_with_check_in_same_op():
    yield Output(1)
    random.seed(time.time())
    yield AssetCheckResult(check_name="random_fail_check", success=random.choice([False, True]))


@asset(group_name="asset_checks")
def check_exception_asset():
    return 1


@asset_check(
    asset=check_exception_asset, description="A check that hits an exception half the time."
)
def exception_check():
    random.seed(time.time())
    if random.choice([False, True]):
        raise Exception("This check failed!")
    return AssetCheckResult(success=True)


@asset_check(
    asset=check_exception_asset,
    description="A severe check that hits an exception half the time.",
)
def severe_exception_check():
    random.seed(time.time())
    if random.choice([False, True]):
        raise Exception("This check failed!")
    return AssetCheckResult(success=True)


@asset(
    group_name="asset_checks",
    partitions_def=DailyPartitionsDefinition(
        start_date="2020-01-01",
    ),
)
def partitioned_asset(_):
    return 1


@asset_check(
    asset=partitioned_asset,
    description="A check that fails half the time.",
)
def random_fail_check_on_partitioned_asset():
    random.seed(time.time())
    return AssetCheckResult(
        success=random.choice([False, True]),
    )


@asset(
    group_name="asset_checks",
    deps=[checked_asset, asset_with_check_in_same_op, check_exception_asset, partitioned_asset],
)
def downstream_asset():
    return 1


@multi_asset(
    outs={
        "one": AssetOut(key="multi_asset_piece_1", group_name="asset_checks", is_required=False),
        "two": AssetOut(key="multi_asset_piece_2", group_name="asset_checks", is_required=False),
    },
    check_specs=[AssetCheckSpec("my_check", asset="multi_asset_piece_1")],
    can_subset=True,
)
def multi_asset_1_and_2(context):
    if AssetKey("multi_asset_piece_1") in context.selected_asset_keys:
        yield Output(1, output_name="one")
        yield AssetCheckResult(success=True, metadata={"foo": "bar"})
    if AssetKey("multi_asset_piece_2") in context.selected_asset_keys:
        yield Output(1, output_name="two")


def get_checks_and_assets():
    return [
        checked_asset,
        random_fail_check,
        severe_random_fail_check,
        always_fail,
        slow_check,
        asset_with_check_in_same_op,
        downstream_asset,
        check_exception_asset,
        exception_check,
        severe_exception_check,
        partitioned_asset,
        random_fail_check_on_partitioned_asset,
        multi_asset_1_and_2,
    ]
