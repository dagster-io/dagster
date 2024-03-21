# pyright: reportPrivateImportUsage=false

import pendulum
import pytest
from dagster import (
    asset,
)
from dagster._check import CheckError
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_checks.time_window_partitioned import (
    build_freshness_checks_for_time_window_partitioned_assets,
)
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
)
from dagster._core.instance import DagsterInstance
from dagster._seven.compat.pendulum import pendulum_freeze_time

from .conftest import add_new_event, assert_check_result


def test_params() -> None:
    """Test definition-time errors and parameter validation for the check builder."""

    @asset(
        partitions_def=DailyPartitionsDefinition(
            start_date=pendulum.datetime(2020, 1, 1, 0, 0, 0, tz="UTC")
        )
    )
    def my_partitioned_asset():
        pass

    result = build_freshness_checks_for_time_window_partitioned_assets(
        assets=[my_partitioned_asset], freshness_cron="0 0 * * *"
    )
    assert len(result) == 1
    check = result[0]
    assert next(iter(check.check_keys)).asset_key == my_partitioned_asset.key
    assert next(iter(check.check_specs)).metadata == {
        "dagster/time_window_partitioned_freshness_params": {
            "dagster/freshness_cron": "0 0 * * *",
            "dagster/freshness_cron_timezone": "UTC",
        }
    }

    result = build_freshness_checks_for_time_window_partitioned_assets(
        assets=[my_partitioned_asset.key], freshness_cron="0 0 * * *", freshness_cron_timezone="UTC"
    )
    assert len(result) == 1
    assert next(iter(result[0].check_keys)).asset_key == my_partitioned_asset.key

    src_asset = SourceAsset("source_asset")
    result = build_freshness_checks_for_time_window_partitioned_assets(
        assets=[src_asset], freshness_cron="0 0 * * *", freshness_cron_timezone="UTC"
    )
    assert len(result) == 1
    assert next(iter(result[0].check_keys)).asset_key == src_asset.key

    result = build_freshness_checks_for_time_window_partitioned_assets(
        assets=[my_partitioned_asset, src_asset],
        freshness_cron="0 0 * * *",
        freshness_cron_timezone="UTC",
    )
    assert len(result) == 2
    assert {next(iter(checks_def.check_keys)).asset_key for checks_def in result} == {
        my_partitioned_asset.key,
        src_asset.key,
    }

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_freshness_checks_for_time_window_partitioned_assets(
            assets=[my_partitioned_asset, my_partitioned_asset],
            freshness_cron="0 0 * * *",
            freshness_cron_timezone="UTC",
        )

    @multi_asset(
        outs={
            "my_partitioned_asset": AssetOut(),
            "b": AssetOut(),
        },
        can_subset=True,
        partitions_def=DailyPartitionsDefinition(
            start_date=pendulum.datetime(2020, 1, 1, 0, 0, 0, tz="UTC")
        ),
    )
    def my_multi_asset(context):
        pass

    result = build_freshness_checks_for_time_window_partitioned_assets(
        assets=[my_multi_asset], freshness_cron="0 0 * * *", freshness_cron_timezone="UTC"
    )
    assert len(result) == 2
    assert {next(iter(checks_def.check_keys)).asset_key for checks_def in result} == set(
        my_multi_asset.keys
    )

    with pytest.raises(Exception, match="freshness_cron must be a valid cron string."):
        build_freshness_checks_for_time_window_partitioned_assets(
            assets=[my_multi_asset], freshness_cron="0 0 * * * *", freshness_cron_timezone="UTC"
        )

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_freshness_checks_for_time_window_partitioned_assets(
            assets=[my_multi_asset, my_multi_asset],
            freshness_cron="0 0 * * *",
            freshness_cron_timezone="UTC",
        )

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_freshness_checks_for_time_window_partitioned_assets(
            assets=[my_multi_asset, my_partitioned_asset],
            freshness_cron="0 0 * * *",
            freshness_cron_timezone="UTC",
        )

    coercible_key = "blah"
    result = build_freshness_checks_for_time_window_partitioned_assets(
        assets=[coercible_key], freshness_cron="0 0 * * *", freshness_cron_timezone="UTC"
    )
    assert len(result) == 1
    assert next(iter(result[0].check_keys)).asset_key == AssetKey.from_coercible(coercible_key)

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_freshness_checks_for_time_window_partitioned_assets(
            assets=[coercible_key, coercible_key],
            freshness_cron="0 0 * * *",
            freshness_cron_timezone="UTC",
        )

    regular_asset_key = AssetKey("regular_asset_key")
    result = build_freshness_checks_for_time_window_partitioned_assets(
        assets=[regular_asset_key], freshness_cron="0 0 * * *", freshness_cron_timezone="UTC"
    )
    assert len(result) == 1
    assert next(iter(result[0].check_keys)).asset_key == regular_asset_key

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_freshness_checks_for_time_window_partitioned_assets(
            assets=[regular_asset_key, regular_asset_key],
            freshness_cron="0 0 * * *",
            freshness_cron_timezone="UTC",
        )


