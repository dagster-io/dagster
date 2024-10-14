import datetime
import multiprocessing

import pytest
from dagster import AssetKey
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._core.instance_for_test import instance_for_test
from dagster._core.scheduler.instigation import TickStatus
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._core.test_utils import cleanup_test_instance, freeze_time
from dagster._daemon.asset_daemon import (
    _PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
    _PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    MAX_TIME_TO_RESUME_TICK_SECONDS,
    _get_pre_sensor_auto_materialize_cursor,
    set_auto_materialize_paused,
)
from dagster._utils import SingleInstigatorDebugCrashFlags, get_terminate_signal

from dagster_tests.definitions_tests.declarative_automation_tests.legacy_tests.scenarios.auto_materialize_policy_scenarios import (
    auto_materialize_policy_scenarios,
)
from dagster_tests.definitions_tests.declarative_automation_tests.legacy_tests.scenarios.auto_observe_scenarios import (
    auto_observe_scenarios,
)
from dagster_tests.definitions_tests.declarative_automation_tests.legacy_tests.scenarios.multi_code_location_scenarios import (
    multi_code_location_scenarios,
)

daemon_scenarios = {
    **auto_materialize_policy_scenarios,
    **multi_code_location_scenarios,
    **auto_observe_scenarios,
}


def _assert_run_requests_match(
    expected_run_requests,
    run_requests,
):
    def sort_run_request_key_fn(run_request):
        return (min(run_request.asset_selection), run_request.partition_key)

    sorted_run_requests = sorted(run_requests, key=sort_run_request_key_fn)
    sorted_expected_run_requests = sorted(expected_run_requests, key=sort_run_request_key_fn)

    for run_request, expected_run_request in zip(sorted_run_requests, sorted_expected_run_requests):
        assert set(run_request.asset_selection) == set(expected_run_request.asset_selection)
        assert run_request.partition_key == expected_run_request.partition_key


@pytest.fixture
def instance():
    with instance_for_test() as the_instance:
        yield the_instance


@pytest.fixture
def daemon_paused_instance():
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            },
            "auto_materialize": {"max_tick_retries": 2, "use_sensors": False},
        }
    ) as the_instance:
        yield the_instance


@pytest.fixture
def daemon_not_paused_instance(daemon_paused_instance):
    set_auto_materialize_paused(daemon_paused_instance, False)
    return daemon_paused_instance


def test_old_tick_not_resumed(daemon_not_paused_instance):
    instance = daemon_not_paused_instance
    error_asset_scenario = daemon_scenarios[
        "auto_materialize_policy_max_materializations_not_exceeded"
    ]
    execution_time = error_asset_scenario.current_time
    error_asset_scenario = error_asset_scenario._replace(current_time=None)

    debug_crash_flags = {"RUN_CREATED": Exception("OOPS")}

    with freeze_time(execution_time):
        error_asset_scenario.do_daemon_scenario(
            instance,
            scenario_name="auto_materialize_policy_max_materializations_not_exceeded",
            debug_crash_flags=debug_crash_flags,
        )

        ticks = instance.get_ticks(
            origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
            selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
        )

        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.FAILURE
        assert ticks[0].tick_data.auto_materialize_evaluation_id == 1
        assert ticks[0].timestamp == execution_time.timestamp()

    # advancing past MAX_TIME_TO_RESUME_TICK_SECONDS gives up and advances to a new evaluation
    execution_time = execution_time + datetime.timedelta(
        seconds=MAX_TIME_TO_RESUME_TICK_SECONDS + 1
    )

    with freeze_time(execution_time):
        error_asset_scenario.do_daemon_scenario(
            instance,
            scenario_name="auto_materialize_policy_max_materializations_not_exceeded",
            debug_crash_flags=debug_crash_flags,
        )

        ticks = instance.get_ticks(
            origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
            selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
        )

        assert len(ticks) == 2
        assert ticks[0].status == TickStatus.FAILURE
        assert ticks[0].tick_data.auto_materialize_evaluation_id == 2

    # advancing less than that retries the same tick
    execution_time = execution_time + datetime.timedelta(
        seconds=MAX_TIME_TO_RESUME_TICK_SECONDS - 1
    )

    with freeze_time(execution_time):
        error_asset_scenario.do_daemon_scenario(
            instance,
            scenario_name="auto_materialize_policy_max_materializations_not_exceeded",
            debug_crash_flags=debug_crash_flags,
        )

        ticks = instance.get_ticks(
            origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
            selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
        )

        assert len(ticks) == 3
        assert ticks[0].status == TickStatus.FAILURE
        assert ticks[0].tick_data.auto_materialize_evaluation_id == 2


