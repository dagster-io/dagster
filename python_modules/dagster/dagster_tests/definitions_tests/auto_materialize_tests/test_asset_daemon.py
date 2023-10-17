import multiprocessing
from typing import TYPE_CHECKING

import pendulum
import pytest
from dagster import AssetKey
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._core.instance_for_test import instance_for_test
from dagster._core.scheduler.instigation import (
    InstigatorType,
    TickData,
    TickStatus,
)
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._core.test_utils import (
    cleanup_test_instance,
)
from dagster._daemon.asset_daemon import (
    FIXED_AUTO_MATERIALIZATION_INSTIGATOR_NAME,
    FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
    FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
    _get_raw_cursor,
    get_current_evaluation_id,
    set_auto_materialize_paused,
)
from dagster._utils import SingleInstigatorDebugCrashFlags, get_terminate_signal

from .scenarios.auto_materialize_policy_scenarios import (
    auto_materialize_policy_scenarios,
)
from .scenarios.auto_observe_scenarios import auto_observe_scenarios
from .scenarios.multi_code_location_scenarios import multi_code_location_scenarios
from .scenarios.scenarios import ASSET_RECONCILIATION_SCENARIOS

if TYPE_CHECKING:
    from pendulum.datetime import DateTime


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


@pytest.mark.parametrize(
    "scenario_item",
    list(ASSET_RECONCILIATION_SCENARIOS.items()),
    ids=list(ASSET_RECONCILIATION_SCENARIOS.keys()),
)
def test_reconcile_with_external_asset_graph(scenario_item, instance):
    scenario_name, scenario = scenario_item
    if not scenario.supports_with_external_asset_graph:
        pytest.skip("Scenario does not support with_external_asset_graph")
    run_requests, _, _ = scenario.do_sensor_scenario(
        instance, scenario_name=scenario_name, with_external_asset_graph=True
    )

    assert len(run_requests) == len(scenario.expected_run_requests), run_requests

    _assert_run_requests_match(scenario.expected_run_requests, run_requests)


daemon_scenarios = {
    **auto_materialize_policy_scenarios,
    **multi_code_location_scenarios,
    **auto_observe_scenarios,
}


@pytest.fixture
def daemon_paused_instance():
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            },
            "auto_materialize": {
                "max_tick_retries": 2,
            },
        }
    ) as the_instance:
        yield the_instance


@pytest.fixture
def daemon_not_paused_instance(daemon_paused_instance):
    set_auto_materialize_paused(daemon_paused_instance, False)
    return daemon_paused_instance


def test_daemon_ticks(daemon_paused_instance):
    instance = daemon_paused_instance
    ticks = instance.get_ticks(
        origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
        selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
    )
    assert len(ticks) == 0

    scenario = daemon_scenarios["auto_materialize_policy_lazy_freshness_missing"]
    scenario.do_daemon_scenario(
        instance, scenario_name="auto_materialize_policy_lazy_freshness_missing"
    )

    ticks = instance.get_ticks(
        origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
        selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
    )

    # Daemon paused, so no ticks
    assert len(ticks) == 0

    set_auto_materialize_paused(instance, False)

    freeze_datetime = pendulum.now("UTC")
    with pendulum.test(freeze_datetime):
        scenario.do_daemon_scenario(
            instance, scenario_name="auto_materialize_policy_lazy_freshness_missing"
        )
        ticks = instance.get_ticks(
            origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
            selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
        )

        assert len(ticks) == 1
        assert ticks[0]
        assert ticks[0].status == TickStatus.SUCCESS
        assert ticks[0].timestamp == freeze_datetime.timestamp()
        assert ticks[0].tick_data.end_timestamp == freeze_datetime.timestamp()
        assert len(ticks[0].tick_data.run_ids) == 1
        assert ticks[0].tick_data.auto_materialize_evaluation_id == 1
        assert ticks[0].tick_data.run_requests == scenario.expected_run_requests

    freeze_datetime = pendulum.now("UTC").add(seconds=40)
    with pendulum.test(freeze_datetime):
        scenario.do_daemon_scenario(
            instance, scenario_name="auto_materialize_policy_lazy_freshness_missing"
        )
        ticks = instance.get_ticks(
            origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
            selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
        )

        # No new runs, so tick is now skipped
        assert len(ticks) == 2
        assert ticks[0]
        assert ticks[0].status == TickStatus.SKIPPED
        assert ticks[0].timestamp == freeze_datetime.timestamp()
        assert ticks[0].tick_data.end_timestamp == freeze_datetime.timestamp()
        assert ticks[0].tick_data.auto_materialize_evaluation_id == 2
        assert ticks[0].tick_data.run_requests == []


