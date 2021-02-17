import datetime
import os
import sys
import tempfile
import time
from contextlib import contextmanager

import pendulum
import pytest
from dagster import (
    DagsterEventType,
    ScheduleDefinition,
    daily_schedule,
    hourly_schedule,
    pipeline,
    repository,
    schedule,
    seven,
    solid,
)
from dagster.core.definitions.job import RunRequest
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.errors import DagsterScheduleWipeRequired
from dagster.core.host_representation import (
    ExternalRepositoryOrigin,
    InProcessRepositoryLocationOrigin,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
)
from dagster.core.scheduler.job import JobState, JobStatus, JobTickStatus, JobType, ScheduleJobData
from dagster.core.storage.pipeline_run import PipelineRunStatus, PipelineRunsFilter
from dagster.core.storage.tags import PARTITION_NAME_TAG, SCHEDULED_EXECUTION_TIME_TAG
from dagster.core.test_utils import (
    instance_for_test,
    instance_for_test_tempdir,
    mock_system_timezone,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.daemon import get_default_daemon_logger
from dagster.scheduler.scheduler import launch_scheduled_runs
from dagster.seven import create_pendulum_time, to_timezone
from dagster.utils import merge_dicts
from dagster.utils.partitions import DEFAULT_DATE_FORMAT

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


@solid(config_schema={"partition_time": str})
def the_solid(context):
    return "Ran at this partition date: {}".format(context.solid_config["partition_time"])


@pipeline
def the_pipeline():
    the_solid()


def _solid_config(date):
    return {
        "solids": {"the_solid": {"config": {"partition_time": date.isoformat()}}},
    }


@daily_schedule(pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO, execution_timezone="UTC")
def simple_schedule(date):
    return _solid_config(date)


@daily_schedule(pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO)
def daily_schedule_without_timezone(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO, execution_timezone="US/Central"
)
def daily_central_time_schedule(date):
    return _solid_config(date)


@schedule(
    pipeline_name="the_pipeline", cron_schedule="*/5 * * * *", execution_timezone="US/Central"
)
def partitionless_schedule(context):
    return _solid_config(context.scheduled_execution_time)


# Schedule that runs on a different day in Central Time vs UTC
@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_time=datetime.time(hour=23, minute=0),
    execution_timezone="US/Central",
)
def daily_late_schedule(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_time=datetime.time(hour=2, minute=30),
    execution_timezone="US/Central",
)
def daily_dst_transition_schedule_skipped_time(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_time=datetime.time(hour=1, minute=30),
    execution_timezone="US/Central",
)
def daily_dst_transition_schedule_doubled_time(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="US/Eastern",
)
def daily_eastern_time_schedule(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    end_date=datetime.datetime(year=2019, month=3, day=1),
    execution_timezone="UTC",
)
def simple_temporary_schedule(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="UTC",
)
def bad_env_fn_schedule():  # forgot context arg
    return {}


@hourly_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="UTC",
)
def simple_hourly_schedule(date):
    return _solid_config(date)


@hourly_schedule(
    pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO, execution_timezone="US/Central"
)
def hourly_central_time_schedule(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    should_execute=_throw,
    execution_timezone="UTC",
)
def bad_should_execute_schedule(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    should_execute=_throw_on_odd_day,
    execution_timezone="UTC",
)
def bad_should_execute_schedule_on_odd_days(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    should_execute=_never,
    execution_timezone="UTC",
)
def skip_schedule(date):
    return _solid_config(date)


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="UTC",
)
def wrong_config_schedule(_date):
    return {}


def define_multi_run_schedule():
    def gen_runs(context):
        if not context.scheduled_execution_time:
            date = pendulum.now().subtract(days=1)
        else:
            date = pendulum.instance(context.scheduled_execution_time).subtract(days=1)

        yield RunRequest(run_key="A", run_config=_solid_config(date), tags={"label": "A"})
        yield RunRequest(run_key="B", run_config=_solid_config(date), tags={"label": "B"})

    return ScheduleDefinition(
        name="multi_run_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="the_pipeline",
        execution_timezone="UTC",
        execution_fn=gen_runs,
    )


def define_multi_run_schedule_with_missing_run_key():
    def gen_runs(context):
        if not context.scheduled_execution_time:
            date = pendulum.now().subtract(days=1)
        else:
            date = pendulum.instance(context.scheduled_execution_time).subtract(days=1)

        yield RunRequest(run_key="A", run_config=_solid_config(date), tags={"label": "A"})
        yield RunRequest(run_key=None, run_config=_solid_config(date), tags={"label": "B"})

    return ScheduleDefinition(
        name="multi_run_schedule_with_missing_run_key",
        cron_schedule="0 0 * * *",
        pipeline_name="the_pipeline",
        execution_timezone="UTC",
        execution_fn=gen_runs,
    )


