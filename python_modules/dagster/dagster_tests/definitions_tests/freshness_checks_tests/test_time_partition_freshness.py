# pyright: reportPrivateImportUsage=false

import hashlib
import time
from typing import Iterator

import pendulum
import pytest
from dagster import (
    asset,
)
from dagster._check import CheckError
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.asset_selection import AssetChecksForAssetKeysSelection
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_checks.time_partition import (
    build_time_partition_freshness_checks,
)
from dagster._core.definitions.freshness_checks.utils import unique_id_from_asset_keys
from dagster._core.definitions.metadata import (
    FloatMetadataValue,
    JsonMetadataValue,
    TimestampMetadataValue,
)
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
)
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
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

    check = build_time_partition_freshness_checks(
        assets=[my_partitioned_asset], deadline_cron="0 0 * * *"
    )

    assert isinstance(check, AssetChecksDefinition)
    assert next(iter(check.check_keys)).asset_key == my_partitioned_asset.key
    assert next(iter(check.check_specs)).metadata == {
        "dagster/freshness_params": {
            "deadline_cron": "0 0 * * *",
            "timezone": "UTC",
        }
    }
    assert (
        check.node_def.name
        == f"freshness_check_{hashlib.md5(str(my_partitioned_asset.key).encode()).hexdigest()[:8]}"
    )

    @asset(
        partitions_def=DailyPartitionsDefinition(
            start_date=pendulum.datetime(2020, 1, 1, 0, 0, 0, tz="UTC")
        )
    )
    def other_partitioned_asset():
        pass

    other_check = build_time_partition_freshness_checks(
        assets=[other_partitioned_asset], deadline_cron="0 0 * * *", timezone="UTC"
    )
    assert isinstance(other_check, AssetChecksDefinition)
    assert not check.node_def.name == other_check.node_def.name

    check = build_time_partition_freshness_checks(
        assets=[my_partitioned_asset.key], deadline_cron="0 0 * * *", timezone="UTC"
    )
    assert isinstance(check, AssetChecksDefinition)
    assert next(iter(check.check_keys)).asset_key == my_partitioned_asset.key

    src_asset = SourceAsset("source_asset")
    check = build_time_partition_freshness_checks(
        assets=[src_asset], deadline_cron="0 0 * * *", timezone="UTC"
    )
    assert isinstance(check, AssetChecksDefinition)
    assert {check_key.asset_key for check_key in check.check_keys} == {src_asset.key}

    check = build_time_partition_freshness_checks(
        assets=[my_partitioned_asset, src_asset],
        deadline_cron="0 0 * * *",
        timezone="UTC",
    )
    assert isinstance(check, AssetChecksDefinition)
    assert {check_key.asset_key for check_key in check.check_keys} == {
        my_partitioned_asset.key,
        src_asset.key,
    }

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_time_partition_freshness_checks(
            assets=[my_partitioned_asset, my_partitioned_asset],
            deadline_cron="0 0 * * *",
            timezone="UTC",
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

    check = build_time_partition_freshness_checks(
        assets=[my_multi_asset], deadline_cron="0 0 * * *", timezone="UTC"
    )
    assert isinstance(check, AssetChecksDefinition)
    assert {check_key.asset_key for check_key in check.check_keys} == set(my_multi_asset.keys)

    with pytest.raises(Exception, match="deadline_cron must be a valid cron string."):
        build_time_partition_freshness_checks(
            assets=[my_multi_asset], deadline_cron="0 0 * * * *", timezone="UTC"
        )

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_time_partition_freshness_checks(
            assets=[my_multi_asset, my_multi_asset],
            deadline_cron="0 0 * * *",
            timezone="UTC",
        )

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_time_partition_freshness_checks(
            assets=[my_multi_asset, my_partitioned_asset],
            deadline_cron="0 0 * * *",
            timezone="UTC",
        )

    coercible_key = "blah"
    check = build_time_partition_freshness_checks(
        assets=[coercible_key], deadline_cron="0 0 * * *", timezone="UTC"
    )
    assert isinstance(check, AssetChecksDefinition)
    assert {check_key.asset_key for check_key in check.check_keys} == {
        AssetKey.from_coercible(coercible_key)
    }

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_time_partition_freshness_checks(
            assets=[coercible_key, coercible_key],
            deadline_cron="0 0 * * *",
            timezone="UTC",
        )

    regular_asset_key = AssetKey("regular_asset_key")
    check = build_time_partition_freshness_checks(
        assets=[regular_asset_key], deadline_cron="0 0 * * *", timezone="UTC"
    )
    assert isinstance(check, AssetChecksDefinition)
    assert next(iter(check.check_keys)).asset_key == regular_asset_key

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_time_partition_freshness_checks(
            assets=[regular_asset_key, regular_asset_key],
            deadline_cron="0 0 * * *",
            timezone="UTC",
        )

    @asset(
        partitions_def=DailyPartitionsDefinition(
            start_date=pendulum.datetime(2020, 1, 1, 0, 0, 0, tz="UTC")
        )
    )
    def my_other_partitioned_asset():
        pass

    check_multiple_assets = build_time_partition_freshness_checks(
        assets=[my_partitioned_asset, my_other_partitioned_asset],
        deadline_cron="0 9 * * *",
    )
    check_multiple_assets_switched_order = build_time_partition_freshness_checks(
        assets=[my_partitioned_asset, my_other_partitioned_asset],
        deadline_cron="0 9 * * *",
    )
    assert check_multiple_assets.node_def.name == check_multiple_assets_switched_order.node_def.name
    unique_id = unique_id_from_asset_keys(
        [my_partitioned_asset.key, my_other_partitioned_asset.key]
    )
    unique_id_switched_order = unique_id_from_asset_keys(
        [my_other_partitioned_asset.key, my_partitioned_asset.key]
    )
    assert check_multiple_assets.node_def.name == f"freshness_check_{unique_id}"
    assert check_multiple_assets.node_def.name == f"freshness_check_{unique_id_switched_order}"


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

    check = build_time_partition_freshness_checks(
        assets=[my_asset],
        deadline_cron="0 9 * * *",  # 09:00 UTC
        timezone="UTC",
    )

    freeze_datetime = start_time
    with pendulum_freeze_time(freeze_datetime):
        # With no events, check fails.
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            # We expected the asset to arrive between the end of the partition window (2021-01-02) and the current time (2021-01-03).
            description_match="Partition 2021-01-01 is overdue. Expected the partition to arrive within the last 1 day, 1 hour.",
            metadata_match={
                "dagster/freshness_params": JsonMetadataValue(
                    {
                        "timezone": "UTC",
                        "deadline_cron": "0 9 * * *",
                    }
                ),
                "dagster/expected_by_timestamp": TimestampMetadataValue(
                    pendulum.datetime(2021, 1, 2, 9, 0, 0, tz="UTC").timestamp()
                ),
                "dagster/overdue_seconds": FloatMetadataValue(57600.0),
            },
        )

        # Add an event for an old partition. Still fails
        add_new_event(instance, my_asset.key, "2020-12-31")
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Partition 2021-01-01 is overdue. Expected the partition to arrive within the last 1 day, 1 hour.",
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
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-01 is fresh. Expected the partition to arrive within the last 1 day, 1 hour, 1 second, and it arrived 1 second ago.",
            metadata_match={
                "dagster/fresh_until_timestamp": TimestampMetadataValue(
                    pendulum.datetime(2021, 1, 3, 9, 0, 0, tz="UTC").timestamp()
                ),
                "dagster/freshness_params": JsonMetadataValue(
                    {"timezone": "UTC", "deadline_cron": "0 9 * * *"}
                ),
                "dagster/last_updated_timestamp": TimestampMetadataValue(
                    freeze_datetime.subtract(seconds=1).timestamp()
                ),
            },
        )

    # Advance a full day. By now, we would expect a new event to have been added.
    # Since that is not the case, we expect the check to fail.
    freeze_datetime = freeze_datetime.add(days=1)  # 2021-01-04 at 01:00:00
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Partition 2021-01-02 is overdue. Expected the partition to arrive within the last 1 day, 1 hour, 1 second.",
        )

        # Add a partition for the most recently completed day, but before the cron has completed on
        # that day. Expect the check to still fail.
        add_new_event(instance, my_asset.key, "2021-01-03")
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Partition 2021-01-02 is overdue. Expected the partition to arrive within the last 1 day, 1 hour, 1 second.",
        )

        # Again, go back in time, and add an event for the most recently completed time window
        # before the tick of the cron. Now we expect the check to pass.
        add_new_event(instance, my_asset.key, "2021-01-02")

    freeze_datetime = freeze_datetime.add(seconds=1)
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-02 is fresh. Expected the partition to arrive within the last 1 day, 1 hour, 2 seconds, and it arrived 1 second ago.",
        )


