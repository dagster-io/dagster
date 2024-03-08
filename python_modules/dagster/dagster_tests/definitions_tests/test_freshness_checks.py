# pyright: reportPrivateImportUsage=false
import logging
from enum import Enum
from typing import Iterator, Optional, Sequence

import pendulum
import pytest
from dagster import (
    asset,
    define_asset_job,
)
from dagster._check import CheckError
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.data_time import DATA_TIME_METADATA_KEY
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey, AssetMaterialization, AssetObservation
from dagster._core.definitions.freshness_checks import build_freshness_checks
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
)
from dagster._core.events.log import EventLogEntry
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._core.instance import DagsterInstance
from dagster._core.instance_for_test import instance_for_test
from mock import patch


@pytest.fixture(name="instance")
def instance_fixture() -> Iterator[DagsterInstance]:
    with instance_for_test() as instance:
        yield instance


@pytest.fixture(name="pendulum_aware_report_dagster_event")
def pendulum_aware_report_dagster_event_fixture() -> Iterator[None]:
    def pendulum_aware_report_dagster_event(
        self,
        dagster_event,
        run_id,
        log_level=logging.INFO,
    ) -> None:
        """If pendulum.test() is active, intercept event log records to have a timestamp no greater than the frozen time.

        This works best if you have a frozen time that is far in the past, so the decision to use the frozen time is clear.
        """
        event_record = EventLogEntry(
            user_message="",
            level=log_level,
            job_name=dagster_event.job_name,
            run_id=run_id,
            error_info=None,
            timestamp=pendulum.now("UTC").timestamp(),
            step_key=dagster_event.step_key,
            dagster_event=dagster_event,
        )
        self.handle_new_event(event_record)

    with patch(
        "dagster._core.instance.DagsterInstance.report_dagster_event",
        pendulum_aware_report_dagster_event,
    ):
        yield


class RecordTypeForTest(Enum):
    materialization = "materialization"
    observation = "observation"
    mat_first = "mat_first"
    obs_first = "obs_first"


def execute_check_for_asset(
    assets=None,
    asset_checks=None,
    instance=None,
) -> ExecuteInProcessResult:
    the_job = define_asset_job(
        name="test_asset_job", selection=AssetSelection.checks(*asset_checks)
    )

    defs = Definitions(assets=assets, asset_checks=asset_checks, jobs=[the_job])
    job_def = defs.get_job_def("test_asset_job")
    return job_def.execute_in_process(instance=instance)


def _assert_check_result(
    the_asset: AssetsDefinition,
    instance: DagsterInstance,
    freshness_checks: Sequence[AssetChecksDefinition],
    severity: AssetCheckSeverity,
    expected_pass: bool,
) -> None:
    result = execute_check_for_asset(
        assets=[the_asset],
        asset_checks=freshness_checks,
        instance=instance,
    )
    assert result.success
    assert len(result.get_asset_check_evaluations()) == 1
    assert result.get_asset_check_evaluations()[0].passed == expected_pass
    assert result.get_asset_check_evaluations()[0].severity == severity


def add_new_event(
    instance: DagsterInstance,
    asset_key: AssetKey,
    partition_key: Optional[str] = None,
    is_materialization: bool = True,
):
    klass = AssetMaterialization if is_materialization else AssetObservation
    metadata = (
        {DATA_TIME_METADATA_KEY: pendulum.now("UTC").timestamp()}
        if not is_materialization
        else None
    )
    instance.report_runless_asset_event(
        klass(
            asset_key=asset_key,
            metadata=metadata,
            partition=partition_key,
        )
    )


def test_freshness_checks() -> None:
    @asset
    def my_asset():
        pass

    with pytest.raises(CheckError, match="At least one of freshness_cron or maximum_lag_minutes"):
        result = build_freshness_checks(assets=[my_asset])

    result = build_freshness_checks(assets=[my_asset], maximum_lag_minutes=10)
    assert len(result) == 1
    assert result[0].asset_key == my_asset.key

    result = build_freshness_checks(assets=[my_asset.key], maximum_lag_minutes=10)
    assert len(result) == 1
    assert result[0].asset_key == my_asset.key

    src_asset = SourceAsset("source_asset")
    result = build_freshness_checks(assets=[src_asset], maximum_lag_minutes=10)
    assert len(result) == 1
    assert result[0].asset_key == src_asset.key

    result = build_freshness_checks(assets=[my_asset, src_asset], maximum_lag_minutes=10)
    assert len(result) == 2
    assert result[0].asset_key == my_asset.key

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_freshness_checks(assets=[my_asset, my_asset], maximum_lag_minutes=10)