def test_error_daemon_tick(daemon_not_paused_instance):
    instance = daemon_not_paused_instance
    error_asset_scenario = daemon_scenarios[
        "auto_materialize_policy_max_materializations_not_exceeded"
    ]
    execution_time = error_asset_scenario.current_time
    error_asset_scenario = error_asset_scenario._replace(current_time=None)

    for trial_num in range(3):
        test_time = execution_time.add(seconds=15 * trial_num)
        with pendulum.test(test_time):
            debug_crash_flags = {"EXECUTION_PLAN_CREATED": Exception(f"Oops {trial_num}")}

            with pytest.raises(Exception, match=f"Oops {trial_num}"):
                error_asset_scenario.do_daemon_scenario(
                    instance,
                    scenario_name="auto_materialize_policy_max_materializations_not_exceeded",
                    debug_crash_flags=debug_crash_flags,
                )

            ticks = instance.get_ticks(
                origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
                selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
            )

            assert len(ticks) == trial_num + 1
            assert ticks[0].status == TickStatus.FAILURE
            assert ticks[0].timestamp == test_time.timestamp()
            assert ticks[0].tick_data.end_timestamp == test_time.timestamp()
            assert ticks[0].tick_data.auto_materialize_evaluation_id == 1
            assert ticks[0].tick_data.failure_count == trial_num + 1

            assert f"Oops {trial_num}" in str(ticks[0].tick_data.error)

            # Run requests are still on the tick since they were stored there before the
            # failure happened during run submission
            _assert_run_requests_match(
                error_asset_scenario.expected_run_requests, ticks[0].tick_data.run_requests
            )

            # Cursor doesn't update until the last trial, since we know we will no longer retry the
            # tick anymore
            cursor = _get_raw_cursor(instance)

            if trial_num == 2:
                assert cursor
            else:
                assert not cursor

    # TODO include a test case that verifies that if the failure happens during run launching,
    # subsequent ticks that retry don't cause runs to loop

    # Next tick moves on to use the new cursor / evaluation ID since we have passed the maximum
    # number of retries
    test_time = execution_time.add(seconds=45)
    with pendulum.test(test_time):
        debug_crash_flags = {"EVALUATIONS_FINISHED": Exception("Oops new tick")}
        with pytest.raises(Exception, match="Oops new tick"):
            error_asset_scenario.do_daemon_scenario(
                instance,
                scenario_name="auto_materialize_policy_max_materializations_not_exceeded",
                debug_crash_flags=debug_crash_flags,
            )

        ticks = instance.get_ticks(
            origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
            selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
        )

        assert len(ticks) == 4
        assert ticks[0].status == TickStatus.FAILURE
        assert ticks[0].timestamp == test_time.timestamp()
        assert ticks[0].tick_data.end_timestamp == test_time.timestamp()
        assert ticks[0].tick_data.auto_materialize_evaluation_id == 2  # advances

        assert "Oops new tick" in str(ticks[0].tick_data.error)

        assert ticks[0].tick_data.failure_count == 1  # starts over


spawn_ctx = multiprocessing.get_context("spawn")