@pipeline
def the_other_pipeline():
    the_solid()


@repository
def the_other_repo():
    return [
        the_other_pipeline,
    ]


@repository
def the_repo():
    return [
        the_pipeline,
        simple_schedule,
        simple_temporary_schedule,
        simple_hourly_schedule,
        daily_schedule_without_timezone,
        daily_late_schedule,
        daily_dst_transition_schedule_skipped_time,
        daily_dst_transition_schedule_doubled_time,
        daily_central_time_schedule,
        daily_eastern_time_schedule,
        hourly_central_time_schedule,
        bad_env_fn_schedule,
        bad_should_execute_schedule,
        bad_should_execute_schedule_on_odd_days,
        skip_schedule,
        wrong_config_schedule,
        define_multi_run_schedule(),
        define_multi_run_schedule_with_missing_run_key(),
        partitionless_schedule,
    ]


def schedule_instance(overrides=None):
    return instance_for_test(
        overrides=merge_dicts(
            {
                "scheduler": {
                    "module": "dagster.core.scheduler",
                    "class": "DagsterDaemonScheduler",
                },
            },
            (overrides if overrides else {}),
        )
    )


def logger():
    return get_default_daemon_logger("SchedulerDaemon")


@contextmanager
def instance_with_schedules(external_repo_context, overrides=None):
    with schedule_instance(overrides) as instance:
        with external_repo_context() as external_repo:
            yield (instance, external_repo)


@contextmanager
def default_repo():
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        python_file=__file__,
        working_directory=os.getcwd(),
    )

    with ManagedGrpcPythonEnvRepositoryLocationOrigin(
        loadable_target_origin=loadable_target_origin,
        location_name="test_location",
    ).create_handle() as handle:
        yield handle.create_location().get_repository("the_repo")


def repos():
    return [default_repo]


def validate_tick(
    tick,
    external_schedule,
    expected_datetime,
    expected_status,
    expected_run_ids,
    expected_error=None,
):
    tick_data = tick.job_tick_data
    assert tick_data.job_origin_id == external_schedule.get_external_origin_id()
    assert tick_data.job_name == external_schedule.name
    assert tick_data.timestamp == expected_datetime.timestamp()
    assert tick_data.status == expected_status
    assert set(tick_data.run_ids) == set(expected_run_ids)
    if expected_error:
        assert expected_error in tick_data.error.message


def validate_run_started(
    run,
    execution_time,
    partition_time=None,
    partition_fmt=DEFAULT_DATE_FORMAT,
    expected_success=True,
):
    assert run.tags[SCHEDULED_EXECUTION_TIME_TAG] == to_timezone(execution_time, "UTC").isoformat()

    if partition_time:
        assert run.tags[PARTITION_NAME_TAG] == partition_time.strftime(partition_fmt)

    if expected_success:
        assert (
            run.status == PipelineRunStatus.STARTED
            or run.status == PipelineRunStatus.STARTING
            or run.status == PipelineRunStatus.SUCCESS
        )

        if partition_time:
            assert run.run_config == _solid_config(partition_time)
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