@pytest.mark.parametrize(
    "use_materialization",
    [True, False],
    ids=["materialization", "observation"],
)
def test_check_different_event_types(
    pendulum_aware_report_dagster_event: None, use_materialization: bool, instance: DagsterInstance
) -> None:
    """Test that the freshness check works with different event types."""

    @asset
    def my_asset():
        pass

    start_time = pendulum.datetime(2021, 1, 1, 1, 0, 0, tz="UTC")
    maximum_lag_minutes = 10

    with pendulum.test(start_time.subtract(minutes=maximum_lag_minutes + 1)):
        add_new_event(instance, my_asset.key, is_materialization=use_materialization)
    with pendulum.test(start_time):
        freshness_checks = build_freshness_checks(
            assets=[my_asset],
            maximum_lag_minutes=maximum_lag_minutes,
        )
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, False)


@pytest.mark.parametrize(
    "maximum_lag_minutes",
    [None, 10],
    ids=["no_lag", "with_lag"],
)
def test_check_result_cron(
    pendulum_aware_report_dagster_event: None,
    instance: DagsterInstance,
    maximum_lag_minutes: Optional[int],
) -> None:
    """Move time forward and backward, with a freshness check parameterized with a cron, and ensure that the check passes and fails as expected."""

    @asset
    def my_asset():
        pass

    start_time = pendulum.datetime(2021, 1, 1, 1, 0, 0, tz="UTC")
    freshness_cron = "0 0 * * *"  # Every day at midnight.

    freshness_checks = build_freshness_checks(
        assets=[my_asset],
        freshness_cron=freshness_cron,
        maximum_lag_minutes=maximum_lag_minutes,
    )

    freeze_datetime = start_time
    with pendulum.test(freeze_datetime):
        # With no events, check fails.
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, False)

    # Add an event outside of the allowed time window. Check fails.
    lower_bound = pendulum.datetime(2021, 1, 1, 0, 0, 0, tz="UTC").subtract(
        minutes=maximum_lag_minutes if maximum_lag_minutes else 0
    )
    with pendulum.test(lower_bound.subtract(minutes=1)):
        add_new_event(instance, my_asset.key)
    with pendulum.test(freeze_datetime):
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, False)

    # Go back in time and add an event within cron-max_lag_minutes.
    with pendulum.test(lower_bound.add(minutes=1)):
        add_new_event(instance, my_asset.key)
    # Now we expect the check to pass.
    with pendulum.test(freeze_datetime):
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, True)

    # Advance a full day. By now, we would expect a new event to have been added.
    # Since that is not the case, we expect the check to fail.
    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, False)

    # Again, go back in time, and add an event within the time window we're checking.
    with pendulum.test(
        pendulum.datetime(2021, 1, 2, 0, 0, 0, tz="UTC")
        .subtract(minutes=maximum_lag_minutes if maximum_lag_minutes else 0)
        .add(minutes=1)
    ):
        add_new_event(instance, my_asset.key)
    # Now we expect the check to pass.
    with pendulum.test(freeze_datetime):
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, True)


def test_check_result_partitioned(
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

    start_time = pendulum.datetime(2021, 1, 1, 1, 0, 0, tz="UTC")
    freshness_cron = "0 0 * * *"  # Every day at midnight.

    freshness_checks = build_freshness_checks(
        assets=[my_asset],
        freshness_cron=freshness_cron,
    )

    freeze_datetime = start_time
    with pendulum.test(freeze_datetime):
        # With no events, check fails.
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, False)

        # Add an event for an old partition. Still fails
        add_new_event(instance, my_asset.key, "2020-12-30")
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, False)

        # Go back in time and add an event for the most recent completed partition.
        add_new_event(instance, my_asset.key, "2020-12-31")
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, True)

    # Advance a full day. By now, we would expect a new event to have been added.
    # Since that is not the case, we expect the check to fail.
    freeze_datetime = freeze_datetime.add(days=1)
    with pendulum.test(freeze_datetime):
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, False)

        # Again, go back in time, and add an event for the most recently completed time window.
        # Now we expect the check to pass.
        add_new_event(instance, my_asset.key, "2021-01-01")
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, True)


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

    freshness_checks = build_freshness_checks(
        assets=[my_asset],
        maximum_lag_minutes=maximum_lag_minutes,
    )

    freeze_datetime = start_time
    with pendulum.test(freeze_datetime):
        # With no events, check fails.
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, False)

    # Add an event outside of the allowed time window. Check fails.
    lower_bound = pendulum.datetime(2021, 1, 1, 0, 50, 0, tz="UTC")
    with pendulum.test(lower_bound.subtract(minutes=1)):
        add_new_event(instance, my_asset.key)
    with pendulum.test(freeze_datetime):
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, False)

    # Go back in time and add an event within the allowed time window.
    with pendulum.test(lower_bound.add(minutes=1)):
        add_new_event(instance, my_asset.key)
    # Now we expect the check to pass.
    with pendulum.test(freeze_datetime):
        _assert_check_result(my_asset, instance, freshness_checks, AssetCheckSeverity.WARN, True)
