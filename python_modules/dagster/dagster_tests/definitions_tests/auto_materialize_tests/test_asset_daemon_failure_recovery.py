import datetime
import multiprocessing
from typing import Sequence

import dagster._check as check
import pytest
from dagster import AssetKey, DagsterInstance, RunRequest
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.instance.ref import InstanceRef
from dagster._core.scheduler.instigation import TickStatus
from dagster._core.test_utils import cleanup_test_instance
from dagster._daemon.asset_daemon import (
    MAX_TIME_TO_RESUME_TICK_SECONDS,
    _get_raw_cursor,
)
from dagster._utils import SingleInstigatorDebugCrashFlags, get_terminate_signal

from .asset_daemon_scenario import AssetDaemonScenario
from .test_asset_daemon import (
    _get_asset_daemon_ticks,
    get_daemon_instance,
    simple_daemon_scenario,
    simple_daemon_scenario_expected_run_requests,
)
from .updated_scenarios.asset_daemon_scenario_states import (
    hourly_to_daily,
    time_partitions_start_datetime,
)

spawn_ctx = multiprocessing.get_context("spawn")


def _test_asset_daemon_in_subprocess(
    instance_ref: InstanceRef,
    current_time: datetime.datetime,
    debug_crash_flags: SingleInstigatorDebugCrashFlags,
) -> None:
    with DagsterInstance.from_ref(instance_ref) as instance:
        try:
            simple_daemon_scenario._replace(
                initial_state=simple_daemon_scenario.initial_state.with_current_time(current_time)
            ).evaluate_daemon(instance, debug_crash_flags=debug_crash_flags)
        finally:
            cleanup_test_instance(instance)


def _assert_run_requests_match(
    expected_run_requests: Sequence[RunRequest], run_requests: Sequence[RunRequest]
) -> None:
    def sort_run_request_key_fn(run_request) -> tuple:
        return (min(run_request.asset_selection), run_request.partition_key)

    sorted_run_requests = sorted(run_requests, key=sort_run_request_key_fn)
    sorted_expected_run_requests = sorted(expected_run_requests, key=sort_run_request_key_fn)

    for run_request, expected_run_request in zip(sorted_run_requests, sorted_expected_run_requests):
        assert set(run_request.asset_selection or []) == set(
            expected_run_request.asset_selection or []
        )
        assert run_request.partition_key == expected_run_request.partition_key


def test_old_tick_not_resumed() -> None:
    # we need a scenario here which will fire off runs each time the time is advanced (in this case
    # because the hourly partitions definition will always have new partitions after advancing time)
    scenario = AssetDaemonScenario(
        id="old_tick_not_resumed",
        initial_state=hourly_to_daily.with_current_time(time_partitions_start_datetime)
        .with_current_time_advanced(hours=5)
        .with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick(),
    )
    with get_daemon_instance() as instance:
        debug_crash_flags = {"RUN_CREATED": Exception("OOPS")}
        with pytest.raises(Exception, match="OOPS"):
            scenario.evaluate_daemon(instance=instance, debug_crash_flags=debug_crash_flags)

        ticks = _get_asset_daemon_ticks(instance)

        assert len(ticks) == 1
        assert ticks[-1].tick_data.auto_materialize_evaluation_id == 1
        assert ticks[-1].timestamp == scenario.initial_state.current_time.timestamp()

        # advancing past MAX_TIME_TO_RESUME_TICK_SECONDS gives up and advances to a new evaluation
        scenario = scenario.with_initial_time_advanced(seconds=MAX_TIME_TO_RESUME_TICK_SECONDS + 1)
        with pytest.raises(Exception, match="OOPS"):
            scenario.evaluate_daemon(instance=instance, debug_crash_flags=debug_crash_flags)

        ticks = _get_asset_daemon_ticks(instance)
        assert len(ticks) == 2
        assert ticks[-1].tick_data.auto_materialize_evaluation_id == 2

        # advancing less than that retries the same tick
        scenario = scenario.with_initial_time_advanced(seconds=MAX_TIME_TO_RESUME_TICK_SECONDS - 1)
        with pytest.raises(Exception, match="OOPS"):
            scenario.evaluate_daemon(instance=instance, debug_crash_flags=debug_crash_flags)
            ticks = _get_asset_daemon_ticks(instance)

            assert len(ticks) == 3
            assert ticks[-1].tick_data.auto_materialize_evaluation_id == 2