@pytest.mark.parametrize("external_repo_context", repos())
def test_simple_schedule(external_repo_context, capfd):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        with pendulum.test(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("simple_schedule")

            schedule_origin = external_schedule.get_external_origin()

            instance.start_schedule_and_update_storage_state(external_schedule)

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

            # launch_scheduled_runs does nothing before the first tick
            list(
                launch_scheduled_runs(
                    instance,
                    logger(),
                    pendulum.now("UTC"),
                )
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

            captured = capfd.readouterr()

            assert (
                captured.out
                == """2019-02-27 17:59:59 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: simple_schedule
2019-02-27 17:59:59 - SchedulerDaemon - INFO - No new runs for simple_schedule
"""
            )

        freeze_datetime = freeze_datetime.add(seconds=2)
        with pendulum.test(freeze_datetime):
            list(
                launch_scheduled_runs(
                    instance,
                    logger(),
                    pendulum.now("UTC"),
                )
            )

            assert instance.get_runs_count() == 1
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 1

            expected_datetime = create_pendulum_time(year=2019, month=2, day=28)

            validate_tick(
                ticks[0],
                external_schedule,
                expected_datetime,
                JobTickStatus.SUCCESS,
                [run.run_id for run in instance.get_runs()],
            )

            wait_for_all_runs_to_start(instance)
            validate_run_started(
                instance.get_runs()[0],
                execution_time=create_pendulum_time(2019, 2, 28),
                partition_time=create_pendulum_time(2019, 2, 27),
            )

            captured = capfd.readouterr()

            assert (
                captured.out
                == """2019-02-27 18:00:01 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: simple_schedule
2019-02-27 18:00:01 - SchedulerDaemon - INFO - Evaluating schedule `simple_schedule` at 2019-02-28 00:00:00+0000
2019-02-27 18:00:01 - SchedulerDaemon - INFO - Completed scheduled launch of run {run_id} for simple_schedule
""".format(
                    run_id=instance.get_runs()[0].run_id
                )
            )

            # Verify idempotence
            list(
                launch_scheduled_runs(
                    instance,
                    logger(),
                    pendulum.now("UTC"),
                )
            )
            assert instance.get_runs_count() == 1
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            assert ticks[0].status == JobTickStatus.SUCCESS

        # Verify advancing in time but not going past a tick doesn't add any new runs
        freeze_datetime = freeze_datetime.add(seconds=2)
        with pendulum.test(freeze_datetime):
            list(
                launch_scheduled_runs(
                    instance,
                    logger(),
                    pendulum.now("UTC"),
                )
            )
            assert instance.get_runs_count() == 1
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            assert ticks[0].status == JobTickStatus.SUCCESS

        freeze_datetime = freeze_datetime.add(days=2)
        with pendulum.test(freeze_datetime):
            capfd.readouterr()

            # Traveling two more days in the future before running results in two new ticks
            list(
                launch_scheduled_runs(
                    instance,
                    logger(),
                    pendulum.now("UTC"),
                )
            )
            assert instance.get_runs_count() == 3
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 3
            assert len([tick for tick in ticks if tick.status == JobTickStatus.SUCCESS]) == 3

            runs_by_partition = {run.tags[PARTITION_NAME_TAG]: run for run in instance.get_runs()}

            assert "2019-02-28" in runs_by_partition
            assert "2019-03-01" in runs_by_partition

            captured = capfd.readouterr()

            assert captured.out == """2019-03-01 18:00:03 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: simple_schedule
2019-03-01 18:00:03 - SchedulerDaemon - INFO - Evaluating schedule `simple_schedule` at the following times: 2019-03-01 00:00:00+0000, 2019-03-02 00:00:00+0000
2019-03-01 18:00:03 - SchedulerDaemon - INFO - Completed scheduled launch of run {first_run_id} for simple_schedule
2019-03-01 18:00:03 - SchedulerDaemon - INFO - Completed scheduled launch of run {second_run_id} for simple_schedule
""".format(
                first_run_id=instance.get_runs()[1].run_id,
                second_run_id=instance.get_runs()[0].run_id,
            )

            # Check idempotence again
            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))
            assert instance.get_runs_count() == 3
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 3


@pytest.mark.parametrize("external_repo_context", repos())
def test_no_started_schedules(external_repo_context, capfd):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        schedule_origin = external_schedule.get_external_origin()

        list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))
        assert instance.get_runs_count() == 0

        ticks = instance.get_job_ticks(schedule_origin.get_id())
        assert len(ticks) == 0

        captured = capfd.readouterr()

        assert "Not checking for any runs since no schedules have been started." in captured.out


@pytest.mark.parametrize("external_repo_context", repos())
def test_schedule_without_timezone(external_repo_context, capfd):
    with mock_system_timezone("US/Eastern"):
        with instance_with_schedules(external_repo_context) as (
            instance,
            external_repo,
        ):
            external_schedule = external_repo.get_external_schedule(
                "daily_schedule_without_timezone"
            )
            schedule_origin = external_schedule.get_external_origin()
            initial_datetime = create_pendulum_time(
                year=2019, month=2, day=27, hour=0, minute=0, second=0, tz="US/Eastern"
            )

            with pendulum.test(initial_datetime):

                instance.start_schedule_and_update_storage_state(external_schedule)

                list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))

                assert instance.get_runs_count() == 1

                ticks = instance.get_job_ticks(schedule_origin.get_id())

                assert len(ticks) == 1

                captured = capfd.readouterr()

                assert (
                    "Using the system timezone, US/Eastern, for daily_schedule_without_timezone as it did not specify an execution_timezone in its definition. "
                    "Specifying an execution_timezone on all schedules will be required in the dagster 0.11.0 release."
                    in captured.out
                )

                expected_datetime = to_timezone(
                    create_pendulum_time(year=2019, month=2, day=27, tz="US/Eastern"), "UTC"
                )

                validate_tick(
                    ticks[0],
                    external_schedule,
                    expected_datetime,
                    JobTickStatus.SUCCESS,
                    [run.run_id for run in instance.get_runs()],
                )

                wait_for_all_runs_to_start(instance)
                validate_run_started(
                    instance.get_runs()[0],
                    execution_time=expected_datetime,
                    partition_time=create_pendulum_time(2019, 2, 26, tz="US/Eastern"),
                )

                # Verify idempotence
                list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))
                assert instance.get_runs_count() == 1
                ticks = instance.get_job_ticks(schedule_origin.get_id())
                assert len(ticks) == 1


