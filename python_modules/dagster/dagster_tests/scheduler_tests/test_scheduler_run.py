import datetime
import os
import sys
import time
from contextlib import contextmanager

import pendulum
import pytest

from dagster import DagsterEventType, daily_schedule, hourly_schedule, pipeline, repository, solid
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation import (
    PythonEnvRepositoryLocation,
    RepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.scheduler import ScheduleState, ScheduleStatus, ScheduleTickStatus
from dagster.core.storage.pipeline_run import PipelineRunStatus, PipelineRunsFilter
from dagster.core.storage.tags import PARTITION_NAME_TAG, SCHEDULED_EXECUTION_TIME_TAG
from dagster.core.test_utils import instance_for_test
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.server import GrpcServerProcess
from dagster.scheduler.scheduler import get_default_scheduler_logger, launch_scheduled_runs
from dagster.utils import merge_dicts

_COUPLE_DAYS_AGO = datetime.datetime(year=2019, month=2, day=25)


def _throw(_context):
    raise Exception("bananas")


def _throw_on_odd_day(context):
    launch_time = context.scheduled_execution_time

    if launch_time.day % 2 == 1:
        raise Exception("Not a good day sorry")
    return True


def _never(_context):
    return False


@solid(config_schema={"work_amt": str})
def the_solid(context):
    return "0.8.0 was {} of work".format(context.solid_config["work_amt"])


@pipeline
def the_pipeline():
    the_solid()


@daily_schedule(pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO)
def simple_schedule(_context):
    return {
        "solids": {"the_solid": {"config": {"work_amt": "a lot"}}},
    }


# Schedule that runs on a different day in Central Time vs UTC
@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_time=datetime.time(hour=23, minute=0),
)
def daily_late_schedule(_context):
    return {
        "solids": {"the_solid": {"config": {"work_amt": "a lot"}}},
    }


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_time=datetime.time(hour=2, minute=30),
)
def daily_dst_transition_schedule(_context):
    return {
        "solids": {"the_solid": {"config": {"work_amt": "a lot"}}},
    }


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    end_date=datetime.datetime(year=2019, month=3, day=1),
)
def simple_temporary_schedule(_context):
    return {}


@daily_schedule(pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO)
def bad_env_fn_schedule():  # forgot context arg
    return {}


@hourly_schedule(pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO)
def simple_hourly_schedule(_context):
    return {"solids": {"the_solid": {"config": {"work_amt": "even more"}}}}


@daily_schedule(
    pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO, should_execute=_throw,
)
def bad_should_execute_schedule(_context):
    return {"solids": {"the_solid": {"config": {"work_amt": "a lot"}}}}


@daily_schedule(
    pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO, should_execute=_throw_on_odd_day,
)
def bad_should_execute_schedule_on_odd_days(_context):
    return {"solids": {"the_solid": {"config": {"work_amt": "a lot"}}}}


@daily_schedule(
    pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO, should_execute=_never,
)
def skip_schedule(_context):
    return {"solids": {"the_solid": {"config": {"work_amt": "a lot"}}}}


@daily_schedule(
    pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO,
)
def wrong_config_schedule(_context):
    return {}


@repository
def the_repo():
    return [
        the_pipeline,
        simple_schedule,
        simple_temporary_schedule,
        simple_hourly_schedule,
        daily_late_schedule,
        daily_dst_transition_schedule,
        bad_env_fn_schedule,
        bad_should_execute_schedule,
        bad_should_execute_schedule_on_odd_days,
        skip_schedule,
        wrong_config_schedule,
    ]


def schedule_instance(timezone=None, overrides=None):
    return instance_for_test(
        overrides=merge_dicts(
            {
                "scheduler": merge_dicts(
                    {"module": "dagster.core.scheduler", "class": "DagsterCommandLineScheduler",},
                    ({"config": {"default_timezone": timezone}} if timezone else {}),
                ),
            },
            (overrides if overrides else {}),
        )
    )


