# pyright: reportPrivateImportUsage=false

import datetime
import json
import time
from typing import Iterator

import pytest
from dagster import asset
from dagster._check import CheckError
from dagster._core.definitions.asset_check_factories.freshness_checks.time_partition import (
    build_time_partition_freshness_checks,
)
from dagster._core.definitions.asset_check_factories.utils import (
    unique_id_from_asset_and_check_keys,
)
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.asset_selection import AssetChecksForAssetKeysSelection
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import JsonMetadataValue, TimestampMetadataValue
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
)
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import freeze_time
from dagster._time import create_datetime, get_timezone
from dagster._utils.env import environ
from dagster._utils.security import non_secure_md5_hash_str

from dagster_tests.definitions_tests.freshness_checks_tests.conftest import (
    add_new_event,
    assert_check_result,
)


def test_params() -> None:
    """Test definition-time errors and parameter validation for the check builder."""

    @asset(
        partitions_def=DailyPartitionsDefinition(start_date=create_datetime(2020, 1, 1, 0, 0, 0))
    )
    def my_partitioned_asset():
        pass

    check = build_time_partition_freshness_checks(
        assets=[my_partitioned_asset], deadline_cron="0 0 * * *"
    )[0]

    assert isinstance(check, AssetChecksDefinition)
    assert next(iter(check.check_keys)).asset_key == my_partitioned_asset.key
    assert next(iter(check.check_specs)).metadata == {
        "dagster/freshness_params": JsonMetadataValue(
            {
                "deadline_cron": "0 0 * * *",
                "timezone": "UTC",
            }
        )
    }
    assert (
        check.node_def.name
        == f"freshness_check_{non_secure_md5_hash_str(json.dumps([str(my_partitioned_asset.key)]).encode())[:8]}"
    )

    @asset(
        partitions_def=DailyPartitionsDefinition(start_date=create_datetime(2020, 1, 1, 0, 0, 0))
    )
    def other_partitioned_asset():
        pass

    other_check = build_time_partition_freshness_checks(
        assets=[other_partitioned_asset], deadline_cron="0 0 * * *", timezone="UTC"
    )[0]
    assert isinstance(other_check, AssetChecksDefinition)
    assert not check.node_def.name == other_check.node_def.name

    check = build_time_partition_freshness_checks(
        assets=[my_partitioned_asset.key], deadline_cron="0 0 * * *", timezone="UTC"
    )[0]
    assert isinstance(check, AssetChecksDefinition)
    assert next(iter(check.check_keys)).asset_key == my_partitioned_asset.key

    src_asset = SourceAsset("source_asset")
    check = build_time_partition_freshness_checks(
        assets=[src_asset], deadline_cron="0 0 * * *", timezone="UTC"
    )[0]
    assert isinstance(check, AssetChecksDefinition)
    assert {check_key.asset_key for check_key in check.check_keys} == {src_asset.key}

    check = build_time_partition_freshness_checks(
        assets=[my_partitioned_asset, src_asset],
        deadline_cron="0 0 * * *",
        timezone="UTC",
    )[0]
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
        partitions_def=DailyPartitionsDefinition(start_date=create_datetime(2020, 1, 1, 0, 0, 0)),
    )
    def my_multi_asset(context):
        pass

    check = build_time_partition_freshness_checks(
        assets=[my_multi_asset], deadline_cron="0 0 * * *", timezone="UTC"
    )[0]
    assert isinstance(check, AssetChecksDefinition)
    assert {check_key.asset_key for check_key in check.check_keys} == set(my_multi_asset.keys)

    with pytest.raises(Exception, match="Invalid cron string."):
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
    )[0]
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
    )[0]
    assert isinstance(check, AssetChecksDefinition)
    assert next(iter(check.check_keys)).asset_key == regular_asset_key

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_time_partition_freshness_checks(
            assets=[regular_asset_key, regular_asset_key],
            deadline_cron="0 0 * * *",
            timezone="UTC",
        )

    @asset(
        partitions_def=DailyPartitionsDefinition(start_date=create_datetime(2020, 1, 1, 0, 0, 0))
    )
    def my_other_partitioned_asset():
        pass

    check_multiple_assets = build_time_partition_freshness_checks(
        assets=[my_partitioned_asset, my_other_partitioned_asset],
        deadline_cron="0 9 * * *",
    )[0]
    check_multiple_assets_switched_order = build_time_partition_freshness_checks(
        assets=[my_partitioned_asset, my_other_partitioned_asset],
        deadline_cron="0 9 * * *",
    )[0]
    assert check_multiple_assets.node_def.name == check_multiple_assets_switched_order.node_def.name
    unique_id = unique_id_from_asset_and_check_keys(
        [my_partitioned_asset.key, my_other_partitioned_asset.key]
    )
    unique_id_switched_order = unique_id_from_asset_and_check_keys(
        [my_other_partitioned_asset.key, my_partitioned_asset.key]
    )
    assert check_multiple_assets.node_def.name == f"freshness_check_{unique_id}"
    assert check_multiple_assets.node_def.name == f"freshness_check_{unique_id_switched_order}"