@pytest.mark.parametrize("external_repo_context", repos())
def test_bad_env_fn(external_repo_context, capfd):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("bad_env_fn_schedule")
        schedule_origin = external_schedule.get_external_origin()
        initial_datetime = create_pendulum_time(
            year=2019, month=2, day=27, hour=0, minute=0, second=0
        )
        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                JobTickStatus.FAILURE,
                [run.run_id for run in instance.get_runs()],
                "Error occurred during the execution of run_config_fn for schedule bad_env_fn_schedule",
            )

            captured = capfd.readouterr()

            assert "Failed to fetch schedule data for bad_env_fn_schedule: " in captured.out

            assert (
                "Error occurred during the execution of run_config_fn for schedule bad_env_fn_schedule"
                in captured.out
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_bad_should_execute(external_repo_context, capfd):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("bad_should_execute_schedule")
        schedule_origin = external_schedule.get_external_origin()
        initial_datetime = create_pendulum_time(
            year=2019,
            month=2,
            day=27,
            hour=0,
            minute=0,
            second=0,
        )
        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                JobTickStatus.FAILURE,
                [run.run_id for run in instance.get_runs()],
                "Error occurred during the execution of should_execute for schedule bad_should_execute_schedule",
            )

            captured = capfd.readouterr()
            assert (
                "Failed to fetch schedule data for bad_should_execute_schedule: "
            ) in captured.out

            assert (
                "Error occurred during the execution of should_execute for schedule bad_should_execute_schedule"
                in captured.out
            )

            assert "Exception: bananas" in captured.out


@pytest.mark.parametrize("external_repo_context", repos())
def test_skip(external_repo_context, capfd):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("skip_schedule")
        schedule_origin = external_schedule.get_external_origin()
        initial_datetime = to_timezone(
            create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0, tz="UTC"),
            "US/Central",
        )
        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                JobTickStatus.SKIPPED,
                [run.run_id for run in instance.get_runs()],
            )

            captured = capfd.readouterr()
            assert (
                captured.out
                == """2019-02-26 18:00:00 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: skip_schedule
2019-02-26 18:00:00 - SchedulerDaemon - INFO - Evaluating schedule `skip_schedule` at 2019-02-27 00:00:00+0000
2019-02-26 18:00:00 - SchedulerDaemon - INFO - No run requests returned for skip_schedule, skipping
"""
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_wrong_config(external_repo_context, capfd):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("wrong_config_schedule")
        schedule_origin = external_schedule.get_external_origin()
        initial_datetime = create_pendulum_time(
            year=2019, month=2, day=27, hour=0, minute=0, second=0
        )
        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))

            assert instance.get_runs_count() == 1

            wait_for_all_runs_to_start(instance)

            run = instance.get_runs()[0]

            validate_run_started(
                run,
                execution_time=initial_datetime,
                partition_time=create_pendulum_time(2019, 2, 26),
                expected_success=False,
            )

            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                JobTickStatus.SUCCESS,
                [run.run_id for run in instance.get_runs()],
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
            assert 'Missing required config entry "solids" at the root.' in captured.out


def _get_unloadable_schedule_origin():
    working_directory = os.path.dirname(__file__)
    recon_repo = ReconstructableRepository.for_file(__file__, "doesnt_exist", working_directory)
    return ExternalRepositoryOrigin(
        InProcessRepositoryLocationOrigin(recon_repo), "fake_repository"
    ).get_job_origin("doesnt_exist")