def test_invalid_runtime_assets(
    pendulum_aware_report_dagster_event: None,
    instance: DagsterInstance,
) -> None:
    """Ensure that the check fails when the asset does not have a TimeWindowPartitionsDefinition."""

    @asset
    def non_partitioned_asset():
        pass

    check = build_time_partition_freshness_checks(
        assets=[non_partitioned_asset], deadline_cron="0 9 * * *", timezone="UTC"
    )

    with pytest.raises(CheckError, match="Asset is not time-window partitioned."):
        assert_check_result(
            non_partitioned_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
        )

    @asset(partitions_def=StaticPartitionsDefinition(["2021-01-01", "2021-01-02"]))
    def static_partitioned_asset():
        pass

    check = build_time_partition_freshness_checks(
        assets=[static_partitioned_asset], deadline_cron="0 9 * * *", timezone="UTC"
    )

    with pytest.raises(CheckError, match="Asset is not time-window partitioned."):
        assert_check_result(
            static_partitioned_asset,
            instance,
            [check],
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

    check = build_time_partition_freshness_checks(
        assets=[my_asset],
        deadline_cron="0 9 * * *",
        timezone="UTC",  # 09:00 UTC
    )

    with pendulum_freeze_time(pendulum.datetime(2021, 1, 3, 1, 0, 0, tz="UTC")):
        add_new_event(instance, my_asset.key, "2021-01-01", is_materialization=False)
    with pendulum_freeze_time(pendulum.datetime(2021, 1, 3, 1, 0, 1, tz="UTC")):
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-01 is fresh. Expected the partition to arrive within the last 1 day, 1 hour, 1 second, and it arrived 1 second ago.",
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

    check = build_time_partition_freshness_checks(
        assets=[my_chicago_asset],
        deadline_cron="0 9 * * *",
        timezone="America/Los_Angeles",  # 09:00 Los Angeles time
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
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-01 is fresh. Expected the partition to arrive within the last 1 day, 1 hour, 1 second, and it arrived 1 second ago.",
        )

    # Move forward enough that only the process timezone would have ticked. The check should still pass.
    # Current time is 2021-01-03 at 08:00:01 in America/Chicago, 2021-01-03 at 09:00:01 in America/New_York, and 2021-01-03 at 06:00:01 in America/Los_Angeles
    freeze_datetime = freeze_datetime.add(hours=7)
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(
            my_chicago_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-01 is fresh. Expected the partition to arrive within the last 1 day, 8 hours, 1 second, and it arrived 7 hours, 1 second ago.",
        )

    # Then, move forward only enough that in the timezone of the partition, and the process timezone, the cron would have ticked, but not in the timezone of the cron. The check should still therefore pass.
    # Current time is 2021-01-03 at 09:00:00 in America/Chicago, 2021-01-03 at 10:00:00 in America/New_York, and 2021-01-03 at 07:00:00 in America/Los_Angeles
    freeze_datetime = freeze_datetime.add(hours=1)
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(
            my_chicago_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-01 is fresh. Expected the partition to arrive within the last 1 day, 9 hours, 1 second, and it arrived 8 hours, 1 second ago.",
        )

    # Finally, move forward enough that the cron has ticked in all timezones, and the new partition isn't present. The check should now fail.
    # Current time is 2021-01-03 at 11:00:01 in America/Chicago, 2021-01-03 at 12:00:01 in America/New_York, and 2021-01-03 at 09:00:01 in America/Los_Angeles
    freeze_datetime = freeze_datetime.add(hours=2)
    with pendulum_freeze_time(freeze_datetime):
        assert_check_result(
            my_chicago_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Partition 2021-01-02 is overdue. Expected the partition to arrive within the last 11 hours, 1 second.",
        )

        add_new_event(instance, my_chicago_asset.key, "2021-01-02")
    with pendulum_freeze_time(freeze_datetime.add(seconds=1)):
        assert_check_result(
            my_chicago_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-02 is fresh. Expected the partition to arrive within the last 11 hours, 2 seconds, and it arrived 1 second ago",
        )


def test_subset_freshness_checks(instance: DagsterInstance):
    """Test the multi asset case, ensure that the freshness check can be subsetted to execute only
    on a subset of assets.
    """

    @asset(
        partitions_def=DailyPartitionsDefinition(
            start_date=pendulum.datetime(2020, 1, 1, 0, 0, 0, tz="UTC")
        )
    )
    def my_asset():
        pass

    # Test multiple different partition defs
    @asset(
        partitions_def=HourlyPartitionsDefinition(
            start_date=pendulum.datetime(2020, 1, 1, 0, 0, 0, tz="UTC")
        )
    )
    def my_other_asset():
        pass

    check = build_time_partition_freshness_checks(
        assets=[my_asset, my_other_asset],
        deadline_cron="0 9 * * *",
        timezone="UTC",  # 09:00 UTC
    )
    single_check_job = define_asset_job(
        "the_job", selection=AssetChecksForAssetKeysSelection(selected_asset_keys=[my_asset.key])
    )
    both_checks_job = define_asset_job(
        "both_checks_job",
        selection=AssetChecksForAssetKeysSelection(
            selected_asset_keys=[my_asset.key, my_other_asset.key]
        ),
    )
    defs = Definitions(
        assets=[my_asset, my_other_asset],
        asset_checks=[check],
        jobs=[single_check_job, both_checks_job],
    )
    job_def = defs.get_job_def("the_job")
    result = job_def.execute_in_process(instance=instance)
    assert result.success
    # Only one asset check should have occurred, and it should be for `my_asset`.
    assert len(result.get_asset_check_evaluations()) == 1
    assert result.get_asset_check_evaluations()[0].asset_key == my_asset.key
    assert not result.get_asset_check_evaluations()[0].passed

    both_checks_job_def = defs.get_job_def("both_checks_job")
    result = both_checks_job_def.execute_in_process(instance=instance)
    assert result.success
    # Both asset checks should have occurred.
    assert len(result.get_asset_check_evaluations()) == 2
    assert {evaluation.asset_key for evaluation in result.get_asset_check_evaluations()} == {
        my_asset.key,
        my_other_asset.key,
    }
    assert not all(evaluation.passed for evaluation in result.get_asset_check_evaluations())


def test_observation_descriptions(
    pendulum_aware_report_dagster_event: None, instance: DagsterInstance
) -> None:
    @asset(
        partitions_def=DailyPartitionsDefinition(
            start_date=pendulum.datetime(2020, 1, 1, 0, 0, 0, tz="UTC")
        )
    )
    def my_asset():
        pass

    start_time = pendulum.datetime(
        2021, 1, 3, 9, 0, 1, tz="UTC"
    )  # 2021-01-03 at 09:00:00. We expect the 2021-01-02 partition to be fresh.

    check = build_time_partition_freshness_checks(
        assets=[my_asset],
        deadline_cron="0 9 * * *",
    )
    # First, create an event that is outside of the allowed time window.
    with pendulum_freeze_time(pendulum.datetime(2021, 1, 1, 1, 0, 0, tz="UTC")):
        add_new_event(instance, my_asset.key, is_materialization=False, partition_key="2021-01-01")
    with pendulum_freeze_time(start_time):
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Partition 2021-01-02 is overdue. Expected the partition to arrive within the last 9 hours, 1 second.",
        )

        add_new_event(
            instance,
            my_asset.key,
            is_materialization=False,
            override_timestamp=start_time.subtract(minutes=2).timestamp(),
            partition_key="2021-01-01",
        )
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Partition 2021-01-02 is overdue. Expected the partition to arrive within the last 9 hours, 1 second.",
        )

        # Create an observation event within the allotted time window, with an up to date last update time. Description should change.
        add_new_event(
            instance,
            my_asset.key,
            is_materialization=False,
            override_timestamp=start_time.subtract(minutes=1).timestamp(),
            partition_key="2021-01-02",
        )
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Partition 2021-01-02 is fresh. Expected the partition to arrive within the last 9 hours, 1 second, and it arrived 1 minute ago.",
        )