def test_result_cron_param(
    instance: DagsterInstance,
) -> None:
    """Move time forward and backward, with a freshness check parameterized with a cron, and ensure that the check passes and fails as expected."""
    partitions_def = DailyPartitionsDefinition(start_date=create_datetime(2020, 1, 1, 0, 0, 0))

    @asset(partitions_def=partitions_def)
    def my_asset():
        pass

    start_time = create_datetime(2021, 1, 3, 1, 0, 0)  # 2021-01-03 at 01:00:00

    check = build_time_partition_freshness_checks(
        assets=[my_asset],
        deadline_cron="0 9 * * *",  # 09:00 UTC
        timezone="UTC",
    )[0]

    freeze_datetime = start_time
    with freeze_time(freeze_datetime):
        # With no events, check fails.
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            # We expected the asset to arrive between the end of the partition window (2021-01-02) and the current time (2021-01-03).
            description_match="The asset has never been observed/materialized.",
            metadata_match={
                "dagster/freshness_params": JsonMetadataValue(
                    {
                        "timezone": "UTC",
                        "deadline_cron": "0 9 * * *",
                    }
                ),
                "dagster/latest_cron_tick_timestamp": TimestampMetadataValue(
                    create_datetime(2021, 1, 2, 9, 0, 0).timestamp()
                ),
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
            description_match="Asset is overdue",
        )

        # Go back in time and add an event for the most recent completed partition previous the
        # cron. Now the check passes.
        add_new_event(instance, my_asset.key, "2021-01-01")
    # Add a bit of time so that the description renders properly.
    freeze_datetime = freeze_datetime + datetime.timedelta(seconds=1)
    with freeze_time(freeze_datetime):
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Asset is currently fresh",
            metadata_match={
                "dagster/fresh_until_timestamp": TimestampMetadataValue(
                    create_datetime(2021, 1, 3, 9, 0, 0).timestamp()
                ),
                "dagster/freshness_params": JsonMetadataValue(
                    {"timezone": "UTC", "deadline_cron": "0 9 * * *"}
                ),
                "dagster/latest_cron_tick_timestamp": TimestampMetadataValue(
                    create_datetime(2021, 1, 2, 9, 0, 0).timestamp()
                ),
            },
        )

    # Advance a full day. By now, we would expect a new event to have been added.
    # Since that is not the case, we expect the check to fail.
    freeze_datetime = freeze_datetime + datetime.timedelta(days=1)  # 2021-01-04 at 01:00:00
    with freeze_time(freeze_datetime):
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Asset is overdue.",
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
            description_match="Asset is overdue.",
        )

        # Again, go back in time, and add an event for the most recently completed time window
        # before the tick of the cron. Now we expect the check to pass.
        add_new_event(instance, my_asset.key, "2021-01-02")

    freeze_datetime = freeze_datetime + datetime.timedelta(seconds=1)
    with freeze_time(freeze_datetime):
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Asset is currently fresh",
        )