@pytest.mark.parametrize("external_repo_context", repos())
def test_bad_schedules_mixed_with_good_schedule(external_repo_context, capfd):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        good_schedule = external_repo.get_external_schedule("simple_schedule")
        bad_schedule = external_repo.get_external_schedule(
            "bad_should_execute_schedule_on_odd_days"
        )

        good_origin = good_schedule.get_external_origin()
        bad_origin = bad_schedule.get_external_origin()
        unloadable_origin = _get_unloadable_schedule_origin()
        initial_datetime = create_pendulum_time(
            year=2019,
            month=2,
            day=27,
            hour=0,
            minute=0,
            second=0,
        )
        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(good_schedule)
            instance.start_schedule_and_update_storage_state(bad_schedule)

            unloadable_schedule_state = JobState(
                unloadable_origin,
                JobType.SCHEDULE,
                JobStatus.RUNNING,
                ScheduleJobData(
                    "0 0 * * *", pendulum.now("UTC").timestamp(), "DagsterDaemonScheduler"
                ),
            )
            instance.add_job_state(unloadable_schedule_state)

            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))

            assert instance.get_runs_count() == 1
            wait_for_all_runs_to_start(instance)
            validate_run_started(
                instance.get_runs()[0],
                execution_time=initial_datetime,
                partition_time=create_pendulum_time(2019, 2, 26),
            )

            good_ticks = instance.get_job_ticks(good_origin.get_id())
            assert len(good_ticks) == 1
            validate_tick(
                good_ticks[0],
                good_schedule,
                initial_datetime,
                JobTickStatus.SUCCESS,
                [run.run_id for run in instance.get_runs()],
            )

            bad_ticks = instance.get_job_ticks(bad_origin.get_id())
            assert len(bad_ticks) == 1

            assert bad_ticks[0].status == JobTickStatus.FAILURE

            assert (
                "Error occurred during the execution of should_execute for schedule bad_should_execute_schedule"
                in bad_ticks[0].error.message
            )

            unloadable_ticks = instance.get_job_ticks(unloadable_origin.get_id())
            assert len(unloadable_ticks) == 0

            captured = capfd.readouterr()
            assert "Scheduler failed for doesnt_exist" in captured.out
            assert "doesnt_exist not found at module scope" in captured.out

        initial_datetime = initial_datetime.add(days=1)
        with pendulum.test(initial_datetime):
            new_now = pendulum.now("UTC")
            list(launch_scheduled_runs(instance, logger(), new_now))

            assert instance.get_runs_count() == 3
            wait_for_all_runs_to_start(instance)

            good_schedule_runs = instance.get_runs(
                filters=PipelineRunsFilter.for_schedule(good_schedule)
            )
            assert len(good_schedule_runs) == 2
            validate_run_started(
                good_schedule_runs[0],
                execution_time=new_now,
                partition_time=create_pendulum_time(2019, 2, 27),
            )

            good_ticks = instance.get_job_ticks(good_origin.get_id())
            assert len(good_ticks) == 2
            validate_tick(
                good_ticks[0],
                good_schedule,
                new_now,
                JobTickStatus.SUCCESS,
                [good_schedule_runs[0].run_id],
            )

            bad_schedule_runs = instance.get_runs(
                filters=PipelineRunsFilter.for_schedule(bad_schedule)
            )
            assert len(bad_schedule_runs) == 1
            validate_run_started(
                bad_schedule_runs[0],
                execution_time=new_now,
                partition_time=create_pendulum_time(2019, 2, 27),
            )

            bad_ticks = instance.get_job_ticks(bad_origin.get_id())
            assert len(bad_ticks) == 2
            validate_tick(
                bad_ticks[0],
                bad_schedule,
                new_now,
                JobTickStatus.SUCCESS,
                [bad_schedule_runs[0].run_id],
            )

            unloadable_ticks = instance.get_job_ticks(unloadable_origin.get_id())
            assert len(unloadable_ticks) == 0

            captured = capfd.readouterr()
            assert "Scheduler failed for doesnt_exist" in captured.out
            assert "doesnt_exist not found at module scope" in captured.out


@pytest.mark.parametrize("external_repo_context", repos())
def test_run_scheduled_on_time_boundary(external_repo_context):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("simple_schedule")

        schedule_origin = external_schedule.get_external_origin()
        initial_datetime = create_pendulum_time(
            year=2019,
            month=2,
            day=27,
            hour=0,
            minute=0,
            second=0,
        )
        with pendulum.test(initial_datetime):
            # Start schedule exactly at midnight
            instance.start_schedule_and_update_storage_state(external_schedule)

            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))

            assert instance.get_runs_count() == 1
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            assert ticks[0].status == JobTickStatus.SUCCESS


def test_bad_load(capfd):
    with schedule_instance() as instance:
        fake_origin = _get_unloadable_schedule_origin()
        initial_datetime = create_pendulum_time(
            year=2019,
            month=2,
            day=27,
            hour=23,
            minute=59,
            second=59,
        )
        with pendulum.test(initial_datetime):
            schedule_state = JobState(
                fake_origin,
                JobType.SCHEDULE,
                JobStatus.RUNNING,
                ScheduleJobData(
                    "0 0 * * *", pendulum.now("UTC").timestamp(), "DagsterDaemonScheduler"
                ),
            )
            instance.add_job_state(schedule_state)

        initial_datetime = initial_datetime.add(seconds=1)
        with pendulum.test(initial_datetime):
            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))

            assert instance.get_runs_count() == 0

            ticks = instance.get_job_ticks(fake_origin.get_id())

            assert len(ticks) == 0

            captured = capfd.readouterr()
            assert "Scheduler failed for doesnt_exist" in captured.out
            assert "doesnt_exist not found at module scope" in captured.out

        initial_datetime = initial_datetime.add(days=1)
        with pendulum.test(initial_datetime):
            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(fake_origin.get_id())
            assert len(ticks) == 0