@pytest.mark.parametrize(
    "crash_location",
    [
        "EVALUATIONS_FINISHED",
        "RUN_REQUESTS_CREATED",
    ],
)
def test_error_loop_before_cursor_written(crash_location: str) -> None:
    scenario = simple_daemon_scenario
    with get_daemon_instance() as instance:
        for trial_num in range(3):
            scenario = scenario.with_initial_time_advanced(seconds=15)
            debug_crash_flags = {crash_location: Exception(f"Oops {trial_num}")}

            with pytest.raises(Exception, match=f"Oops {trial_num}"):
                state = scenario.evaluate_daemon(instance, debug_crash_flags)

                ticks = _get_asset_daemon_ticks(instance)
                assert len(ticks) == trial_num + 1
                assert ticks[-1].status == TickStatus.FAILURE
                assert ticks[-1].timestamp == state.current_time.timestamp()
                assert ticks[-1].tick_data.end_timestamp == state.current_time.timestamp()
                assert ticks[-1].tick_data.auto_materialize_evaluation_id == 1

                # each tick is considered a brand new retry since it happened before the cursor
                # was written
                assert ticks[-1].tick_data.failure_count == 1

                assert f"Oops {trial_num}" in str(ticks[0].tick_data.error)

                # Run requests are still on the tick since they were stored there before the
                # failure happened during run submission
                _assert_run_requests_match(
                    simple_daemon_scenario_expected_run_requests,
                    ticks[-1].tick_data.run_requests or [],
                )

                # Cursor never writes since failure happens before cursor write
                cursor = _get_raw_cursor(instance)
                assert not cursor

        # Next successful tick recovers
        scenario = scenario.with_initial_time_advanced(seconds=45)
        state = scenario.evaluate_daemon(instance, debug_crash_flags=None)
        ticks = _get_asset_daemon_ticks(instance)

        assert len(ticks) == 4
        assert ticks[-1].status == TickStatus.SUCCESS
        assert ticks[-1].timestamp == state.current_time.timestamp()
        assert ticks[-1].tick_data.end_timestamp == state.current_time.timestamp()
        assert ticks[-1].tick_data.auto_materialize_evaluation_id == 1  # finally finishes

        runs = instance.get_runs()
        assert len(runs) == 3


@pytest.mark.parametrize(
    "crash_location",
    [
        "RUN_CREATED",  # exception after creating any run
        "RUN_SUBMITTED",  # exception after submitting any run
        "EXECUTION_PLAN_CREATED_1",  # exception after running code for 2nd run
        "RUN_CREATED_1",  # exception after creating 2nd run
        "RUN_SUBMITTED_1",  # exception after submitting 2nd run
        "RUN_IDS_ADDED_TO_EVALUATIONS",  # exception after updating asset evaluations
    ],
)
def test_error_loop_after_cursor_written(crash_location: str) -> None:
    scenario = simple_daemon_scenario
    current_time = scenario.initial_state.current_time
    with get_daemon_instance() as instance:
        last_cursor = None

        # User code error retries but does not increment the retry count
        debug_crash_flags = {crash_location: DagsterUserCodeUnreachableError("WHERE IS THE CODE")}

        with pytest.raises(Exception, match="WHERE IS THE CODE"):
            scenario.evaluate_daemon(instance, debug_crash_flags=debug_crash_flags)

        ticks = _get_asset_daemon_ticks(instance)

        assert len(ticks) == 1
        assert ticks[-1].status == TickStatus.FAILURE
        assert ticks[-1].timestamp == current_time.timestamp()
        assert ticks[-1].tick_data.end_timestamp == current_time.timestamp()
        assert ticks[-1].tick_data.auto_materialize_evaluation_id == 1

        # failure count does not increase since it was a user code error
        assert ticks[-1].tick_data.failure_count == 0

        assert "WHERE IS THE CODE" in str(ticks[-1].tick_data.error)
        assert "Auto-materialization will resume once the code server is available" in str(
            ticks[-1].tick_data.error
        )

        # Run requests are still on the tick since they were stored there before the
        # failure happened during run submission
        _assert_run_requests_match(
            simple_daemon_scenario_expected_run_requests, ticks[-1].tick_data.run_requests or []
        )

        cursor = _get_raw_cursor(instance)
        # Same cursor due to the retry
        assert cursor is not None
        last_cursor = cursor

        for trial_num in range(3):
            scenario = scenario.with_initial_time_advanced(seconds=15)
            current_time = scenario.initial_state.current_time
            debug_crash_flags = {crash_location: Exception(f"Oops {trial_num}")}

            with pytest.raises(Exception, match=f"Oops {trial_num}"):
                scenario.evaluate_daemon(instance, debug_crash_flags=debug_crash_flags)

            ticks = _get_asset_daemon_ticks(instance)

            assert len(ticks) == trial_num + 2
            assert ticks[-1].status == TickStatus.FAILURE
            assert ticks[-1].timestamp == current_time.timestamp()
            assert ticks[-1].tick_data.end_timestamp == current_time.timestamp()
            assert ticks[-1].tick_data.auto_materialize_evaluation_id == 1

            # failure count only increases if the cursor was written - otherwise
            # each tick is considered a brand new retry
            assert ticks[-1].tick_data.failure_count == trial_num + 1

            assert f"Oops {trial_num}" in str(ticks[-1].tick_data.error)

            # Run requests are still on the tick since they were stored there before the
            # failure happened during run submission
            _assert_run_requests_match(
                simple_daemon_scenario_expected_run_requests, ticks[-1].tick_data.run_requests or []
            )

            # Same cursor due to the retry
            retry_cursor = _get_raw_cursor(instance)
            assert retry_cursor == last_cursor

        # Next tick moves on to use the new cursor / evaluation ID since we have passed the maximum
        # number of retries
        scenario = scenario.with_initial_time_advanced(seconds=45)
        current_time = scenario.initial_state.current_time
        debug_crash_flags = {"RUN_IDS_ADDED_TO_EVALUATIONS": Exception("Oops new tick")}
        with pytest.raises(Exception, match="Oops new tick"):
            scenario.evaluate_daemon(instance, debug_crash_flags=debug_crash_flags)

        ticks = _get_asset_daemon_ticks(instance)
        print(ticks)
        assert len(ticks) == 5
        assert ticks[-1].status == TickStatus.FAILURE
        assert ticks[-1].timestamp == current_time.timestamp()
        assert ticks[-1].tick_data.end_timestamp == current_time.timestamp()
        assert ticks[-1].tick_data.auto_materialize_evaluation_id == 2  # advances

        assert "Oops new tick" in str(ticks[-1].tick_data.error)

        assert ticks[-1].tick_data.failure_count == 1  # starts over

        # Cursor has moved on
        moved_on_cursor = _get_raw_cursor(instance)
        assert moved_on_cursor != last_cursor

        scenario = scenario.with_initial_time_advanced(seconds=45)
        current_time = scenario.initial_state.current_time
        # Next successful tick recovers
        scenario.evaluate_daemon(instance, debug_crash_flags=debug_crash_flags)

        ticks = _get_asset_daemon_ticks(instance)
        assert len(ticks) == 6
        assert ticks[-1].status != TickStatus.FAILURE
        assert ticks[-1].timestamp == current_time.timestamp()
        assert ticks[-1].tick_data.end_timestamp == current_time.timestamp()
        assert ticks[-1].tick_data.auto_materialize_evaluation_id == 2  # finishes