def test_invalid_runtime_assets(
    instance: DagsterInstance,
) -> None:
    """Ensure that the check fails when the asset does not have a TimeWindowPartitionsDefinition."""

    @asset
    def non_partitioned_asset():
        pass

    check = build_time_partition_freshness_checks(
        assets=[non_partitioned_asset], deadline_cron="0 9 * * *", timezone="UTC"
    )[0]

    with pytest.raises(CheckError, match="not a TimeWindowPartitionsDefinition"):
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
    )[0]

    with pytest.raises(CheckError, match="not a TimeWindowPartitionsDefinition"):
        assert_check_result(
            static_partitioned_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
        )


def test_observations(
    instance: DagsterInstance,
) -> None:
    partitions_def = DailyPartitionsDefinition(start_date=create_datetime(2020, 1, 1, 0, 0, 0))

    @asset(partitions_def=partitions_def)
    def my_asset():
        pass

    check = build_time_partition_freshness_checks(
        assets=[my_asset],
        deadline_cron="0 9 * * *",
        timezone="UTC",  # 09:00 UTC
    )[0]

    with freeze_time(create_datetime(2021, 1, 3, 1, 0, 0)):
        add_new_event(instance, my_asset.key, "2021-01-01", is_materialization=False)
    with freeze_time(create_datetime(2021, 1, 3, 1, 0, 1)):
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Asset is currently fresh",
        )


def test_materialization_and_observation(instance: DagsterInstance) -> None:
    """Test that freshness check works when latest event is an observation, but it has no last_updated_time."""

    @asset(
        partitions_def=DailyPartitionsDefinition(start_date=create_datetime(2020, 1, 1, 0, 0, 0))
    )
    def my_asset():
        pass

    check = build_time_partition_freshness_checks(
        assets=[my_asset],
        deadline_cron="0 9 * * *",
        timezone="UTC",  # 09:00 UTC
    )[0]

    with freeze_time(create_datetime(2021, 1, 3, 1, 0, 0)):
        add_new_event(instance, my_asset.key, "2021-01-01", is_materialization=True)
        add_new_event(
            instance, my_asset.key, "2021-01-02", is_materialization=False, include_metadata=False
        )
    with freeze_time(create_datetime(2021, 1, 3, 1, 0, 1)):
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Asset is currently fresh",
        )


@pytest.fixture
def new_york_time() -> Iterator[None]:
    with environ({"TZ": "America/New_York"}):
        time.tzset()
        yield
    time.tzset()