def _test_asset_daemon_in_subprocess(
    scenario_name,
    instance_ref: InstanceRef,
    execution_datetime: "DateTime",
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
        "RUN_IDS_ADDED_TO_EVALUATIONS",
        "RUN_CREATED",
        "RUN_SUBMITTED",
        "CURSOR_UPDATED",
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
        origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
        selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
    )

    assert len(ticks) == 1
    assert ticks[0]
    assert ticks[0].status == TickStatus.STARTED
    assert ticks[0].timestamp == scenario.current_time.timestamp()
    assert not ticks[0].tick_data.end_timestamp == scenario.current_time.timestamp()
    assert not len(ticks[0].tick_data.run_ids)
    assert ticks[0].tick_data.auto_materialize_evaluation_id == 1

    freeze_datetime = scenario.current_time.add(seconds=1)

    cursor = _get_raw_cursor(instance)

    if crash_location == "CURSOR_UPDATED":
        assert cursor
        assert cursor == ticks[0].tick_data.cursor
    else:
        assert not cursor

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
        origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
        selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
    )

    assert len(ticks) == 1

    assert ticks[0]
    assert ticks[0].status == TickStatus.SUCCESS
    assert ticks[0].timestamp == scenario.current_time.timestamp()
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
        asset_key=AssetKey("hourly"), limit=100
    )
    assert len(evaluations) == 1
    assert evaluations[0].evaluation.asset_key == AssetKey("hourly")
    assert evaluations[0].evaluation.run_ids == {run.run_id for run in sorted_runs}

    cursor = _get_raw_cursor(instance)
    assert cursor == ticks[0].tick_data.cursor


@pytest.fixture
def custom_purge_instance():
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            },
            "retention": {"auto_materialize": {"purge_after_days": {"skipped": 2}}},
        }
    ) as the_instance:
        set_auto_materialize_paused(the_instance, False)
        yield the_instance


def _create_tick(instance, status, timestamp):
    return instance.create_tick(
        TickData(
            instigator_origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
            instigator_name=FIXED_AUTO_MATERIALIZATION_INSTIGATOR_NAME,
            instigator_type=InstigatorType.AUTO_MATERIALIZE,
            status=status,
            timestamp=timestamp,
            selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
            run_ids=[],
        )
    )


def test_auto_materialize_purge(daemon_not_paused_instance):
    freeze_datetime = pendulum.now("UTC")

    tick_1 = _create_tick(
        daemon_not_paused_instance, TickStatus.SKIPPED, freeze_datetime.subtract(days=1).timestamp()
    )
    tick_2 = _create_tick(
        daemon_not_paused_instance, TickStatus.SKIPPED, freeze_datetime.subtract(days=6).timestamp()
    )
    _create_tick(
        daemon_not_paused_instance, TickStatus.SKIPPED, freeze_datetime.subtract(days=8).timestamp()
    )

    ticks = daemon_not_paused_instance.get_ticks(
        origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
        selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
    )
    assert len(ticks) == 3

    with pendulum.test(freeze_datetime):
        scenario = daemon_scenarios["auto_materialize_policy_lazy_freshness_missing"]
        scenario.do_daemon_scenario(
            daemon_not_paused_instance,
            scenario_name="auto_materialize_policy_lazy_freshness_missing",
        )

        # creates one SUCCESS tick and purges the old SKIPPED ticks
        ticks = daemon_not_paused_instance.get_ticks(
            origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
            selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
        )

        assert len(ticks) == 3

        assert ticks[0]
        assert ticks[0].status == TickStatus.SUCCESS
        assert ticks[0].timestamp == freeze_datetime.timestamp()

        assert ticks[1] == tick_1
        assert ticks[2] == tick_2


def test_custom_purge(custom_purge_instance):
    freeze_datetime = pendulum.now("UTC")

    tick_1 = _create_tick(
        custom_purge_instance, TickStatus.SKIPPED, freeze_datetime.subtract(days=1).timestamp()
    )
    _create_tick(
        custom_purge_instance, TickStatus.SKIPPED, freeze_datetime.subtract(days=6).timestamp()
    )
    _create_tick(
        custom_purge_instance, TickStatus.SKIPPED, freeze_datetime.subtract(days=8).timestamp()
    )

    ticks = custom_purge_instance.get_ticks(
        origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
        selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
    )
    assert len(ticks) == 3

    with pendulum.test(freeze_datetime):
        scenario = daemon_scenarios["auto_materialize_policy_lazy_freshness_missing"]
        scenario.do_daemon_scenario(
            custom_purge_instance,
            scenario_name="auto_materialize_policy_lazy_freshness_missing",
        )

        # creates one SUCCESS tick and purges the old SKIPPED ticks
        ticks = custom_purge_instance.get_ticks(
            origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
            selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
        )

        assert len(ticks) == 2

        assert ticks[0]
        assert ticks[0].status == TickStatus.SUCCESS
        assert ticks[0].timestamp == freeze_datetime.timestamp()

        assert ticks[1] == tick_1


