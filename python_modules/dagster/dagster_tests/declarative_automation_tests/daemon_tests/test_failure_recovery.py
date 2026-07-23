import datetime
import multiprocessing

import dagster as dg
import pytest
from dagster._core.instance.ref import InstanceRef
from dagster._core.instance_for_test import cleanup_test_instance
from dagster._core.scheduler.instigation import TickStatus
from dagster._core.test_utils import freeze_time
from dagster._utils import get_terminate_signal

from dagster_tests.declarative_automation_tests.daemon_tests.test_e2e import (
    _execute_ticks,
    _get_all_sensors,
    get_grpc_workspace_request_context,
    get_threadpool_executor,
    wait_for_daemon_subprocess,
)


def _execute(
    instance_ref: InstanceRef,
    crash_location: str,
    terminate: bool,
    evaluation_time: datetime.datetime,
) -> None:
    with (
        get_grpc_workspace_request_context(
            "five_runs_required", instance_ref=instance_ref
        ) as context,
        get_threadpool_executor() as executor,
    ):
        try:
            with freeze_time(evaluation_time):
                _execute_ticks(
                    context,
                    executor,
                    {
                        crash_location: get_terminate_signal() if terminate else Exception("Oops!"),
                    },
                )
        finally:
            cleanup_test_instance(context.instance)


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
@pytest.mark.parametrize("terminate", [True, False])
def test_failure_recovery(crash_location: str, terminate: bool) -> None:
    spawn_ctx = multiprocessing.get_context("spawn")
    with get_grpc_workspace_request_context("five_runs_required") as workspace_context:
        sensors = _get_all_sensors(workspace_context.create_request_context())
        assert len(sensors) == 1
        selector_id, origin_id = (
            sensors[0].selector_id,
            sensors[0].get_remote_origin_id(),
        )

    with dg.instance_for_test() as instance:
        try:
            # run a tick that is destined to fail
            evaluation_time_1 = datetime.datetime(2024, 8, 16, 1, 35)
            evaluation_time_2 = evaluation_time_1 + datetime.timedelta(seconds=35)

            # execute a tick, crash at the specified location
            test_process = spawn_ctx.Process(
                target=_execute,
                args=[instance.get_ref(), crash_location, terminate, evaluation_time_1],
            )
            test_process.start()
            wait_for_daemon_subprocess(test_process)

            ticks = instance.get_ticks(selector_id=selector_id, origin_id=origin_id)
            assert len(ticks) == 1

            if terminate:
                # tick didn't get a chance to transition into the FAILURE state
                assert ticks[0].status == TickStatus.STARTED
                assert len(ticks[0].tick_data.run_ids) == 0

                tick_data_written = crash_location not in (
                    "EVALUATIONS_FINISHED",
                    "ASSET_EVALUATIONS_ADDED",
                )

                if not tick_data_written:
                    assert not len(ticks[0].tick_data.reserved_run_ids or [])
                else:
                    assert len(ticks[0].tick_data.reserved_run_ids or []) == 5

            else:
                # tick was able to gracefully exit
                assert ticks[0].status == TickStatus.FAILURE
                assert ticks[0].timestamp == evaluation_time_1.timestamp()

            assert ticks[0].automation_condition_evaluation_id == 1

            # execute another tick, don't crash
            test_process = spawn_ctx.Process(
                target=_execute,
                args=[instance.get_ref(), None, terminate, evaluation_time_2],
            )
            test_process.start()
            wait_for_daemon_subprocess(test_process)

            cursor_written = crash_location not in (
                "EVALUATIONS_FINISHED",
                "ASSET_EVALUATIONS_ADDED",
                "RUN_REQUESTS_CREATED",
            )

            ticks = instance.get_ticks(selector_id=selector_id, origin_id=origin_id)
            # Tick is resumed if the cursor was written before the crash, otherwise a new
            # tick is created
            assert len(ticks) == (1 if cursor_written and terminate else 2)

            assert ticks[0]
            assert ticks[0].status == TickStatus.SUCCESS
            assert len(ticks[0].tick_data.run_ids) == 5
            assert ticks[0].automation_condition_evaluation_id == 1

            if terminate and len(ticks) == 2:
                # first tick is intercepted and moved into skipped instead of being stuck in STARTED
                assert ticks[1].status == TickStatus.SKIPPED

            # all runs should have been kicked off
            runs = instance.get_runs()
            assert len(runs) == 5

            # the evaluations for each asset should have been updated
            assert instance.schedule_storage
            for i in range(5):
                key = dg.AssetKey(f"a{i}")
                evaluations = instance.schedule_storage.get_auto_materialize_asset_evaluations(
                    key=key, limit=100
                )
                assert len(evaluations) == 1
                assert evaluations[0].get_evaluation_with_run_ids().evaluation.key == key
                run_ids_for_asset = {
                    run.run_id for run in runs if key in (run.asset_selection or [])
                }
                assert len(run_ids_for_asset) == 1
                assert evaluations[0].get_evaluation_with_run_ids().run_ids == run_ids_for_asset
        finally:
            cleanup_test_instance(instance)


def _execute_job_scenario(
    instance_ref: InstanceRef,
    crash_location: str | None,
    evaluation_time: datetime.datetime,
) -> None:
    with (
        get_grpc_workspace_request_context(
            "job_fires_immediately", instance_ref=instance_ref
        ) as context,
        get_threadpool_executor() as executor,
    ):
        try:
            with freeze_time(evaluation_time):
                _execute_ticks(
                    context,
                    executor,
                    {crash_location: Exception("Oops!")} if crash_location else None,
                )
        finally:
            cleanup_test_instance(context.instance)


@pytest.mark.parametrize("crash_location", ["RUN_CREATED", "RUN_SUBMITTED"])
def test_job_entity_run_failure_recovery(crash_location: str) -> None:
    """A job-entity run interrupted mid-submission is resumed on the next tick and neither
    lost nor duplicated -- exercising submit_job_entity_run's interrupted-tick branch. The
    job fires on the first tick (all_job_root_assets_match(missing()) over a missing asset).
    """
    spawn_ctx = multiprocessing.get_context("spawn")
    with dg.instance_for_test() as instance:
        try:
            time_1 = datetime.datetime(2024, 8, 16, 1, 35)
            time_2 = time_1 + datetime.timedelta(seconds=35)

            # tick 1: crash partway through submitting the job run
            p = spawn_ctx.Process(
                target=_execute_job_scenario,
                args=[instance.get_ref(), crash_location, time_1],
            )
            p.start()
            wait_for_daemon_subprocess(p)

            # the failed tick reserved a run id (a run was created regardless of where we crashed)
            assert len([r for r in instance.get_runs() if r.job_name == "my_job"]) == 1

            # tick 2: resume, no crash
            p = spawn_ctx.Process(
                target=_execute_job_scenario, args=[instance.get_ref(), None, time_2]
            )
            p.start()
            wait_for_daemon_subprocess(p)

            # exactly one job run, and it was submitted (not stranded in NOT_STARTED)
            job_runs = [r for r in instance.get_runs() if r.job_name == "my_job"]
            assert len(job_runs) == 1
            assert job_runs[0].status != dg.DagsterRunStatus.NOT_STARTED
        finally:
            cleanup_test_instance(instance)
