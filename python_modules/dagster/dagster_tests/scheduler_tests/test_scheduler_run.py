import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

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
from dagster.scheduler.scheduler import launch_scheduled_runs
from dagster.seven import (
    get_current_datetime_in_utc,
    get_timestamp_from_utc_datetime,
    get_utc_timezone,
)
from dagster.utils import merge_dicts

_COUPLE_DAYS_AGO = datetime(year=2019, month=2, day=25)


def _throw(_context):
    raise Exception("bananas")


def _throw_on_odd_day(context):
    launch_time = context.scheduled_execution_time_utc

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


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    end_date=datetime(year=2019, month=3, day=1),
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
        bad_env_fn_schedule,
        bad_should_execute_schedule,
        bad_should_execute_schedule_on_odd_days,
        skip_schedule,
        wrong_config_schedule,
    ]


def schedule_instance(overrides=None):
    return instance_for_test(
        overrides=merge_dicts(
            {
                "scheduler": {
                    "module": "dagster.core.scheduler",
                    "class": "DagsterCommandLineScheduler",
                }
            },
            (overrides if overrides else {}),
        )
    )


@contextmanager
def instance_with_schedules(external_repo_context, overrides=None):
    with schedule_instance(overrides) as instance:
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
def cli_api_repo():
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable, python_file=__file__, attribute="the_repo",
    )

    yield PythonEnvRepositoryLocation(
        RepositoryLocationHandle.create_python_env_location(
            loadable_target_origin=loadable_target_origin, location_name="test_location",
        )
    ).get_repository("the_repo")


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
    assert tick_data.timestamp == get_timestamp_from_utc_datetime(expected_datetime)
    assert tick_data.status == expected_status
    assert tick_data.run_id == expected_run_id
    if expected_error:
        assert expected_error in tick_data.error.message


def validate_run_started(run, expected_datetime, expected_partition, expected_success=True):
    assert run.tags[SCHEDULED_EXECUTION_TIME_TAG] == expected_datetime.isoformat()
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
    "external_repo_context", [cli_api_repo, grpc_repo],
)
def test_simple_schedule(external_repo_context):
    initial_datetime = datetime(
        year=2019, month=2, day=27, hour=23, minute=59, second=59, tzinfo=get_utc_timezone(),
    )
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        with freeze_time(initial_datetime) as frozen_datetime:
            external_schedule = external_repo.get_external_schedule("simple_schedule")

            schedule_origin = external_schedule.get_origin()

            instance.start_schedule_and_update_storage_state(external_schedule)

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

            # launch_scheduled_runs does nothing before the first tick
            launch_scheduled_runs(instance, get_current_datetime_in_utc())
            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

            # Move forward in time so we're past a tick
            frozen_datetime.tick(delta=timedelta(seconds=2))
            launch_scheduled_runs(instance, get_current_datetime_in_utc())

            assert instance.get_runs_count() == 1
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1

            expected_datetime = datetime(year=2019, month=2, day=28, tzinfo=get_utc_timezone())

            validate_tick(
                ticks[0],
                external_schedule,
                expected_datetime,
                ScheduleTickStatus.SUCCESS,
                instance.get_runs()[0].run_id,
            )

            wait_for_all_runs_to_start(instance)
            validate_run_started(instance.get_runs()[0], expected_datetime, "2019-02-27")

            # Verify idempotence
            launch_scheduled_runs(instance, get_current_datetime_in_utc())
            assert instance.get_runs_count() == 1
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            assert ticks[0].status == ScheduleTickStatus.SUCCESS

            # Verify advancing in time but not going past a tick doesn't add any new runs
            frozen_datetime.tick(delta=timedelta(seconds=2))
            launch_scheduled_runs(instance, get_current_datetime_in_utc())
            assert instance.get_runs_count() == 1
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            assert ticks[0].status == ScheduleTickStatus.SUCCESS

            # Traveling two more days in the future before running results in two new ticks
            frozen_datetime.tick(delta=timedelta(days=2))
            launch_scheduled_runs(instance, get_current_datetime_in_utc())
            assert instance.get_runs_count() == 3
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 3
            assert len([tick for tick in ticks if tick.status == ScheduleTickStatus.SUCCESS]) == 3

            runs_by_partition = {run.tags[PARTITION_NAME_TAG]: run for run in instance.get_runs()}

            assert "2019-02-28" in runs_by_partition
            assert "2019-03-01" in runs_by_partition

            # Check idempotence again
            launch_scheduled_runs(instance, get_current_datetime_in_utc())
            assert instance.get_runs_count() == 3
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 3