@pytest.mark.parametrize(
    "crash_location",
    [
        "EVALUATIONS_FINISHED",
        "RUN_REQUESTS_CREATED",
    ],
)
def test_error_loop_before_cursor_written(daemon_not_paused_instance, crash_location):
    instance = daemon_not_paused_instance
    error_asset_scenario = daemon_scenarios[
        "auto_materialize_policy_max_materializations_not_exceeded"
    ]
    execution_time = error_asset_scenario.current_time
    error_asset_scenario = error_asset_scenario._replace(current_time=None)

    for trial_num in range(3):
        test_time = execution_time + datetime.timedelta(seconds=15 * trial_num)
        with freeze_time(test_time):
            debug_crash_flags = {crash_location: Exception(f"Oops {trial_num}")}

            error_asset_scenario.do_daemon_scenario(
                instance,
                scenario_name="auto_materialize_policy_max_materializations_not_exceeded",
                debug_crash_flags=debug_crash_flags,
            )

            ticks = instance.get_ticks(
                origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
                selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
            )

            assert len(ticks) == trial_num + 1
            assert ticks[0].status == TickStatus.FAILURE
            assert ticks[0].timestamp == test_time.timestamp()
            assert ticks[0].tick_data.end_timestamp == test_time.timestamp()
            assert ticks[0].tick_data.auto_materialize_evaluation_id == 1

            # each tick is considered a brand new retry since it happened before the cursor
            # was written
            assert ticks[0].tick_data.failure_count == 1

            assert f"Oops {trial_num}" in str(ticks[0].tick_data.error)

            # Run requests are still on the tick since they were stored there before the
            # failure happened during run submission
            _assert_run_requests_match(
                error_asset_scenario.expected_run_requests, ticks[0].tick_data.run_requests
            )

            # Cursor never writes since failure happens before cursor write
            cursor = _get_pre_sensor_auto_materialize_cursor(instance, None)
            assert not cursor.evaluation_id

    test_time = test_time + datetime.timedelta(seconds=45)
    with freeze_time(test_time):
        # Next successful tick recovers
        error_asset_scenario.do_daemon_scenario(
            instance,
            scenario_name="auto_materialize_policy_max_materializations_not_exceeded",
            debug_crash_flags={},
        )
    ticks = instance.get_ticks(
        origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
        selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    )

    assert len(ticks) == 4
    assert ticks[0].status == TickStatus.SUCCESS
    assert ticks[0].timestamp == test_time.timestamp()
    assert ticks[0].tick_data.end_timestamp == test_time.timestamp()
    assert ticks[0].tick_data.auto_materialize_evaluation_id == 1  # finally finishes

    runs = instance.get_runs()
    assert len(runs) == 5


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
def test_error_loop_after_cursor_written(daemon_not_paused_instance, crash_location):
    instance = daemon_not_paused_instance
    error_asset_scenario = daemon_scenarios[
        "auto_materialize_policy_max_materializations_not_exceeded"
    ]
    execution_time = error_asset_scenario.current_time
    error_asset_scenario = error_asset_scenario._replace(current_time=None)

    last_cursor = None

    # User code error retries but does not increment the retry count
    test_time = execution_time + datetime.timedelta(seconds=15)
    with freeze_time(test_time):
        debug_crash_flags = {crash_location: DagsterUserCodeUnreachableError("WHERE IS THE CODE")}

        error_asset_scenario.do_daemon_scenario(
            instance,
            scenario_name="auto_materialize_policy_max_materializations_not_exceeded",
            debug_crash_flags=debug_crash_flags,
        )
        ticks = instance.get_ticks(
            origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
            selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
        )

        assert len(ticks) == 1
        assert ticks[0].status == TickStatus.FAILURE
        assert ticks[0].timestamp == test_time.timestamp()
        assert ticks[0].tick_data.end_timestamp == test_time.timestamp()
        assert ticks[0].tick_data.auto_materialize_evaluation_id == 1

        # failure count does not increase since it was a user code error
        assert ticks[0].tick_data.failure_count == 0

        assert "WHERE IS THE CODE" in str(ticks[0].tick_data.error)
        assert "Auto-materialization will resume once the code server is available" in str(
            ticks[0].tick_data.error
        )

        # Run requests are still on the tick since they were stored there before the
        # failure happened during run submission
        _assert_run_requests_match(
            error_asset_scenario.expected_run_requests, ticks[0].tick_data.run_requests
        )

        cursor = _get_pre_sensor_auto_materialize_cursor(instance, None)
        # Same cursor due to the retry
        assert cursor.evaluation_id == 1
        last_cursor = cursor

    for trial_num in range(3):
        test_time = test_time + datetime.timedelta(seconds=15)
        with freeze_time(test_time):
            debug_crash_flags = {crash_location: Exception(f"Oops {trial_num}")}

            error_asset_scenario.do_daemon_scenario(
                instance,
                scenario_name="auto_materialize_policy_max_materializations_not_exceeded",
                debug_crash_flags=debug_crash_flags,
            )

            ticks = instance.get_ticks(
                origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
                selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
            )

            assert len(ticks) == trial_num + 2
            assert ticks[0].status == TickStatus.FAILURE
            assert ticks[0].timestamp == test_time.timestamp()
            assert ticks[0].tick_data.end_timestamp == test_time.timestamp()
            assert ticks[0].tick_data.auto_materialize_evaluation_id == 1

            # failure count only increases if the cursor was written - otherwise
            # each tick is considered a brand new retry
            assert ticks[0].tick_data.failure_count == trial_num + 1

            assert f"Oops {trial_num}" in str(ticks[0].tick_data.error)

            # Run requests are still on the tick since they were stored there before the
            # failure happened during run submission
            _assert_run_requests_match(
                error_asset_scenario.expected_run_requests, ticks[0].tick_data.run_requests
            )

            # Same cursor due to the retry
            retry_cursor = _get_pre_sensor_auto_materialize_cursor(instance, None)
            assert retry_cursor == last_cursor

    # Next tick moves on to use the new cursor / evaluation ID since we have passed the maximum
    # number of retries
    test_time = test_time + datetime.timedelta(seconds=45)
    with freeze_time(test_time):
        debug_crash_flags = {"RUN_IDS_ADDED_TO_EVALUATIONS": Exception("Oops new tick")}
        error_asset_scenario.do_daemon_scenario(
            instance,
            scenario_name="auto_materialize_policy_max_materializations_not_exceeded",
            debug_crash_flags=debug_crash_flags,
        )

        ticks = instance.get_ticks(
            origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
            selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
        )

        assert len(ticks) == 5
        assert ticks[0].status == TickStatus.FAILURE
        assert ticks[0].timestamp == test_time.timestamp()
        assert ticks[0].tick_data.end_timestamp == test_time.timestamp()
        assert (
            ticks[0].tick_data.auto_materialize_evaluation_id == 5
        )  # advances, skipping a few numbers

        assert "Oops new tick" in str(ticks[0].tick_data.error)

        assert ticks[0].tick_data.failure_count == 1  # starts over

        # Cursor has moved on
        moved_on_cursor = _get_pre_sensor_auto_materialize_cursor(instance, None)
        assert moved_on_cursor != last_cursor

    test_time = test_time + datetime.timedelta(seconds=45)
    with freeze_time(test_time):
        # Next successful tick recovers
        error_asset_scenario.do_daemon_scenario(
            instance,
            scenario_name="auto_materialize_policy_max_materializations_not_exceeded",
            debug_crash_flags={},
        )

    ticks = instance.get_ticks(
        origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
        selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    )

    assert len(ticks) == 6
    assert ticks[0].status != TickStatus.FAILURE
    assert ticks[0].timestamp == test_time.timestamp()
    assert ticks[0].tick_data.end_timestamp == test_time.timestamp()
    assert ticks[0].tick_data.auto_materialize_evaluation_id == 5  # finishes


