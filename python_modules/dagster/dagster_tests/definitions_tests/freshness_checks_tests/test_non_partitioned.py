# pyright: reportPrivateImportUsage=false

import pendulum
import pytest
from dagster import (
    asset,
)
from dagster._check import CheckError
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.freshness_checks.non_partitioned import (
    build_freshness_checks_for_non_partitioned_assets,
)
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition
from dagster._core.instance import DagsterInstance
from dagster._seven.compat.pendulum import pendulum_freeze_time

from .conftest import add_new_event, assert_check_result


def test_params() -> None:
    @asset
    def my_asset():
        pass

    result = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_asset], maximum_lag_minutes=10
    )
    assert len(result) == 1
    check = result[0]
    assert next(iter(check.check_keys)).asset_key == my_asset.key
    assert next(iter(check.check_specs)).metadata == {
        "dagster/non_partitioned_freshness_params": {
            "dagster/maximum_lag_minutes": 10,
        }
    }

    result = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_asset], freshness_cron="0 0 * * *", maximum_lag_minutes=10
    )
    check = result[0]
    assert next(iter(check.check_specs)).metadata == {
        "dagster/non_partitioned_freshness_params": {
            "dagster/maximum_lag_minutes": 10,
            "dagster/freshness_cron": "0 0 * * *",
            "dagster/freshness_cron_timezone": "UTC",
        }
    }

    result = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_asset.key], maximum_lag_minutes=10
    )
    assert len(result) == 1
    assert next(iter(result[0].check_keys)).asset_key == my_asset.key

    src_asset = SourceAsset("source_asset")
    result = build_freshness_checks_for_non_partitioned_assets(
        assets=[src_asset], maximum_lag_minutes=10
    )
    assert len(result) == 1
    assert next(iter(result[0].check_keys)).asset_key == src_asset.key

    result = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_asset, src_asset], maximum_lag_minutes=10
    )

    assert len(result) == 2
    assert next(iter(result[0].check_keys)).asset_key == my_asset.key

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_freshness_checks_for_non_partitioned_assets(
            assets=[my_asset, my_asset], maximum_lag_minutes=10
        )

    result = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_asset],
        maximum_lag_minutes=10,
        freshness_cron="0 0 * * *",
        freshness_cron_timezone="UTC",
    )
    assert len(result) == 1
    assert next(iter(result[0].check_keys)).asset_key == my_asset.key


@pytest.mark.parametrize(
    "use_materialization",
    [True, False],
    ids=["materialization", "observation"],
)
def test_different_event_types(
    pendulum_aware_report_dagster_event: None, use_materialization: bool, instance: DagsterInstance
) -> None:
    """Test that the freshness check works with different event types."""

    @asset
    def my_asset():
        pass

    start_time = pendulum.datetime(2021, 1, 1, 1, 0, 0, tz="UTC")
    maximum_lag_minutes = 10

    with pendulum_freeze_time(start_time.subtract(minutes=maximum_lag_minutes - 1)):
        add_new_event(instance, my_asset.key, is_materialization=use_materialization)
    with pendulum_freeze_time(start_time):
        freshness_checks = build_freshness_checks_for_non_partitioned_assets(
            assets=[my_asset],
            maximum_lag_minutes=maximum_lag_minutes,
        )
        assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, True)


def test_check_result_cron_non_partitioned(
    pendulum_aware_report_dagster_event: None,
    instance: DagsterInstance,
) -> None:
    """Move time forward and backward, with a freshness check parameterized with a cron, and ensure that the check passes and fails as expected."""

    @asset
    def my_asset():
        pass

    start_time = pendulum.datetime(2021, 1, 1, 1, 0, 0, tz="UTC")
    freshness_cron = "0 0 * * *"  # Every day at midnight.
    freshness_cron_timezone = "UTC"
    maximum_lag_minutes = 10

    freshness_checks = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_asset],
        freshness_cron=freshness_cron,
        maximum_lag_minutes=maximum_lag_minutes,
        freshness_cron_timezone=freshness_cron_timezone,
    )

    freeze_datetime = start_time
    with pendulum_freeze_time(freeze_datetime):
        # With no events, check passes, with description indicating no last updated timestamps could be found.
        assert_check_result(
            my_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Could not determine last updated timestamp",
        )

    # Add an event outside of the allowed time window. Check fails.
    lower_bound = pendulum.datetime(2021, 1, 1, 0, 0, 0, tz="UTC").subtract(
        minutes=maximum_lag_minutes if maximum_lag_minutes else 0
    )
    with pendulum_freeze_time(lower_bound.subtract(minutes=1)):
        add_new_event(instance, my_asset.key)
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, False)

    # Go back in time and add an event within cron-max_lag_minutes.
    with pendulum_freeze_time(lower_bound.add(minutes=1)):
        add_new_event(instance, my_asset.key)
    # Now we expect the check to pass.
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, True)

    # Advance a full day. By now, we would expect a new event to have been added.
    # Since that is not the case, we expect the check to fail.
    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, False)

    # Again, go back in time, and add an event within the time window we're checking.
    with pendulum_freeze_time(
        pendulum.datetime(2021, 1, 2, 0, 0, 0, tz="UTC")
        .subtract(minutes=maximum_lag_minutes if maximum_lag_minutes else 0)
        .add(minutes=1)
    ):
        add_new_event(instance, my_asset.key)
    # Now we expect the check to pass.
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, True)


def test_check_result_lag_only(
    pendulum_aware_report_dagster_event: None,
    instance: DagsterInstance,
) -> None:
    """Move time forward and backward, with a freshness check parameterized with only lag, and ensure that the check passes and fails as expected."""

    @asset
    def my_asset():
        pass

    start_time = pendulum.datetime(2021, 1, 1, 1, 0, 0, tz="UTC")
    maximum_lag_minutes = 10

    freshness_checks = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_asset],
        maximum_lag_minutes=maximum_lag_minutes,
    )

    freeze_datetime = start_time
    with pendulum_freeze_time(freeze_datetime):
        # With no events, check passes, with description indicating that no last updated timestamp could be found.
        assert_check_result(
            my_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Could not determine last updated timestamp",
        )

    # Add an event outside of the allowed time window. Check fails.
    lower_bound = pendulum.datetime(2021, 1, 1, 0, 50, 0, tz="UTC")
    with pendulum_freeze_time(lower_bound.subtract(minutes=1)):
        add_new_event(instance, my_asset.key)
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, False)

    # Go back in time and add an event within the allowed time window.
    with pendulum_freeze_time(lower_bound.add(minutes=1)):
        add_new_event(instance, my_asset.key)
    # Now we expect the check to pass.
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, True)


def test_invalid_runtime_asset(
    pendulum_aware_report_dagster_event: None,
    instance: DagsterInstance,
) -> None:
    """Test that a runtime error is raised when an asset is partitioned."""

    @asset(partitions_def=DailyPartitionsDefinition(start_date=pendulum.datetime(2021, 1, 1)))
    def my_asset():
        pass

    freshness_checks = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_asset],
        maximum_lag_minutes=10,
    )

    with pytest.raises(CheckError, match="Expected non-partitioned asset"):
        assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, True)