@pytest.mark.parametrize("external_repo_context", repos())
def test_multiple_schedules_on_different_time_ranges(external_repo_context, capfd):
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("simple_schedule")
        external_hourly_schedule = external_repo.get_external_schedule("simple_hourly_schedule")
        initial_datetime = to_timezone(
            create_pendulum_time(
                year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"
            ),
            "US/Central",
        )
        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)
            instance.start_schedule_and_update_storage_state(external_hourly_schedule)

        initial_datetime = initial_datetime.add(seconds=2)
        with pendulum.test(initial_datetime):
            list(
                launch_scheduled_runs(
                    instance,
                    logger(),
                    pendulum.now("UTC"),
                )
            )

            assert instance.get_runs_count() == 2
            ticks = instance.get_job_ticks(external_schedule.get_external_origin_id())
            assert len(ticks) == 1
            assert ticks[0].status == JobTickStatus.SUCCESS

            hourly_ticks = instance.get_job_ticks(external_hourly_schedule.get_external_origin_id())
            assert len(hourly_ticks) == 1
            assert hourly_ticks[0].status == JobTickStatus.SUCCESS

            captured = capfd.readouterr()

            assert captured.out == """2019-02-27 18:00:01 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: simple_schedule, simple_hourly_schedule
2019-02-27 18:00:01 - SchedulerDaemon - INFO - Evaluating schedule `simple_schedule` at 2019-02-28 00:00:00+0000
2019-02-27 18:00:01 - SchedulerDaemon - INFO - Completed scheduled launch of run {first_run_id} for simple_schedule
2019-02-27 18:00:01 - SchedulerDaemon - INFO - Evaluating schedule `simple_hourly_schedule` at 2019-02-28 00:00:00+0000
2019-02-27 18:00:01 - SchedulerDaemon - INFO - Completed scheduled launch of run {second_run_id} for simple_hourly_schedule
""".format(
                first_run_id=instance.get_runs()[1].run_id,
                second_run_id=instance.get_runs()[0].run_id,
            )

        initial_datetime = initial_datetime.add(hours=1)
        with pendulum.test(initial_datetime):
            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))

            assert instance.get_runs_count() == 3

            ticks = instance.get_job_ticks(external_schedule.get_external_origin_id())
            assert len(ticks) == 1
            assert ticks[0].status == JobTickStatus.SUCCESS

            hourly_ticks = instance.get_job_ticks(external_hourly_schedule.get_external_origin_id())
            assert len(hourly_ticks) == 2
            assert len([tick for tick in hourly_ticks if tick.status == JobTickStatus.SUCCESS]) == 2

            captured = capfd.readouterr()
            assert (
                captured.out
                == """2019-02-27 19:00:01 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: simple_schedule, simple_hourly_schedule
2019-02-27 19:00:01 - SchedulerDaemon - INFO - No new runs for simple_schedule
2019-02-27 19:00:01 - SchedulerDaemon - INFO - Evaluating schedule `simple_hourly_schedule` at 2019-02-28 01:00:00+0000
2019-02-27 19:00:01 - SchedulerDaemon - INFO - Completed scheduled launch of run {third_run_id} for simple_hourly_schedule
""".format(
                    third_run_id=instance.get_runs()[0].run_id
                )
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_launch_failure(external_repo_context, capfd):
    with instance_with_schedules(
        external_repo_context,
        overrides={
            "run_launcher": {
                "module": "dagster.core.test_utils",
                "class": "ExplodingRunLauncher",
            },
        },
    ) as (instance, external_repo):
        external_schedule = external_repo.get_external_schedule("simple_schedule")

        schedule_origin = external_schedule.get_external_origin()
        initial_datetime = to_timezone(
            create_pendulum_time(year=2019, month=2, day=27, hour=0, minute=0, second=0, tz="UTC"),
            "US/Central",
        )

        with pendulum.test(initial_datetime):
            instance.start_schedule_and_update_storage_state(external_schedule)

            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))

            assert instance.get_runs_count() == 1

            run = instance.get_runs()[0]

            validate_run_started(
                run,
                execution_time=initial_datetime,
                partition_time=create_pendulum_time(2019, 2, 26),
                expected_success=False,
            )

            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_schedule,
                initial_datetime,
                JobTickStatus.SUCCESS,
                [run.run_id for run in instance.get_runs()],
            )

            captured = capfd.readouterr()
            assert (
                captured.out
                == """2019-02-26 18:00:00 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: simple_schedule
2019-02-26 18:00:00 - SchedulerDaemon - INFO - Evaluating schedule `simple_schedule` at 2019-02-27 00:00:00+0000
2019-02-26 18:00:00 - SchedulerDaemon - ERROR - Run {run_id} created successfully but failed to launch.
""".format(
                    run_id=instance.get_runs()[0].run_id
                )
            )