spawn_ctx = multiprocessing.get_context("spawn")


def _test_asset_daemon_in_subprocess(
    scenario_name,
    instance_ref: InstanceRef,
    execution_datetime: datetime.datetime,
    debug_crash_flags: SingleInstigatorDebugCrashFlags,
) -> None:
    scenario = daemon_scenarios[scenario_name]
    with DagsterInstance.from_ref(instance_ref) as instance:
        try:
            scenario._replace(current_time=execution_datetime).do_daemon_scenario(
                instance, scenario_name=scenario_name, debug_crash_flags=debug_crash_flags
            )
        finally:
            cleanup_test_instance(instance)


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
def test_asset_daemon_crash_recovery(daemon_not_paused_instance, crash_location):
    # Verifies that if we crash at various points during the tick, the next tick recovers and
    # produces the correct number of runs
    instance = daemon_not_paused_instance
    scenario = daemon_scenarios["auto_materialize_policy_max_materializations_not_exceeded"]

    # Run a tick where the daemon crashes after run requests are created
    asset_daemon_process = spawn_ctx.Process(
        target=_test_asset_daemon_in_subprocess,
        args=[
            "auto_materialize_policy_max_materializations_not_exceeded",
            instance.get_ref(),
            scenario.current_time,
            {crash_location: get_terminate_signal()},
        ],
    )
    asset_daemon_process.start()
    asset_daemon_process.join(timeout=60)

    ticks = instance.get_ticks(
        origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
        selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    )

    assert len(ticks) == 1
    assert ticks[0]
    assert ticks[0].status == TickStatus.STARTED
    assert ticks[0].timestamp == scenario.current_time.timestamp()
    assert not ticks[0].tick_data.end_timestamp == scenario.current_time.timestamp()

    assert not len(ticks[0].tick_data.run_ids)
    assert ticks[0].tick_data.auto_materialize_evaluation_id == 1

    freeze_datetime = scenario.current_time + datetime.timedelta(seconds=1)

    # Run another tick with no crash, daemon continues on and succeeds
    asset_daemon_process = spawn_ctx.Process(
        target=_test_asset_daemon_in_subprocess,
        args=[
            "auto_materialize_policy_max_materializations_not_exceeded",
            instance.get_ref(),
            freeze_datetime,
            None,  # No crash this time
        ],
    )
    asset_daemon_process.start()
    asset_daemon_process.join(timeout=60)

    ticks = instance.get_ticks(
        origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
        selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    )

    cursor_written = crash_location not in (
        "EVALUATIONS_FINISHED",
        "ASSET_EVALUATIONS_ADDED",
        "RUN_REQUESTS_CREATED",
    )

    # Tick is resumed if the cursor was written before the crash, otherwise a new
    # tick is created
    assert len(ticks) == 1 if cursor_written else 2

    assert ticks[0]
    assert ticks[0].status == TickStatus.SUCCESS
    assert (
        ticks[0].timestamp == scenario.current_time.timestamp()
        if cursor_written
        else freeze_datetime.timestamp()
    )
    assert ticks[0].tick_data.end_timestamp == freeze_datetime.timestamp()
    assert len(ticks[0].tick_data.run_ids) == 5
    assert ticks[0].tick_data.auto_materialize_evaluation_id == 1

    if len(ticks) == 2:
        # first tick is intercepted and moved into skipped instead of being stuck in STARTED
        assert ticks[1].status == TickStatus.SKIPPED

    _assert_run_requests_match(scenario.expected_run_requests, ticks[0].tick_data.run_requests)

    runs = instance.get_runs()
    assert len(runs) == 5

    def sort_run_key_fn(run):
        return (min(run.asset_selection), run.tags.get(PARTITION_NAME_TAG))

    sorted_runs = sorted(runs[: len(scenario.expected_run_requests)], key=sort_run_key_fn)

    evaluations = instance.schedule_storage.get_auto_materialize_asset_evaluations(
        key=AssetKey("hourly"), limit=100
    )
    assert len(evaluations) == 1
    assert evaluations[0].get_evaluation_with_run_ids().evaluation.key == AssetKey("hourly")
    assert evaluations[0].get_evaluation_with_run_ids().run_ids == {
        run.run_id for run in sorted_runs
    }


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
def test_asset_daemon_exception_recovery(daemon_not_paused_instance, crash_location):
    # Verifies that if we raise an exception at various points during the tick, the next tick
    # recovers and produces the correct number of runs
    instance = daemon_not_paused_instance
    scenario = daemon_scenarios["auto_materialize_policy_max_materializations_not_exceeded"]

    asset_daemon_process = spawn_ctx.Process(
        target=_test_asset_daemon_in_subprocess,
        args=[
            "auto_materialize_policy_max_materializations_not_exceeded",
            instance.get_ref(),
            scenario.current_time,
            {crash_location: Exception("OOPS")},
        ],
    )
    asset_daemon_process.start()
    asset_daemon_process.join(timeout=60)

    ticks = instance.get_ticks(
        origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
        selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    )

    assert len(ticks) == 1
    assert ticks[0]
    assert ticks[0].status == TickStatus.FAILURE
    assert ticks[0].timestamp == scenario.current_time.timestamp()
    assert ticks[0].tick_data.end_timestamp == scenario.current_time.timestamp()

    assert ticks[0].tick_data.auto_materialize_evaluation_id == 1

    tick_data_written = crash_location not in ("EVALUATIONS_FINISHED", "ASSET_EVALUATIONS_ADDED")

    cursor_written = crash_location not in (
        "EVALUATIONS_FINISHED",
        "ASSET_EVALUATIONS_ADDED",
        "RUN_REQUESTS_CREATED",
    )

    if not tick_data_written:
        assert not len(ticks[0].tick_data.reserved_run_ids)
    else:
        assert len(ticks[0].tick_data.reserved_run_ids) == 5

    cursor = _get_pre_sensor_auto_materialize_cursor(instance, None)
    assert (cursor.evaluation_id > 0) == cursor_written

    freeze_datetime = scenario.current_time + datetime.timedelta(seconds=1)

    # Run another tick with no failure, daemon continues on and succeeds
    asset_daemon_process = spawn_ctx.Process(
        target=_test_asset_daemon_in_subprocess,
        args=[
            "auto_materialize_policy_max_materializations_not_exceeded",
            instance.get_ref(),
            freeze_datetime,
            None,  # No crash this time
        ],
    )
    asset_daemon_process.start()
    asset_daemon_process.join(timeout=60)

    ticks = instance.get_ticks(
        origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
        selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    )

    assert len(ticks) == 2

    assert ticks[0]
    assert ticks[0].status == TickStatus.SUCCESS
    assert ticks[0].timestamp == freeze_datetime.timestamp()
    assert ticks[0].tick_data.end_timestamp == freeze_datetime.timestamp()
    assert len(ticks[0].tick_data.run_ids) == 5
    assert ticks[0].tick_data.auto_materialize_evaluation_id == 1

    _assert_run_requests_match(scenario.expected_run_requests, ticks[0].tick_data.run_requests)

    runs = instance.get_runs()
    assert len(runs) == 5

    def sort_run_key_fn(run):
        return (min(run.asset_selection), run.tags.get(PARTITION_NAME_TAG))

    sorted_runs = sorted(runs[: len(scenario.expected_run_requests)], key=sort_run_key_fn)

    evaluations = instance.schedule_storage.get_auto_materialize_asset_evaluations(
        key=AssetKey("hourly"), limit=100
    )
    assert len(evaluations) == 1
    assert evaluations[0].get_evaluation_with_run_ids().evaluation.key == AssetKey("hourly")
    assert evaluations[0].get_evaluation_with_run_ids().run_ids == {
        run.run_id for run in sorted_runs
    }

    cursor = _get_pre_sensor_auto_materialize_cursor(instance, None)
    assert cursor.evaluation_id > 0