def test_differing_timezones(
    instance: DagsterInstance,
    new_york_time: None,
) -> None:
    """Test the interplay between the three different timezones: the timezone of the cron, the timezone of the asset, and the timezone of the running process."""
    partitions_def = DailyPartitionsDefinition(
        start_date=datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo=get_timezone("America/Chicago")),
        timezone="America/Chicago",
    )

    @asset(partitions_def=partitions_def)
    def my_chicago_asset():
        pass

    check = build_time_partition_freshness_checks(
        assets=[my_chicago_asset],
        deadline_cron="0 9 * * *",
        timezone="America/Los_Angeles",  # 09:00 Los Angeles time
    )[0]

    # Start in a neutral hour in all timezones, such that the cron is on the same tick for all, and add a new event. expect the check to pass.
    # Current time is 2021-01-03 at 01:00:00 in America/Chicago, 2021-01-03 at 02:00:00 in America/New_York, and 2021-01-03 at 00:00:00 in America/Los_Angeles
    freeze_datetime = datetime.datetime(2021, 1, 3, 1, 0, 0, tzinfo=get_timezone("America/Chicago"))
    with freeze_time(freeze_datetime):
        add_new_event(instance, my_chicago_asset.key, "2021-01-01")
    freeze_datetime = freeze_datetime + datetime.timedelta(seconds=1)
    with freeze_time(freeze_datetime):
        assert_check_result(
            my_chicago_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Asset is currently fresh",
        )

    # Move forward enough that only the process timezone would have ticked. The check should still pass.
    # Current time is 2021-01-03 at 08:00:01 in America/Chicago, 2021-01-03 at 09:00:01 in America/New_York, and 2021-01-03 at 06:00:01 in America/Los_Angeles
    freeze_datetime = freeze_datetime + datetime.timedelta(hours=7)
    with freeze_time(freeze_datetime):
        assert_check_result(
            my_chicago_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Asset is currently fresh",
        )

    # Then, move forward only enough that in the timezone of the partition, and the process timezone, the cron would have ticked, but not in the timezone of the cron. The check should still therefore pass.
    # Current time is 2021-01-03 at 09:00:00 in America/Chicago, 2021-01-03 at 10:00:00 in America/New_York, and 2021-01-03 at 07:00:00 in America/Los_Angeles
    freeze_datetime = freeze_datetime + datetime.timedelta(hours=1)
    with freeze_time(freeze_datetime):
        assert_check_result(
            my_chicago_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Asset is currently fresh",
        )

    # Finally, move forward enough that the cron has ticked in all timezones, and the new partition isn't present. The check should now fail.
    # Current time is 2021-01-03 at 11:00:01 in America/Chicago, 2021-01-03 at 12:00:01 in America/New_York, and 2021-01-03 at 09:00:01 in America/Los_Angeles
    freeze_datetime = freeze_datetime + datetime.timedelta(hours=2)
    with freeze_time(freeze_datetime):
        assert_check_result(
            my_chicago_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Asset is overdue.",
        )

        add_new_event(instance, my_chicago_asset.key, "2021-01-02")
    with freeze_time(freeze_datetime + datetime.timedelta(seconds=1)):
        assert_check_result(
            my_chicago_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Asset is currently fresh",
        )


def test_subset_freshness_checks(instance: DagsterInstance):
    """Test the multi asset case, ensure that the freshness check can be subsetted to execute only
    on a subset of assets.
    """

    @asset(
        partitions_def=DailyPartitionsDefinition(start_date=create_datetime(2020, 1, 1, 0, 0, 0))
    )
    def my_asset():
        pass

    # Test multiple different partition defs
    @asset(
        partitions_def=HourlyPartitionsDefinition(start_date=create_datetime(2020, 1, 1, 0, 0, 0))
    )
    def my_other_asset():
        pass

    check = build_time_partition_freshness_checks(
        assets=[my_asset, my_other_asset],
        deadline_cron="0 9 * * *",
        timezone="UTC",  # 09:00 UTC
    )[0]
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


def test_observation_descriptions(instance: DagsterInstance) -> None:
    @asset(
        partitions_def=DailyPartitionsDefinition(start_date=create_datetime(2020, 1, 1, 0, 0, 0))
    )
    def my_asset():
        pass

    start_time = create_datetime(
        2021, 1, 3, 9, 0, 1
    )  # 2021-01-03 at 09:00:00. We expect the 2021-01-02 partition to be fresh.

    check = build_time_partition_freshness_checks(
        assets=[my_asset],
        deadline_cron="0 9 * * *",
    )[0]
    # First, create an event that is outside of the allowed time window.
    with freeze_time(create_datetime(2021, 1, 1, 1, 0, 0)):
        add_new_event(instance, my_asset.key, is_materialization=False, partition_key="2021-01-01")
    # Asset is in an unknown state since we haven't had any observation events during this time window.
    with freeze_time(start_time):
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Asset is overdue.",
        )

        add_new_event(
            instance,
            my_asset.key,
            is_materialization=False,
            override_timestamp=(start_time - datetime.timedelta(minutes=2)).timestamp(),
            partition_key="2021-01-01",
        )
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Asset is overdue.",
        )

        # Create an observation event within the allotted time window, with an up to date last update time. Description should change.
        add_new_event(
            instance,
            my_asset.key,
            is_materialization=False,
            override_timestamp=(start_time - datetime.timedelta(minutes=1)).timestamp(),
            partition_key="2021-01-02",
        )
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Asset is currently fresh",
        )