@pytest.mark.parametrize(
    "external_repo_context", [cli_api_repo, grpc_repo],
)
def test_bad_env_fn(external_repo_context):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("bad_env_fn_schedule")
        schedule_origin = external_schedule.get_origin()
        initial_datetime = datetime(
            year=2019, month=2, day=27, hour=0, minute=0, second=0, tzinfo=get_utc_timezone(),
        )
        with freeze_time(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            launch_scheduled_runs(instance, get_current_datetime_in_utc())

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


@pytest.mark.parametrize(
    "external_repo_context", [cli_api_repo, grpc_repo],
)
def test_bad_should_execute(external_repo_context):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("bad_should_execute_schedule")
        schedule_origin = external_schedule.get_origin()
        initial_datetime = datetime(
            year=2019, month=2, day=27, hour=0, minute=0, second=0, tzinfo=get_utc_timezone(),
        )
        with freeze_time(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            launch_scheduled_runs(instance, get_current_datetime_in_utc())

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


@pytest.mark.parametrize(
    "external_repo_context", [cli_api_repo, grpc_repo],
)
def test_skip(external_repo_context):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("skip_schedule")
        schedule_origin = external_schedule.get_origin()
        initial_datetime = datetime(
            year=2019, month=2, day=27, hour=0, minute=0, second=0, tzinfo=get_utc_timezone(),
        )
        with freeze_time(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            launch_scheduled_runs(instance, get_current_datetime_in_utc())

            assert instance.get_runs_count() == 0
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0], external_schedule, initial_datetime, ScheduleTickStatus.SKIPPED, None,
            )


@pytest.mark.parametrize(
    "external_repo_context", [cli_api_repo, grpc_repo],
)
def test_wrong_config(external_repo_context):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("wrong_config_schedule")
        schedule_origin = external_schedule.get_origin()
        initial_datetime = datetime(
            year=2019, month=2, day=27, hour=0, minute=0, second=0, tzinfo=get_utc_timezone(),
        )
        with freeze_time(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            launch_scheduled_runs(instance, get_current_datetime_in_utc())

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


@pytest.mark.parametrize(
    "external_repo_context", [cli_api_repo, grpc_repo],
)
def test_bad_schedule_mixed_with_good_schedule(external_repo_context):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        good_schedule = external_repo.get_external_schedule("simple_schedule")
        bad_schedule = external_repo.get_external_schedule(
            "bad_should_execute_schedule_on_odd_days"
        )

        good_origin = good_schedule.get_origin()
        bad_origin = bad_schedule.get_origin()
        initial_datetime = datetime(
            year=2019, month=2, day=27, hour=0, minute=0, second=0, tzinfo=get_utc_timezone(),
        )
        with freeze_time(initial_datetime) as frozen_datetime:
            instance.start_schedule_and_update_storage_state(good_schedule)
            instance.start_schedule_and_update_storage_state(bad_schedule)

            launch_scheduled_runs(instance, get_current_datetime_in_utc())

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
                "Error occurred during the execution of should_execute for schedule bad_should_execute_schedule"
                in bad_ticks[0].error.message
            )

            frozen_datetime.tick(delta=timedelta(days=1))

            new_now = get_current_datetime_in_utc()

            launch_scheduled_runs(instance, get_current_datetime_in_utc())

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


@pytest.mark.parametrize(
    "external_repo_context", [cli_api_repo, grpc_repo],
)
def test_run_scheduled_on_time_boundary(external_repo_context):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("simple_schedule")

        schedule_origin = external_schedule.get_origin()
        initial_datetime = datetime(
            year=2019, month=2, day=27, hour=0, minute=0, second=0, tzinfo=get_utc_timezone(),
        )
        with freeze_time(initial_datetime):
            # Start schedule exactly at midnight
            instance.start_schedule_and_update_storage_state(external_schedule)

            launch_scheduled_runs(instance, get_current_datetime_in_utc())

            assert instance.get_runs_count() == 1
            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            assert ticks[0].status == ScheduleTickStatus.SUCCESS


def test_bad_load():
    with schedule_instance() as instance:
        working_directory = os.path.dirname(__file__)
        recon_repo = ReconstructableRepository.for_file(__file__, "doesnt_exist", working_directory)
        schedule = recon_repo.get_reconstructable_schedule("also_doesnt_exist")
        fake_origin = schedule.get_origin()

        initial_datetime = datetime(
            year=2019, month=2, day=27, hour=23, minute=59, second=59, tzinfo=get_utc_timezone(),
        )
        with freeze_time(initial_datetime) as frozen_datetime:
            schedule_state = ScheduleState(
                fake_origin,
                ScheduleStatus.RUNNING,
                "0 0 * * *",
                get_timestamp_from_utc_datetime(get_current_datetime_in_utc()),
            )
            instance.add_schedule_state(schedule_state)

            frozen_datetime.tick(delta=timedelta(seconds=1))

            launch_scheduled_runs(instance, get_current_datetime_in_utc())

            assert instance.get_runs_count() == 0

            ticks = instance.get_schedule_ticks(fake_origin.get_id())

            assert len(ticks) == 1
            assert ticks[0].status == ScheduleTickStatus.FAILURE
            assert ticks[0].timestamp == get_timestamp_from_utc_datetime(
                get_current_datetime_in_utc()
            )
            assert "doesnt_exist not found at module scope in file" in ticks[0].error.message

            frozen_datetime.tick(delta=timedelta(days=1))

            launch_scheduled_runs(instance, get_current_datetime_in_utc())

            assert instance.get_runs_count() == 0

            ticks = instance.get_schedule_ticks(fake_origin.get_id())

            assert len(ticks) == 2
            assert ticks[0].status == ScheduleTickStatus.FAILURE
            assert ticks[0].timestamp == get_timestamp_from_utc_datetime(
                get_current_datetime_in_utc()
            )
            assert "doesnt_exist not found at module scope in file" in ticks[0].error.message


@pytest.mark.parametrize(
    "external_repo_context", [cli_api_repo, grpc_repo],
)
def test_multiple_schedules_on_different_time_ranges(external_repo_context):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        external_hourly_schedule = external_repo.get_external_schedule("simple_hourly_schedule")
        initial_datetime = datetime(
            year=2019, month=2, day=27, hour=23, minute=59, second=59, tzinfo=get_utc_timezone(),
        )
        with freeze_time(initial_datetime) as frozen_datetime:
            instance.start_schedule_and_update_storage_state(external_schedule)
            instance.start_schedule_and_update_storage_state(external_hourly_schedule)
            frozen_datetime.tick(delta=timedelta(seconds=2))

            launch_scheduled_runs(instance, get_current_datetime_in_utc())

            assert instance.get_runs_count() == 2
            ticks = instance.get_schedule_ticks(external_schedule.get_origin_id())
            assert len(ticks) == 1
            assert ticks[0].status == ScheduleTickStatus.SUCCESS

            hourly_ticks = instance.get_schedule_ticks(external_hourly_schedule.get_origin_id())
            assert len(hourly_ticks) == 1
            assert hourly_ticks[0].status == ScheduleTickStatus.SUCCESS

            frozen_datetime.tick(delta=timedelta(hours=1))

            launch_scheduled_runs(instance, get_current_datetime_in_utc())

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


@pytest.mark.parametrize(
    "external_repo_context", [cli_api_repo, grpc_repo],
)
def test_launch_failure(external_repo_context):
    with instance_with_schedules(
        external_repo_context,
        overrides={
            "run_launcher": {"module": "dagster.core.test_utils", "class": "ExplodingRunLauncher",},
        },
    ) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("simple_schedule")

        schedule_origin = external_schedule.get_origin()
        initial_datetime = datetime(
            year=2019, month=2, day=27, hour=0, minute=0, second=0, tzinfo=get_utc_timezone(),
        )

        with freeze_time(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            launch_scheduled_runs(instance, get_current_datetime_in_utc())

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