def test_result_cron_param(
    pendulum_aware_report_dagster_event: None,
    instance: DagsterInstance,
) -> None:
    """Move time forward and backward, with a freshness check parameterized with a cron, and ensure that the check passes and fails as expected."""
    partitions_def = DailyPartitionsDefinition(
        start_date=pendulum.datetime(2020, 1, 1, 0, 0, 0, tz="UTC")
    )

    @asset(partitions_def=partitions_def)
    def my_asset():
        pass

    start_time = pendulum.datetime(2021, 1, 3, 1, 0, 0, tz="UTC")  # 2021-01-03 at 01:00:00

    freshness_checks = build_freshness_checks_for_time_window_partitioned_assets(
        assets=[my_asset],
        freshness_cron="0 9 * * *",  # 09:00 UTC
        freshness_cron_timezone="UTC",
    )

    freeze_datetime = start_time
    with pendulum_freeze_time(freeze_datetime):
        # With no events, check fails.
        assert_check_result(
            my_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            False,
            description_match="Partition 2021-01-01 is 960.0 minutes late.",
        )

        # Add an event for an old partition. Still fails
        add_new_event(instance, my_asset.key, "2020-12-31")
        assert_check_result(
            my_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            False,
            description_match="Partition 2021-01-01 is 960.0 minutes late.",
        )

        # Go back in time and add an event for the most recent completed partition previous the
        # cron. Now the check passes.
        add_new_event(instance, my_asset.key, "2021-01-01")
        assert_check_result(
            my_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-01 arrived on time.",
        )

    # Advance a full day. By now, we would expect a new event to have been added.
    # Since that is not the case, we expect the check to fail.
    freeze_datetime = freeze_datetime.add(days=1)  # 2021-01-04 at 01:00:00
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(
            my_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            False,
            description_match="Partition 2021-01-02 is 960.0 minutes late.",
        )

        # Add a partition for the most recently completed day, but before the cron has completed on
        # that day. Expect the check to still fail.
        add_new_event(instance, my_asset.key, "2021-01-03")
        assert_check_result(
            my_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            False,
            description_match="Partition 2021-01-02 is 960.0 minutes late.",
        )

        # Again, go back in time, and add an event for the most recently completed time window
        # before the tick of the cron. Now we expect the check to pass.
        add_new_event(instance, my_asset.key, "2021-01-02")
        assert_check_result(
            my_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-02 arrived on time.",
        )


def test_invalid_runtime_assets(
    pendulum_aware_report_dagster_event: None,
    instance: DagsterInstance,
) -> None:
    """Ensure that the check fails when the asset does not have a TimeWindowPartitionsDefinition."""

    @asset
    def non_partitioned_asset():
        pass

    asset_checks = build_freshness_checks_for_time_window_partitioned_assets(
        assets=[non_partitioned_asset], freshness_cron="0 9 * * *", freshness_cron_timezone="UTC"
    )

    with pytest.raises(CheckError, match="not a TimeWindowPartitionsDefinition."):
        assert_check_result(
            non_partitioned_asset,
            instance,
            asset_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Could not determine last updated timestamp",
        )

    @asset(partitions_def=StaticPartitionsDefinition(["2021-01-01", "2021-01-02"]))
    def static_partitioned_asset():
        pass

    asset_checks = build_freshness_checks_for_time_window_partitioned_assets(
        assets=[static_partitioned_asset], freshness_cron="0 9 * * *", freshness_cron_timezone="UTC"
    )

    with pytest.raises(CheckError, match="not a TimeWindowPartitionsDefinition."):
        assert_check_result(
            static_partitioned_asset,
            instance,
            asset_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Could not determine last updated timestamp",
        )


def test_observations(
    pendulum_aware_report_dagster_event: None,
    instance: DagsterInstance,
) -> None:
    partitions_def = DailyPartitionsDefinition(
        start_date=pendulum.datetime(2020, 1, 1, 0, 0, 0, tz="UTC")
    )

    @asset(partitions_def=partitions_def)
    def my_asset():
        pass

    freshness_checks = build_freshness_checks_for_time_window_partitioned_assets(
        assets=[my_asset],
        freshness_cron="0 9 * * *",
        freshness_cron_timezone="UTC",  # 09:00 UTC
    )

    with pendulum_freeze_time(pendulum.datetime(2021, 1, 3, 1, 0, 0, tz="UTC")):
        add_new_event(instance, my_asset.key, "2021-01-01", is_materialization=False)
        assert_check_result(
            my_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-01 arrived on time.",
        )