@contextmanager
def instance_with_schedules(external_repo_context, timezone=None, overrides=None):
    with schedule_instance(timezone, overrides) as instance:
        with external_repo_context() as external_repo:
            instance.reconcile_scheduler_state(external_repo)
            yield (instance, external_repo)


@contextmanager
def grpc_repo_location():
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable, python_file=__file__, attribute="the_repo"
    )
    server_process = GrpcServerProcess(loadable_target_origin=loadable_target_origin)
    try:
        with server_process.create_ephemeral_client() as api_client:
            yield RepositoryLocation.from_handle(
                RepositoryLocationHandle.create_grpc_server_location(
                    port=api_client.port, socket=api_client.socket, host=api_client.host,
                )
            )
    finally:
        server_process.wait()


@contextmanager
def grpc_repo():
    with grpc_repo_location() as repo_location:
        yield repo_location.get_repository("the_repo")


@contextmanager
def default_repo():
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable, python_file=__file__, attribute="the_repo",
    )

    with RepositoryLocationHandle.create_python_env_location(
        loadable_target_origin=loadable_target_origin, location_name="test_location",
    ) as handle:
        yield PythonEnvRepositoryLocation(handle).get_repository("the_repo")


def validate_tick(
    tick,
    external_schedule,
    expected_datetime,
    expected_status,
    expected_run_id,
    expected_error=None,
):
    tick_data = tick.schedule_tick_data
    assert tick_data.schedule_origin_id == external_schedule.get_origin_id()
    assert tick_data.schedule_name == external_schedule.name
    assert tick_data.cron_schedule == external_schedule.cron_schedule
    assert tick_data.timestamp == expected_datetime.timestamp()
    assert tick_data.status == expected_status
    assert tick_data.run_id == expected_run_id
    if expected_error:
        assert expected_error in tick_data.error.message


def validate_run_started(run, expected_datetime, expected_partition, expected_success=True):
    assert run.tags[SCHEDULED_EXECUTION_TIME_TAG] == expected_datetime.in_tz("UTC").isoformat()
    assert run.tags[PARTITION_NAME_TAG] == expected_partition

    if expected_success:
        assert run.status == PipelineRunStatus.STARTED or run.status == PipelineRunStatus.SUCCESS
    else:
        assert run.status == PipelineRunStatus.FAILURE