@pytest.mark.parametrize(
    "crash_location",
    [
        "EVALUATIONS_FINISHED",
        "ASSET_EVALUATIONS_ADDED",
        "RUN_REQUESTS_CREATED",
        "CURSOR_UPDATED",
        "RUN_IDS_ADDED_TO_EVALUATIONS",
        "EXECUTION_PLAN_CREATED_1",  # exception after running code for 2nd run
        "RUN_CREATED",
        "RUN_SUBMITTED",
        "RUN_CREATED_1",  # exception after creating 2nd run
        "RUN_SUBMITTED_1",  # exception after submitting 2nd run
    ],
)
def test_asset_daemon_crash_recovery(crash_location: str) -> None:
    """Verifies that if we crash at various points during the tick, the next tick recovers and
    produces the correct number of runs.
    """
    with get_daemon_instance() as instance:
        current_time = simple_daemon_scenario.initial_state.current_time
        # Run a tick where the daemon crashes after run requests are created
        asset_daemon_process = spawn_ctx.Process(
            target=_test_asset_daemon_in_subprocess,
            args=[instance.get_ref(), current_time, {crash_location: get_terminate_signal()}],
        )
        asset_daemon_process.start()
        asset_daemon_process.join(timeout=60)

        ticks = _get_asset_daemon_ticks(instance)

        assert len(ticks) == 1
        assert ticks[-1]
        assert ticks[-1].status == TickStatus.STARTED
        assert ticks[-1].timestamp == current_time.timestamp()
        # some time must have elapsed
        assert (
            not ticks[-1].tick_data.end_timestamp
            == simple_daemon_scenario.initial_state.current_time.timestamp()
        )

        assert not len(ticks[-1].tick_data.run_ids)
        assert ticks[-1].tick_data.auto_materialize_evaluation_id == 1

        current_time = current_time + datetime.timedelta(seconds=1)

        # Run another tick with no crash, daemon continues on and succeeds
        asset_daemon_process = spawn_ctx.Process(
            target=_test_asset_daemon_in_subprocess,
            # No crash this time
            args=[instance.get_ref(), current_time, None],
        )
        asset_daemon_process.start()
        asset_daemon_process.join(timeout=60)

        ticks = _get_asset_daemon_ticks(instance)
        cursor_written = crash_location not in (
            "EVALUATIONS_FINISHED",
            "ASSET_EVALUATIONS_ADDED",
            "RUN_REQUESTS_CREATED",
        )

        # Tick is resumed if the cursor was written before the crash, otherwise a new tick is created
        assert len(ticks) == 1 if cursor_written else 2

        assert ticks[-1]
        assert ticks[-1].status == TickStatus.SUCCESS
        assert (
            ticks[-1].timestamp == simple_daemon_scenario.initial_state.current_time.timestamp()
            if cursor_written
            else current_time.timestamp()
        )
        assert ticks[-1].tick_data.end_timestamp == current_time.timestamp()
        assert len(ticks[-1].tick_data.run_ids) == 3
        assert ticks[-1].tick_data.auto_materialize_evaluation_id == 1

        if len(ticks) == 2:
            # first tick is intercepted and moved into skipped instead of being stuck in STARTED
            assert ticks[0].status == TickStatus.SKIPPED

        _assert_run_requests_match(
            simple_daemon_scenario_expected_run_requests, ticks[0].tick_data.run_requests or []
        )

        runs = instance.get_runs()
        assert len(runs) == 3

        evaluations = check.not_none(
            instance.schedule_storage
        ).get_auto_materialize_asset_evaluations(asset_key=AssetKey("A"), limit=100)
        assert len(evaluations) == 1
        assert evaluations[-1].evaluation.asset_key == AssetKey("A")
        assert evaluations[-1].evaluation.run_ids == {run.run_id for run in runs}