@pytest.mark.parametrize(
    "scenario_item",
    list(daemon_scenarios.items()),
    ids=list(daemon_scenarios.keys()),
)
def test_daemon(scenario_item, daemon_not_paused_instance):
    scenario_name, scenario = scenario_item
    scenario.do_daemon_scenario(daemon_not_paused_instance, scenario_name=scenario_name)

    runs = daemon_not_paused_instance.get_runs()

    expected_runs = 0
    inner_scenario = scenario
    while inner_scenario is not None:
        expected_runs += len(inner_scenario.unevaluated_runs or []) + len(
            inner_scenario.expected_run_requests
            if inner_scenario.expected_run_requests and not inner_scenario.expected_error_message
            else []
        )
        inner_scenario = inner_scenario.cursor_from

    assert len(runs) == expected_runs

    for run in runs:
        if any(
            op_config["config"].get("fail") for op_config in run.run_config.get("ops", {}).values()
        ):
            assert run.status == DagsterRunStatus.FAILURE
        else:
            assert run.status == DagsterRunStatus.SUCCESS

    def sort_run_request_key_fn(run_request):
        return (min(run_request.asset_selection), run_request.partition_key)

    def sort_run_key_fn(run):
        return (min(run.asset_selection), run.tags.get(PARTITION_NAME_TAG))

    # Get all of the runs that were submitted in the most recent asset evaluation
    asset_evaluation_id = get_current_evaluation_id(daemon_not_paused_instance)
    submitted_runs_in_scenario = (
        [
            run
            for run in runs
            if run.tags.get("dagster/asset_evaluation_id") == str(asset_evaluation_id)
        ]
        if asset_evaluation_id
        else []
    )

    if scenario.expected_error_message:
        assert (
            len(submitted_runs_in_scenario) == 0
        ), "scenario should have raised an error, but instead it submitted runs"
    else:
        assert len(submitted_runs_in_scenario) == len(scenario.expected_run_requests), (
            "Expected the following run requests to be submitted:"
            f" {scenario.expected_run_requests} \n"
            " but instead submitted runs with asset and partition selection:"
            f" {[(list(run.asset_selection), run.tags.get(PARTITION_NAME_TAG)) for run in submitted_runs_in_scenario]}"
        )

    sorted_runs = sorted(runs[: len(scenario.expected_run_requests)], key=sort_run_key_fn)
    sorted_expected_run_requests = sorted(
        scenario.expected_run_requests, key=sort_run_request_key_fn
    )
    for run, expected_run_request in zip(sorted_runs, sorted_expected_run_requests):
        assert run.asset_selection is not None
        assert set(run.asset_selection) == set(expected_run_request.asset_selection)
        assert run.tags.get(PARTITION_NAME_TAG) == expected_run_request.partition_key

    ticks = daemon_not_paused_instance.get_ticks(
        origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
        selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
    )
    tick = ticks[0]
    if tick.status == TickStatus.SUCCESS and scenario.expected_evaluations:
        assert tick.requested_asset_materialization_count == sum(
            [spec.num_requested for spec in scenario.expected_evaluations]
        )
        assert tick.requested_asset_keys == {
            AssetKey.from_coercible(spec.asset_key)
            for spec in scenario.expected_evaluations
            if spec.num_requested > 0
        }