def wait_for_all_runs_to_start(instance, timeout=10):
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise Exception("Timed out waiting for runs to start")
        time.sleep(0.5)

        not_started_runs = [
            run for run in instance.get_runs() if run.status == PipelineRunStatus.NOT_STARTED
        ]

        if len(not_started_runs) == 0:
            break


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_simple_schedule(external_repo_context, capfd):
    freeze_datetime = pendulum.datetime(
        year=2019, month=2, day=27, hour=23, minute=59, second=59,
    ).in_tz("US/Central")
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        with pendulum.test(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("simple_schedule")

            schedule_origin = external_schedule.get_origin()

            instance.start_schedule_and_update_storage_state(external_schedule)

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

            # launch_scheduled_runs does nothing before the first tick
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

            captured = capfd.readouterr()

            assert (
                captured.out
                == """2019-02-27 17:59:59 - dagster-scheduler - INFO - Checking for new runs for the following schedules: simple_schedule
2019-02-27 17:59:59 - dagster-scheduler - INFO - No new runs for simple_schedule
"""
            )

        freeze_datetime = freeze_datetime.add(seconds=2)
        with pendulum.test(freeze_datetime):
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )

            assert instance.get_runs_count() == 1
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1

            expected_datetime = pendulum.datetime(year=2019, month=2, day=28)

            validate_tick(
                ticks[0],
                external_schedule,
                expected_datetime,
                ScheduleTickStatus.SUCCESS,
                instance.get_runs()[0].run_id,
            )

            wait_for_all_runs_to_start(instance)
            validate_run_started(instance.get_runs()[0], expected_datetime, "2019-02-27")

            captured = capfd.readouterr()

            assert (
                captured.out
                == """2019-02-27 18:00:01 - dagster-scheduler - INFO - Checking for new runs for the following schedules: simple_schedule
2019-02-27 18:00:01 - dagster-scheduler - INFO - Launching run for simple_schedule at 2019-02-28 00:00:00+0000
2019-02-27 18:00:01 - dagster-scheduler - INFO - Completed scheduled launch of run {run_id} for simple_schedule
""".format(
                    run_id=instance.get_runs()[0].run_id
                )
            )

            # Verify idempotence
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 1
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            assert ticks[0].status == ScheduleTickStatus.SUCCESS

        # Verify advancing in time but not going past a tick doesn't add any new runs
        freeze_datetime = freeze_datetime.add(seconds=2)
        with pendulum.test(freeze_datetime):
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 1
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            assert ticks[0].status == ScheduleTickStatus.SUCCESS

        freeze_datetime = freeze_datetime.add(days=2)
        with pendulum.test(freeze_datetime):
            capfd.readouterr()

            # Traveling two more days in the future before running results in two new ticks
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )
            assert instance.get_runs_count() == 3
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 3
            assert len([tick for tick in ticks if tick.status == ScheduleTickStatus.SUCCESS]) == 3

            runs_by_partition = {run.tags[PARTITION_NAME_TAG]: run for run in instance.get_runs()}

            assert "2019-02-28" in runs_by_partition
            assert "2019-03-01" in runs_by_partition

            captured = capfd.readouterr()

            assert (
                captured.out
                == """2019-03-01 18:00:03 - dagster-scheduler - INFO - Checking for new runs for the following schedules: simple_schedule
2019-03-01 18:00:03 - dagster-scheduler - INFO - Launching 2 runs for simple_schedule at the following times: 2019-03-01 00:00:00+0000, 2019-03-02 00:00:00+0000
2019-03-01 18:00:03 - dagster-scheduler - INFO - Completed scheduled launch of run {first_run_id} for simple_schedule
2019-03-01 18:00:03 - dagster-scheduler - INFO - Completed scheduled launch of run {second_run_id} for simple_schedule
""".format(
                    first_run_id=instance.get_runs()[1].run_id,
                    second_run_id=instance.get_runs()[0].run_id,
                )
            )

            # Check idempotence again
            launch_scheduled_runs(instance, get_default_scheduler_logger(), pendulum.now("UTC"))
            assert instance.get_runs_count() == 3
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 3


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_bad_env_fn(external_repo_context, capfd):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("bad_env_fn_schedule")
        schedule_origin = external_schedule.get_origin()
        initial_datetime = pendulum.datetime(year=2019, month=2, day=27, hour=0, minute=0, second=0)
        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            launch_scheduled_runs(instance, get_default_scheduler_logger(), pendulum.now("UTC"))

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                ScheduleTickStatus.FAILURE,
                None,
                "Error occurred during the execution of run_config_fn for "
                "schedule bad_env_fn_schedule",
            )

            captured = capfd.readouterr()

            assert "Failed to fetch schedule data for bad_env_fn_schedule: " in captured.out

            assert (
                "Error occurred during the execution of run_config_fn for "
                "schedule bad_env_fn_schedule" in captured.out
            )


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_bad_should_execute(external_repo_context, capfd):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("bad_should_execute_schedule")
        schedule_origin = external_schedule.get_origin()
        initial_datetime = pendulum.datetime(
            year=2019, month=2, day=27, hour=0, minute=0, second=0,
        )
        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            launch_scheduled_runs(instance, get_default_scheduler_logger(), pendulum.now("UTC"))

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                ScheduleTickStatus.FAILURE,
                None,
                "Error occurred during the execution of should_execute for "
                "schedule bad_should_execute_schedule",
            )

            captured = capfd.readouterr()
            assert (
                "Failed to fetch schedule data for bad_should_execute_schedule: "
            ) in captured.out

            assert (
                "Error occurred during the execution of should_execute "
                "for schedule bad_should_execute_schedule" in captured.out
            )

            assert "Exception: bananas" in captured.out


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_skip(external_repo_context, capfd):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("skip_schedule")
        schedule_origin = external_schedule.get_origin()
        initial_datetime = pendulum.datetime(
            year=2019, month=2, day=27, hour=0, minute=0, second=0,
        ).in_tz("US/Central")
        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            launch_scheduled_runs(instance, get_default_scheduler_logger(), pendulum.now("UTC"))

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0], external_schedule, initial_datetime, ScheduleTickStatus.SKIPPED, None,
            )

            captured = capfd.readouterr()
            assert (
                captured.out
                == """2019-02-26 18:00:00 - dagster-scheduler - INFO - Checking for new runs for the following schedules: skip_schedule
2019-02-26 18:00:00 - dagster-scheduler - INFO - Launching run for skip_schedule at 2019-02-27 00:00:00+0000
2019-02-26 18:00:00 - dagster-scheduler - INFO - should_execute returned False for skip_schedule, skipping
"""
            )


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_wrong_config(external_repo_context, capfd):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("wrong_config_schedule")
        schedule_origin = external_schedule.get_origin()
        initial_datetime = pendulum.datetime(year=2019, month=2, day=27, hour=0, minute=0, second=0)
        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            launch_scheduled_runs(instance, get_default_scheduler_logger(), pendulum.now("UTC"))

            assert instance.get_runs_count() == 1

            wait_for_all_runs_to_start(instance)

            run = instance.get_runs()[0]

            validate_run_started(run, initial_datetime, "2019-02-26", expected_success=False)

            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                ScheduleTickStatus.SUCCESS,
                run.run_id,
            )

            run_logs = instance.all_logs(run.run_id)

            assert (
                len(
                    [
                        event
                        for event in run_logs
                        if (
                            "DagsterInvalidConfigError" in event.dagster_event.message
                            and event.dagster_event_type == DagsterEventType.ENGINE_EVENT
                        )
                    ]
                )
                > 0
            )

            captured = capfd.readouterr()

            assert "Failed to fetch execution plan for wrong_config_schedule" in captured.out
            assert "Error in config for pipeline the_pipeline" in captured.out
            assert 'Missing required field "solids" at the root.' in captured.out


