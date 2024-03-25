# pyright: reportPrivateImportUsage=false

import time
from typing import Iterator

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
from dagster._core.definitions.freshness_checks.time_partition import (
    build_time_partition_freshness_checks,
)
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
)
from dagster._core.instance import DagsterInstance
from dagster._seven.compat.pendulum import pendulum_freeze_time
from dagster._utils.env import environ

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

    result = build_time_partition_freshness_checks(
        assets=[my_partitioned_asset], freshness_cron="0 0 * * *"
    )
    assert len(result) == 1
    check = result[0]
    assert next(iter(check.check_keys)).asset_key == my_partitioned_asset.key
    assert next(iter(check.check_specs)).metadata == {
        "dagster/freshness_params": {
            "dagster/freshness_cron": "0 0 * * *",
            "dagster/freshness_cron_timezone": "UTC",
        }
    }

    result = build_time_partition_freshness_checks(
        assets=[my_partitioned_asset.key], freshness_cron="0 0 * * *", freshness_cron_timezone="UTC"
    )
    assert len(result) == 1
    assert next(iter(result[0].check_keys)).asset_key == my_partitioned_asset.key

    src_asset = SourceAsset("source_asset")
    result = build_time_partition_freshness_checks(
        assets=[src_asset], freshness_cron="0 0 * * *", freshness_cron_timezone="UTC"
    )
    assert len(result) == 1
    assert next(iter(result[0].check_keys)).asset_key == src_asset.key

    result = build_time_partition_freshness_checks(
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
        build_time_partition_freshness_checks(
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

    result = build_time_partition_freshness_checks(
        assets=[my_multi_asset], freshness_cron="0 0 * * *", freshness_cron_timezone="UTC"
    )
    assert len(result) == 2
    assert {next(iter(checks_def.check_keys)).asset_key for checks_def in result} == set(
        my_multi_asset.keys
    )

    with pytest.raises(Exception, match="freshness_cron must be a valid cron string."):
        build_time_partition_freshness_checks(
            assets=[my_multi_asset], freshness_cron="0 0 * * * *", freshness_cron_timezone="UTC"
        )

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_time_partition_freshness_checks(
            assets=[my_multi_asset, my_multi_asset],
            freshness_cron="0 0 * * *",
            freshness_cron_timezone="UTC",
        )

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_time_partition_freshness_checks(
            assets=[my_multi_asset, my_partitioned_asset],
            freshness_cron="0 0 * * *",
            freshness_cron_timezone="UTC",
        )

    coercible_key = "blah"
    result = build_time_partition_freshness_checks(
        assets=[coercible_key], freshness_cron="0 0 * * *", freshness_cron_timezone="UTC"
    )
    assert len(result) == 1
    assert next(iter(result[0].check_keys)).asset_key == AssetKey.from_coercible(coercible_key)

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_time_partition_freshness_checks(
            assets=[coercible_key, coercible_key],
            freshness_cron="0 0 * * *",
            freshness_cron_timezone="UTC",
        )

    regular_asset_key = AssetKey("regular_asset_key")
    result = build_time_partition_freshness_checks(
        assets=[regular_asset_key], freshness_cron="0 0 * * *", freshness_cron_timezone="UTC"
    )
    assert len(result) == 1
    assert next(iter(result[0].check_keys)).asset_key == regular_asset_key

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_time_partition_freshness_checks(
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

    freshness_checks = build_time_partition_freshness_checks(
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
            description_match="Partition 2021-01-01 is overdue. Expected a record for the partition within the last 16 hours.",
        )

        # Add an event for an old partition. Still fails
        add_new_event(instance, my_asset.key, "2020-12-31")
        assert_check_result(
            my_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            False,
            description_match="Partition 2021-01-01 is overdue. Expected a record for the partition within the last 16 hours.",
        )

        # Go back in time and add an event for the most recent completed partition previous the
        # cron. Now the check passes.
        add_new_event(instance, my_asset.key, "2021-01-01")
    # Add a bit of time so that the description renders properly.
    freeze_datetime = freeze_datetime.add(seconds=1)
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(
            my_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-01 is fresh. Expected a record for the partition within the last 16 hours 1 second, and found one last updated 1 second ago.",
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
            description_match="Partition 2021-01-02 is overdue. Expected a record for the partition within the last 16 hours 1 second.",
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
            description_match="Partition 2021-01-02 is overdue. Expected a record for the partition within the last 16 hours 1 second.",
        )

        # Again, go back in time, and add an event for the most recently completed time window
        # before the tick of the cron. Now we expect the check to pass.
        add_new_event(instance, my_asset.key, "2021-01-02")

    freeze_datetime = freeze_datetime.add(seconds=1)
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(
            my_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-02 is fresh. Expected a record for the partition within the last 16 hours 2 seconds, and found one last updated 1 second ago.",
        )


def test_invalid_runtime_assets(
    pendulum_aware_report_dagster_event: None,
    instance: DagsterInstance,
) -> None:
    """Ensure that the check fails when the asset does not have a TimeWindowPartitionsDefinition."""

    @asset
    def non_partitioned_asset():
        pass

    asset_checks = build_time_partition_freshness_checks(
        assets=[non_partitioned_asset], freshness_cron="0 9 * * *", freshness_cron_timezone="UTC"
    )

    with pytest.raises(CheckError, match="Asset is not time-window partitioned."):
        assert_check_result(
            non_partitioned_asset,
            instance,
            asset_checks,
            AssetCheckSeverity.WARN,
            True,
        )

    @asset(partitions_def=StaticPartitionsDefinition(["2021-01-01", "2021-01-02"]))
    def static_partitioned_asset():
        pass

    asset_checks = build_time_partition_freshness_checks(
        assets=[static_partitioned_asset], freshness_cron="0 9 * * *", freshness_cron_timezone="UTC"
    )

    with pytest.raises(CheckError, match="Asset is not time-window partitioned."):
        assert_check_result(
            static_partitioned_asset,
            instance,
            asset_checks,
            AssetCheckSeverity.WARN,
            True,
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

    freshness_checks = build_time_partition_freshness_checks(
        assets=[my_asset],
        freshness_cron="0 9 * * *",
        freshness_cron_timezone="UTC",  # 09:00 UTC
    )

    with pendulum_freeze_time(pendulum.datetime(2021, 1, 3, 1, 0, 0, tz="UTC")):
        add_new_event(instance, my_asset.key, "2021-01-01", is_materialization=False)
    with pendulum_freeze_time(pendulum.datetime(2021, 1, 3, 1, 0, 1, tz="UTC")):
        assert_check_result(
            my_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-01 is fresh. Expected a record for the partition within the last 16 hours 1 second, and found one last updated 1 second ago.",
        )


@pytest.fixture
def new_york_time() -> Iterator[None]:
    with environ({"TZ": "America/New_York"}):
        time.tzset()
        yield
    time.tzset()


def test_differing_timezones(
    pendulum_aware_report_dagster_event: None,
    instance: DagsterInstance,
    new_york_time: None,
) -> None:
    """Test the interplay between the three different timezones: the timezone of the cron, the timezone of the asset, and the timezone of the running process."""
    partitions_def = DailyPartitionsDefinition(
        start_date=pendulum.datetime(2020, 1, 1, 0, 0, 0, tz="America/Chicago"),
        timezone="America/Chicago",
    )

    @asset(partitions_def=partitions_def)
    def my_chicago_asset():
        pass

    freshness_checks = build_time_partition_freshness_checks(
        assets=[my_chicago_asset],
        freshness_cron="0 9 * * *",
        freshness_cron_timezone="America/Los_Angeles",  # 09:00 Los Angeles time
    )

    # Start in a neutral hour in all timezones, such that the cron is on the same tick for all, and add a new event. expect the check to pass.
    # Current time is 2021-01-03 at 01:00:00 in America/Chicago, 2021-01-03 at 02:00:00 in America/New_York, and 2021-01-03 at 00:00:00 in America/Los_Angeles
    freeze_datetime = pendulum.datetime(2021, 1, 3, 1, 0, 0, tz="America/Chicago")
    with pendulum_freeze_time(freeze_datetime):
        add_new_event(instance, my_chicago_asset.key, "2021-01-01")
    freeze_datetime = freeze_datetime.add(seconds=1)
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(
            my_chicago_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-01 is fresh. Expected a record for the partition within the last 14 hours 1 second, and found one last updated 1 second ago.",
        )

    # Move forward enough that only the process timezone would have ticked. The check should still pass.
    # Current time is 2021-01-03 at 08:00:01 in America/Chicago, 2021-01-03 at 09:00:01 in America/New_York, and 2021-01-03 at 06:00:01 in America/Los_Angeles
    freeze_datetime = freeze_datetime.add(hours=7)
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(
            my_chicago_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-01 is fresh. Expected a record for the partition within the last 21 hours 1 second, and found one last updated 7 hours 1 second ago.",
        )

    # Then, move forward only enough that in the timezone of the partition, and the process timezone, the cron would have ticked, but not in the timezone of the cron. The check should still therefore pass.
    # Current time is 2021-01-03 at 09:00:00 in America/Chicago, 2021-01-03 at 10:00:00 in America/New_York, and 2021-01-03 at 07:00:00 in America/Los_Angeles
    freeze_datetime = freeze_datetime.add(hours=1)
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(
            my_chicago_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-01 is fresh. Expected a record for the partition within the last 22 hours 1 second, and found one last updated 8 hours 1 second ago.",
        )

    # Finally, move forward enough that the cron has ticked in all timezones, and the new partition isn't present. The check should now fail.
    # Current time is 2021-01-03 at 11:00:01 in America/Chicago, 2021-01-03 at 12:00:01 in America/New_York, and 2021-01-03 at 09:00:01 in America/Los_Angeles
    freeze_datetime = freeze_datetime.add(hours=2)
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(
            my_chicago_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            False,
            description_match="Partition 2021-01-02 is overdue. Expected a record for the partition within the last 1 second.",
        )

        add_new_event(instance, my_chicago_asset.key, "2021-01-02")
    with pendulum_freeze_time(freeze_datetime.add(seconds=1)):
        assert_check_result(
            my_chicago_asset,
            instance,
            freshness_checks,
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-02 is fresh. Expected a record for the partition within the last 2 seconds, and found one last updated 1 second ago",
        )