@pytest.mark.parametrize(
    "crash_location",
    [
        "EVALUATIONS_FINISHED",
        "ASSET_EVALUATIONS_ADDED",
        "RUN_REQUESTS_CREATED",
        "RUN_IDS_ADDED_TO_EVALUATIONS",
        "RUN_CREATED",
        "RUN_SUBMITTED",
        "RUN_CREATED_2",
        "RUN_SUBMITTED_2",
    ],
)
def test_asset_daemon_exception_recovery(crash_location: str) -> None:
    """Verifies that if we raise an exception at various points during the tick, the next tick
    recovers and produces the correct number of runs.
    """
    with get_daemon_instance() as instance:
        current_time = simple_daemon_scenario.initial_state.current_time
        asset_daemon_process = spawn_ctx.Process(
            target=_test_asset_daemon_in_subprocess,
            args=[instance.get_ref(), current_time, {crash_location: Exception("OOPS")}],
        )
        asset_daemon_process.start()
        asset_daemon_process.join(timeout=60)

        ticks = _get_asset_daemon_ticks(instance)

        assert len(ticks) == 1
        assert ticks[-1]
        assert ticks[-1].status == TickStatus.FAILURE
        assert ticks[-1].timestamp == current_time.timestamp()
        assert ticks[-1].tick_data.end_timestamp == current_time.timestamp()

        assert ticks[-1].tick_data.auto_materialize_evaluation_id == 1

        tick_data_written = crash_location not in (
            "EVALUATIONS_FINISHED",
            "ASSET_EVALUATIONS_ADDED",
        )

        cursor_written = crash_location not in (
            "EVALUATIONS_FINISHED",
            "ASSET_EVALUATIONS_ADDED",
            "RUN_REQUESTS_CREATED",
        )

        if not tick_data_written:
            assert not len(ticks[0].tick_data.reserved_run_ids or [])
        else:
            assert len(ticks[0].tick_data.reserved_run_ids or []) == 3

        cursor = _get_raw_cursor(instance)
        assert bool(cursor) == cursor_written

        current_time = current_time + datetime.timedelta(seconds=1)

        # Run another tick with no failure, daemon continues on and succeeds
        asset_daemon_process = spawn_ctx.Process(
            target=_test_asset_daemon_in_subprocess,
            # No crash this time
            args=[instance.get_ref(), current_time, None],
        )
        asset_daemon_process.start()
        asset_daemon_process.join(timeout=60)

        ticks = _get_asset_daemon_ticks(instance)

        assert len(ticks) == 2

        assert ticks[-1]
        assert ticks[-1].status == TickStatus.SUCCESS
        assert ticks[-1].timestamp == current_time.timestamp()
        assert ticks[-1].tick_data.end_timestamp == current_time.timestamp()
        assert len(ticks[-1].tick_data.run_ids) == 3
        assert ticks[-1].tick_data.auto_materialize_evaluation_id == 1

        _assert_run_requests_match(
            simple_daemon_scenario_expected_run_requests, ticks[0].tick_data.run_requests or []
        )

        runs = instance.get_runs()
        assert len(runs) == 3

        evaluations = check.not_none(
            instance.schedule_storage
        ).get_auto_materialize_asset_evaluations(asset_key=AssetKey("A"), limit=100)
        assert len(evaluations) == 1
        assert evaluations[0].evaluation.asset_key == AssetKey("A")
        assert evaluations[0].evaluation.run_ids == {run.run_id for run in runs}

        cursor = _get_raw_cursor(instance)
        assert cursor