def _get_unloadable_schedule_origin():
    working_directory = os.path.dirname(__file__)
    recon_repo = ReconstructableRepository.for_file(__file__, "doesnt_exist", working_directory)
    schedule = recon_repo.get_reconstructable_schedule("also_doesnt_exist")
    return schedule.get_origin()


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_bad_schedules_mixed_with_good_schedule(external_repo_context, capfd):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        good_schedule = external_repo.get_external_schedule("simple_schedule")
        bad_schedule = external_repo.get_external_schedule(
            "bad_should_execute_schedule_on_odd_days"
        )

        good_origin = good_schedule.get_origin()
        bad_origin = bad_schedule.get_origin()
        unloadable_origin = _get_unloadable_schedule_origin()
        initial_datetime = pendulum.datetime(
            year=2019, month=2, day=27, hour=0, minute=0, second=0,
        )
        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(good_schedule)
            instance.start_schedule_and_update_storage_state(bad_schedule)

            unloadable_schedule_state = ScheduleState(
                unloadable_origin,
                ScheduleStatus.RUNNING,
                "0 0 * * *",
                pendulum.now("UTC").timestamp(),
            )
            instance.add_schedule_state(unloadable_schedule_state)

            launch_scheduled_runs(instance, get_default_scheduler_logger(), pendulum.now("UTC"))

            assert instance.get_runs_count() == 1
            wait_for_all_runs_to_start(instance)
            validate_run_started(instance.get_runs()[0], initial_datetime, "2019-02-26")

            good_ticks = instance.get_schedule_ticks(good_origin.get_id())
            assert len(good_ticks) == 1
            validate_tick(
                good_ticks[0],
                good_schedule,
                initial_datetime,
                ScheduleTickStatus.SUCCESS,
                instance.get_runs()[0].run_id,
            )

            bad_ticks = instance.get_schedule_ticks(bad_origin.get_id())
            assert len(bad_ticks) == 1

            assert bad_ticks[0].status == ScheduleTickStatus.FAILURE

            assert (
                "Error occurred during the execution of should_execute "
                "for schedule bad_should_execute_schedule" in bad_ticks[0].error.message
            )

            unloadable_ticks = instance.get_schedule_ticks(unloadable_origin.get_id())
            assert len(unloadable_ticks) == 0

            captured = capfd.readouterr()
            assert "Scheduler failed for also_doesnt_exist" in captured.out
            assert "doesnt_exist not found at module scope" in captured.out

        initial_datetime = initial_datetime.add(days=1)
        with pendulum.test(initial_datetime):
            new_now = pendulum.now("UTC")
            launch_scheduled_runs(instance, get_default_scheduler_logger(), new_now)

            assert instance.get_runs_count() == 3
            wait_for_all_runs_to_start(instance)

            good_schedule_runs = instance.get_runs(
                filters=PipelineRunsFilter.for_schedule(good_schedule)
            )
            assert len(good_schedule_runs) == 2
            validate_run_started(good_schedule_runs[0], new_now, "2019-02-27")

            good_ticks = instance.get_schedule_ticks(good_origin.get_id())
            assert len(good_ticks) == 2
            validate_tick(
                good_ticks[0],
                good_schedule,
                new_now,
                ScheduleTickStatus.SUCCESS,
                good_schedule_runs[0].run_id,
            )

            bad_schedule_runs = instance.get_runs(
                filters=PipelineRunsFilter.for_schedule(bad_schedule)
            )
            assert len(bad_schedule_runs) == 1
            validate_run_started(bad_schedule_runs[0], new_now, "2019-02-27")

            bad_ticks = instance.get_schedule_ticks(bad_origin.get_id())
            assert len(bad_ticks) == 2
            validate_tick(
                bad_ticks[0],
                bad_schedule,
                new_now,
                ScheduleTickStatus.SUCCESS,
                bad_schedule_runs[0].run_id,
            )

            unloadable_ticks = instance.get_schedule_ticks(unloadable_origin.get_id())
            assert len(unloadable_ticks) == 0

            captured = capfd.readouterr()
            assert "Scheduler failed for also_doesnt_exist" in captured.out
            assert "doesnt_exist not found at module scope" in captured.out


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_run_scheduled_on_time_boundary(external_repo_context):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("simple_schedule")

        schedule_origin = external_schedule.get_origin()
        initial_datetime = pendulum.datetime(
            year=2019, month=2, day=27, hour=0, minute=0, second=0,
        )
        with pendulum.test(initial_datetime):
            # Start schedule exactly at midnight
            instance.start_schedule_and_update_storage_state(external_schedule)

            launch_scheduled_runs(instance, get_default_scheduler_logger(), pendulum.now("UTC"))

            assert instance.get_runs_count() == 1
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            assert ticks[0].status == ScheduleTickStatus.SUCCESS