def test_daemon_run_tags():
    scenario_name = "auto_materialize_policy_eager_with_freshness_policies"
    scenario = auto_materialize_policy_scenarios[scenario_name]

    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            },
            "auto_materialize": {"run_tags": {"foo": "bar"}},
        }
    ) as instance:
        set_auto_materialize_paused(instance, False)

        scenario.do_daemon_scenario(instance, scenario_name=scenario_name)

        runs = instance.get_runs()

        assert len(runs) == len(
            scenario.expected_run_requests
            + scenario.unevaluated_runs
            + (scenario.cursor_from.unevaluated_runs if scenario.cursor_from else [])
        )

        for run in runs:
            assert run.status == DagsterRunStatus.SUCCESS

        def sort_run_request_key_fn(run_request):
            return (min(run_request.asset_selection), run_request.partition_key)

        def sort_run_key_fn(run):
            return (min(run.asset_selection), run.tags.get(PARTITION_NAME_TAG))

        sorted_runs = sorted(runs[: len(scenario.expected_run_requests)], key=sort_run_key_fn)
        sorted_expected_run_requests = sorted(
            scenario.expected_run_requests, key=sort_run_request_key_fn
        )
        for run, expected_run_request in zip(sorted_runs, sorted_expected_run_requests):
            assert run.asset_selection is not None
            assert set(run.asset_selection) == set(expected_run_request.asset_selection)
            assert run.tags.get(PARTITION_NAME_TAG) == expected_run_request.partition_key
            assert run.tags["foo"] == "bar"


def test_daemon_paused():
    scenario_name = "auto_materialize_policy_eager_with_freshness_policies"
    scenario = auto_materialize_policy_scenarios[scenario_name]

    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            },
        }
    ) as instance:
        scenario.do_daemon_scenario(instance, scenario_name=scenario_name)

        runs = instance.get_runs()

        # daemon is paused by default , so no new runs should have been created
        assert len(runs) == len(
            scenario.unevaluated_runs
            + (scenario.cursor_from.unevaluated_runs if scenario.cursor_from else [])
        )

        instance.wipe()
        set_auto_materialize_paused(instance, False)
        scenario.do_daemon_scenario(instance, scenario_name=scenario_name)
        runs = instance.get_runs()

        assert len(runs) == len(
            scenario.expected_run_requests
            + scenario.unevaluated_runs
            + (scenario.cursor_from.unevaluated_runs if scenario.cursor_from else [])
        )


def test_run_ids():
    scenario_name = "auto_materialize_policy_eager_with_freshness_policies"
    scenario = auto_materialize_policy_scenarios[scenario_name]

    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            },
        }
    ) as instance:
        set_auto_materialize_paused(instance, False)

        scenario.do_daemon_scenario(instance, scenario_name=scenario_name)

        runs = instance.get_runs()

        assert len(runs) == len(
            scenario.expected_run_requests
            + scenario.unevaluated_runs
            + (scenario.cursor_from.unevaluated_runs if scenario.cursor_from else [])
        )

        for run in runs:
            assert run.status == DagsterRunStatus.SUCCESS

        def sort_run_request_key_fn(run_request):
            return (min(run_request.asset_selection), run_request.partition_key)

        def sort_run_key_fn(run):
            return (min(run.asset_selection), run.tags.get(PARTITION_NAME_TAG))

        sorted_runs = sorted(runs[: len(scenario.expected_run_requests)], key=sort_run_key_fn)
        sorted_expected_run_requests = sorted(
            scenario.expected_run_requests, key=sort_run_request_key_fn
        )
        for run, expected_run_request in zip(sorted_runs, sorted_expected_run_requests):
            assert run.asset_selection is not None
            assert set(run.asset_selection) == set(expected_run_request.asset_selection)
            assert run.tags.get(PARTITION_NAME_TAG) == expected_run_request.partition_key

        evaluations = instance.schedule_storage.get_auto_materialize_asset_evaluations(
            asset_key=AssetKey("asset4"), limit=100
        )
        assert len(evaluations) == 1
        assert evaluations[0].evaluation.asset_key == AssetKey("asset4")
        assert evaluations[0].evaluation.run_ids == {run.run_id for run in sorted_runs}