def test_partitionless_schedule(capfd):
    initial_datetime = create_pendulum_time(year=2019, month=2, day=27, tz="US/Central")
    with instance_with_schedules(default_repo) as (instance, external_repo):
        with pendulum.test(initial_datetime):
            external_schedule = external_repo.get_external_schedule("partitionless_schedule")
            schedule_origin = external_schedule.get_external_origin()
            instance.start_schedule_and_update_storage_state(external_schedule)

        # Travel enough in the future that many ticks have passed, but only one run executes
        initial_datetime = initial_datetime.add(days=5)
        with pendulum.test(initial_datetime):
            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))
            assert instance.get_runs_count() == 1

            wait_for_all_runs_to_start(instance)

            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                create_pendulum_time(year=2019, month=3, day=4, tz="US/Central"),
                JobTickStatus.SUCCESS,
                [run.run_id for run in instance.get_runs()],
            )

            validate_run_started(
                instance.get_runs()[0],
                execution_time=create_pendulum_time(year=2019, month=3, day=4, tz="US/Central"),
                partition_time=None,
            )

            captured = capfd.readouterr()

            assert (
                captured.out
                == """2019-03-04 00:00:00 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: partitionless_schedule
2019-03-04 00:00:00 - SchedulerDaemon - WARNING - partitionless_schedule has no partition set, so not trying to catch up
2019-03-04 00:00:00 - SchedulerDaemon - INFO - Evaluating schedule `partitionless_schedule` at 2019-03-04 00:00:00-0600
2019-03-04 00:00:00 - SchedulerDaemon - INFO - Completed scheduled launch of run {run_id} for partitionless_schedule
""".format(
                    run_id=instance.get_runs()[0].run_id
                )
            )