def test_bad_load(capfd):
    with schedule_instance() as instance:
        fake_origin = _get_unloadable_schedule_origin()
        initial_datetime = pendulum.datetime(
            year=2019, month=2, day=27, hour=23, minute=59, second=59,
        )
        with pendulum.test(initial_datetime):
            schedule_state = ScheduleState(
                fake_origin, ScheduleStatus.RUNNING, "0 0 * * *", pendulum.now("UTC").timestamp(),
            )
            instance.add_schedule_state(schedule_state)

        initial_datetime = initial_datetime.add(seconds=1)
        with pendulum.test(initial_datetime):
            launch_scheduled_runs(instance, get_default_scheduler_logger(), pendulum.now("UTC"))

            assert instance.get_runs_count() == 0

            ticks = instance.get_schedule_ticks(fake_origin.get_id())

            assert len(ticks) == 0

            captured = capfd.readouterr()
            assert "Scheduler failed for also_doesnt_exist" in captured.out
            assert "doesnt_exist not found at module scope" in captured.out

        initial_datetime = initial_datetime.add(days=1)
        with pendulum.test(initial_datetime):
            launch_scheduled_runs(instance, get_default_scheduler_logger(), pendulum.now("UTC"))
            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(fake_origin.get_id())
            assert len(ticks) == 0


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_multiple_schedules_on_different_time_ranges(external_repo_context, capfd):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        external_hourly_schedule = external_repo.get_external_schedule("simple_hourly_schedule")
        initial_datetime = pendulum.datetime(
            year=2019, month=2, day=27, hour=23, minute=59, second=59,
        ).in_tz("US/Central")
        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)
            instance.start_schedule_and_update_storage_state(external_hourly_schedule)

        initial_datetime = initial_datetime.add(seconds=2)
        with pendulum.test(initial_datetime):
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"),
            )

            assert instance.get_runs_count() == 2
            ticks = instance.get_schedule_ticks(external_schedule.get_origin_id())
            assert len(ticks) == 1
            assert ticks[0].status == ScheduleTickStatus.SUCCESS

            hourly_ticks = instance.get_schedule_ticks(external_hourly_schedule.get_origin_id())
            assert len(hourly_ticks) == 1
            assert hourly_ticks[0].status == ScheduleTickStatus.SUCCESS

            captured = capfd.readouterr()

            assert (
                captured.out
                == """2019-02-27 18:00:01 - dagster-scheduler - INFO - Checking for new runs for the following schedules: simple_hourly_schedule, simple_schedule
2019-02-27 18:00:01 - dagster-scheduler - INFO - Launching run for simple_hourly_schedule at 2019-02-28 00:00:00+0000
2019-02-27 18:00:01 - dagster-scheduler - INFO - Completed scheduled launch of run {first_run_id} for simple_hourly_schedule
2019-02-27 18:00:01 - dagster-scheduler - INFO - Launching run for simple_schedule at 2019-02-28 00:00:00+0000
2019-02-27 18:00:01 - dagster-scheduler - INFO - Completed scheduled launch of run {second_run_id} for simple_schedule
""".format(
                    first_run_id=instance.get_runs()[1].run_id,
                    second_run_id=instance.get_runs()[0].run_id,
                )
            )

        initial_datetime = initial_datetime.add(hours=1)
        with pendulum.test(initial_datetime):
            launch_scheduled_runs(instance, get_default_scheduler_logger(), pendulum.now("UTC"))

            assert instance.get_runs_count() == 3

            ticks = instance.get_schedule_ticks(external_schedule.get_origin_id())
            assert len(ticks) == 1
            assert ticks[0].status == ScheduleTickStatus.SUCCESS

            hourly_ticks = instance.get_schedule_ticks(external_hourly_schedule.get_origin_id())
            assert len(hourly_ticks) == 2
            assert (
                len([tick for tick in hourly_ticks if tick.status == ScheduleTickStatus.SUCCESS])
                == 2
            )

            captured = capfd.readouterr()
            assert (
                captured.out
                == """2019-02-27 19:00:01 - dagster-scheduler - INFO - Checking for new runs for the following schedules: simple_hourly_schedule, simple_schedule
2019-02-27 19:00:01 - dagster-scheduler - INFO - Launching run for simple_hourly_schedule at 2019-02-28 01:00:00+0000
2019-02-27 19:00:01 - dagster-scheduler - INFO - Completed scheduled launch of run {third_run_id} for simple_hourly_schedule
2019-02-27 19:00:01 - dagster-scheduler - INFO - No new runs for simple_schedule
""".format(
                    third_run_id=instance.get_runs()[0].run_id
                )
            )