def test_max_catchup_runs(capfd):
    initial_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with instance_with_schedules(default_repo) as (instance, external_repo):
        with pendulum.test(initial_datetime):
            external_schedule = external_repo.get_external_schedule("simple_schedule")
            schedule_origin = external_schedule.get_external_origin()
            instance.start_schedule_and_update_storage_state(external_schedule)

        initial_datetime = initial_datetime.add(days=5)
        with pendulum.test(initial_datetime):
            # Day is now March 4 at 11:59PM
            list(
                launch_scheduled_runs(
                    instance,
                    logger(),
                    pendulum.now("UTC"),
                    max_catchup_runs=2,
                )
            )

            assert instance.get_runs_count() == 2
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 2

            first_datetime = create_pendulum_time(year=2019, month=3, day=4)

            wait_for_all_runs_to_start(instance)

            validate_tick(
                ticks[0],
                external_schedule,
                first_datetime,
                JobTickStatus.SUCCESS,
                [instance.get_runs()[0].run_id],
            )
            validate_run_started(
                instance.get_runs()[0],
                execution_time=first_datetime,
                partition_time=create_pendulum_time(2019, 3, 3),
            )

            second_datetime = create_pendulum_time(year=2019, month=3, day=3)

            validate_tick(
                ticks[1],
                external_schedule,
                second_datetime,
                JobTickStatus.SUCCESS,
                [instance.get_runs()[1].run_id],
            )

            validate_run_started(
                instance.get_runs()[1],
                execution_time=second_datetime,
                partition_time=create_pendulum_time(2019, 3, 2),
            )

            captured = capfd.readouterr()
            assert captured.out == """2019-03-04 17:59:59 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: simple_schedule
2019-03-04 17:59:59 - SchedulerDaemon - WARNING - simple_schedule has fallen behind, only launching 2 runs
2019-03-04 17:59:59 - SchedulerDaemon - INFO - Evaluating schedule `simple_schedule` at the following times: 2019-03-03 00:00:00+0000, 2019-03-04 00:00:00+0000
2019-03-04 17:59:59 - SchedulerDaemon - INFO - Completed scheduled launch of run {first_run_id} for simple_schedule
2019-03-04 17:59:59 - SchedulerDaemon - INFO - Completed scheduled launch of run {second_run_id} for simple_schedule
""".format(
                first_run_id=instance.get_runs()[1].run_id,
                second_run_id=instance.get_runs()[0].run_id,
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_multi_runs(external_repo_context, capfd):
    freeze_datetime = to_timezone(
        create_pendulum_time(
            year=2019,
            month=2,
            day=27,
            hour=23,
            minute=59,
            second=59,
            tz="UTC",
        ),
        "US/Central",
    )
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        with pendulum.test(freeze_datetime):
            external_schedule = external_repo.get_external_schedule("multi_run_schedule")
            schedule_origin = external_schedule.get_external_origin()
            instance.start_schedule_and_update_storage_state(external_schedule)

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

            # launch_scheduled_runs does nothing before the first tick
            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 0

            captured = capfd.readouterr()

            assert (
                captured.out
                == """2019-02-27 17:59:59 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: multi_run_schedule
2019-02-27 17:59:59 - SchedulerDaemon - INFO - No new runs for multi_run_schedule
"""
            )

        freeze_datetime = freeze_datetime.add(seconds=2)
        with pendulum.test(freeze_datetime):
            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))
            assert instance.get_runs_count() == 2
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 1

            expected_datetime = create_pendulum_time(year=2019, month=2, day=28)

            runs = instance.get_runs()
            validate_tick(
                ticks[0],
                external_schedule,
                expected_datetime,
                JobTickStatus.SUCCESS,
                [run.run_id for run in runs],
            )

            wait_for_all_runs_to_start(instance)
            runs = instance.get_runs()
            validate_run_started(runs[0], execution_time=create_pendulum_time(2019, 2, 28))
            validate_run_started(runs[1], execution_time=create_pendulum_time(2019, 2, 28))

            captured = capfd.readouterr()

            assert (
                captured.out
                == f"""2019-02-27 18:00:01 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: multi_run_schedule
2019-02-27 18:00:01 - SchedulerDaemon - INFO - Evaluating schedule `multi_run_schedule` at 2019-02-28 00:00:00+0000
2019-02-27 18:00:01 - SchedulerDaemon - INFO - Completed scheduled launch of run {runs[1].run_id} for multi_run_schedule
2019-02-27 18:00:01 - SchedulerDaemon - INFO - Completed scheduled launch of run {runs[0].run_id} for multi_run_schedule
"""
            )

            # Verify idempotence
            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))
            assert instance.get_runs_count() == 2
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 1
            assert ticks[0].status == JobTickStatus.SUCCESS

        freeze_datetime = freeze_datetime.add(days=1)
        with pendulum.test(freeze_datetime):
            capfd.readouterr()

            # Traveling one more day in the future before running results in a tick
            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))
            assert instance.get_runs_count() == 4
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 2
            assert len([tick for tick in ticks if tick.status == JobTickStatus.SUCCESS]) == 2
            runs = instance.get_runs()

            captured = capfd.readouterr()

            assert (
                captured.out
                == f"""2019-02-28 18:00:01 - SchedulerDaemon - INFO - Checking for new runs for the following schedules: multi_run_schedule
2019-02-28 18:00:01 - SchedulerDaemon - INFO - Evaluating schedule `multi_run_schedule` at 2019-03-01 00:00:00+0000
2019-02-28 18:00:01 - SchedulerDaemon - INFO - Completed scheduled launch of run {runs[1].run_id} for multi_run_schedule
2019-02-28 18:00:01 - SchedulerDaemon - INFO - Completed scheduled launch of run {runs[0].run_id} for multi_run_schedule
"""
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_multi_runs_missing_run_key(external_repo_context, capfd):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"), "US/Central"
    )
    with instance_with_schedules(external_repo_context) as (instance, external_repo):
        with pendulum.test(freeze_datetime):
            external_schedule = external_repo.get_external_schedule(
                "multi_run_schedule_with_missing_run_key"
            )
            schedule_origin = external_schedule.get_external_origin()
            instance.start_schedule_and_update_storage_state(external_schedule)

            list(launch_scheduled_runs(instance, logger(), pendulum.now("UTC")))
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_schedule,
                freeze_datetime,
                JobTickStatus.FAILURE,
                [],
                "Error occurred during the execution function for schedule "
                "multi_run_schedule_with_missing_run_key",
            )

            captured = capfd.readouterr()

            assert (
                "Failed to fetch schedule data for multi_run_schedule_with_missing_run_key: "
                in captured.out
            )

            assert (
                "Error occurred during the execution function for schedule "
                "multi_run_schedule_with_missing_run_key" in captured.out
            )

            assert (
                "Schedules that return multiple RunRequests must specify a "
                "run_key in each RunRequest" in captured.out
            )


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Cron doesn't work on windows")
def test_run_with_hanging_cron_schedules():
    # Verify that the system will prompt you to wipe your schedules with the SystemCronScheduler
    # before you can switch to DagsterDaemonScheduler

    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test_tempdir(
            temp_dir,
            overrides={"scheduler": {"module": "dagster_cron", "class": "SystemCronScheduler"}},
        ) as cron_instance:
            with default_repo() as external_repo:
                cron_instance.start_schedule_and_update_storage_state(
                    external_repo.get_external_schedule("simple_schedule")
                )

        # Can't change scheduler to DagsterDaemonScheduler, warns you to wipe
        with pytest.raises(DagsterScheduleWipeRequired):
            with instance_for_test_tempdir(
                temp_dir,
                overrides={
                    "scheduler": {
                        "module": "dagster.core.scheduler",
                        "class": "DagsterDaemonScheduler",
                    },
                },
            ):
                pass

        with instance_for_test_tempdir(
            temp_dir,
            overrides={
                "scheduler": {
                    "module": "dagster_cron",
                    "class": "SystemCronScheduler",
                },
            },
        ) as cron_instance:
            cron_instance.wipe_all_schedules()

        # After wiping, now can change the scheduler to DagsterDaemonScheduler
        with instance_for_test_tempdir(
            temp_dir,
            overrides={
                "scheduler": {
                    "module": "dagster.core.scheduler",
                    "class": "DagsterDaemonScheduler",
                },
            },
        ):
            pass