@pytest.mark.parametrize(
    "external_repo_context", [default_repo, grpc_repo],
)
def test_launch_failure(external_repo_context, capfd):
    with instance_with_schedules(
        external_repo_context,
        overrides={
            "run_launcher": {"module": "dagster.core.test_utils", "class": "ExplodingRunLauncher",},
        },
    ) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("simple_schedule")

        schedule_origin = external_schedule.get_origin()
        initial_datetime = pendulum.datetime(
            year=2019, month=2, day=27, hour=0, minute=0, second=0,
        ).in_tz("US/Central")

        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            launch_scheduled_runs(instance, get_default_scheduler_logger(), pendulum.now("UTC"))

            assert instance.get_runs_count() == 1

            run = instance.get_runs()[0]

            validate_run_started(run, initial_datetime, "2019-02-26", expected_success=False)

            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                ScheduleTickStatus.SUCCESS,
                run.run_id,
            )

            captured = capfd.readouterr()
            assert (
                captured.out
                == """2019-02-26 18:00:00 - dagster-scheduler - INFO - Checking for new runs for the following schedules: simple_schedule
2019-02-26 18:00:00 - dagster-scheduler - INFO - Launching run for simple_schedule at 2019-02-27 00:00:00+0000
2019-02-26 18:00:00 - dagster-scheduler - ERROR - Run {run_id} created successfully but failed to launch.
""".format(
                    run_id=instance.get_runs()[0].run_id
                )
            )


def test_max_catchup_runs(capfd):
    initial_datetime = pendulum.datetime(
        year=2019, month=2, day=27, hour=23, minute=59, second=59
    ).in_tz("US/Central")
    with instance_with_schedules(grpc_repo) as (instance, external_repo):
        with pendulum.test(initial_datetime):
            external_schedule = external_repo.get_external_schedule("simple_schedule")
            schedule_origin = external_schedule.get_origin()
            instance.start_schedule_and_update_storage_state(external_schedule)

        initial_datetime = initial_datetime.add(days=5)
        with pendulum.test(initial_datetime):
            # Day is now March 4 at 11:59PM
            launch_scheduled_runs(
                instance, get_default_scheduler_logger(), pendulum.now("UTC"), max_catchup_runs=2,
            )

            assert instance.get_runs_count() == 2
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 2

            first_datetime = pendulum.datetime(year=2019, month=3, day=4)

            wait_for_all_runs_to_start(instance)

            validate_tick(
                ticks[0],
                external_schedule,
                first_datetime,
                ScheduleTickStatus.SUCCESS,
                instance.get_runs()[0].run_id,
            )
            validate_run_started(instance.get_runs()[0], first_datetime, "2019-03-03")

            second_datetime = pendulum.datetime(year=2019, month=3, day=3)

            validate_tick(
                ticks[1],
                external_schedule,
                second_datetime,
                ScheduleTickStatus.SUCCESS,
                instance.get_runs()[1].run_id,
            )

            validate_run_started(instance.get_runs()[1], second_datetime, "2019-03-02")

            captured = capfd.readouterr()
            assert (
                captured.out
                == """2019-03-04 17:59:59 - dagster-scheduler - INFO - Checking for new runs for the following schedules: simple_schedule
2019-03-04 17:59:59 - dagster-scheduler - WARNING - simple_schedule has fallen behind, only launching 2 runs
2019-03-04 17:59:59 - dagster-scheduler - INFO - Launching 2 runs for simple_schedule at the following times: 2019-03-03 00:00:00+0000, 2019-03-04 00:00:00+0000
2019-03-04 17:59:59 - dagster-scheduler - INFO - Completed scheduled launch of run {first_run_id} for simple_schedule
2019-03-04 17:59:59 - dagster-scheduler - INFO - Completed scheduled launch of run {second_run_id} for simple_schedule
""".format(
                    first_run_id=instance.get_runs()[1].run_id,
                    second_run_id=instance.get_runs()[0].run_id,
                )
            )
