import os
import sys
import time
from contextlib import contextmanager

import pendulum
import pytest
from dagster import pipeline, repository, solid
from dagster.core.definitions.decorators.sensor import sensor
from dagster.core.definitions.job import JobType
from dagster.core.definitions.sensor import RunRequest, SkipReason
from dagster.core.execution.api import execute_pipeline
from dagster.core.host_representation import (
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    RepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.scheduler.job import JobState, JobStatus, JobTickStatus
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import instance_for_test
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.daemon import get_default_daemon_logger
from dagster.scheduler.sensor import execute_sensor_iteration


@solid
def the_solid(_):
    return 1


@pipeline
def the_pipeline():
    the_solid()


@sensor(pipeline_name="the_pipeline")
def simple_sensor(context):
    if not context.last_completion_time or not int(context.last_completion_time) % 2:
        return SkipReason()

    return RunRequest(run_key=None, run_config={}, tags={})


@sensor(pipeline_name="the_pipeline")
def always_on_sensor(_context):
    return RunRequest(run_key=None, run_config={}, tags={})


@sensor(pipeline_name="the_pipeline")
def run_key_sensor(_context):
    return RunRequest(run_key="only_once", run_config={}, tags={})


@sensor(pipeline_name="the_pipeline")
def error_sensor(context):
    raise Exception("womp womp")


@sensor(pipeline_name="the_pipeline")
def wrong_config_sensor(_context):
    return RunRequest(run_key="bad_config_key", run_config={"bad_key": "bad_val"}, tags={})


@sensor(pipeline_name="the_pipeline", minimum_interval_seconds=60)
def custom_interval_sensor(_context):
    return SkipReason()


@repository
def the_repo():
    return [
        the_pipeline,
        simple_sensor,
        error_sensor,
        wrong_config_sensor,
        always_on_sensor,
        run_key_sensor,
        custom_interval_sensor,
    ]


@pipeline
def the_other_pipeline():
    the_solid()


@repository
def the_other_repo():
    return [
        the_other_pipeline,
    ]


@contextmanager
def instance_with_sensors(external_repo_context, overrides=None):
    with instance_for_test(overrides) as instance:
        with external_repo_context() as external_repo:
            yield (instance, external_repo)


@contextmanager
def default_repo():
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable, python_file=__file__, working_directory=os.getcwd(),
    )

    with RepositoryLocationHandle.create_from_repository_location_origin(
        ManagedGrpcPythonEnvRepositoryLocationOrigin(
            loadable_target_origin=loadable_target_origin, location_name="test_location",
        )
    ) as handle:
        yield RepositoryLocation.from_handle(handle).get_repository("the_repo")


def repos():
    return [default_repo]


def validate_tick(
    tick,
    external_sensor,
    expected_datetime,
    expected_status,
    expected_run_ids=None,
    expected_error=None,
):
    tick_data = tick.job_tick_data
    assert tick_data.job_origin_id == external_sensor.get_external_origin_id()
    assert tick_data.job_name == external_sensor.name
    assert tick_data.job_type == JobType.SENSOR
    assert tick_data.status == expected_status
    assert tick_data.timestamp == expected_datetime.timestamp()
    assert set(tick_data.run_ids) == set(expected_run_ids if expected_run_ids else [])
    if expected_error:
        assert expected_error in tick_data.error.message


def validate_run_started(run, expected_success=True):
    if expected_success:
        assert (
            run.status == PipelineRunStatus.STARTED
            or run.status == PipelineRunStatus.SUCCESS
            or run.status == PipelineRunStatus.STARTING
        )
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
def test_simple_sensor(external_repo_context, capfd):
    freeze_datetime = pendulum.datetime(
        year=2019, month=2, day=27, hour=23, minute=59, second=59,
    ).in_tz("US/Central")
    with instance_with_sensors(external_repo_context) as (instance, external_repo):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("simple_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            list(execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon")))

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0], external_sensor, freeze_datetime, JobTickStatus.SKIPPED,
            )

            captured = capfd.readouterr()
            assert (
                captured.out
                == """2019-02-27 17:59:59 - SensorDaemon - INFO - Checking for new runs for the following sensors: simple_sensor
2019-02-27 17:59:59 - SensorDaemon - INFO - Sensor returned false for simple_sensor, skipping
"""
            )

            freeze_datetime = freeze_datetime.add(seconds=30)

        with pendulum.test(freeze_datetime):
            list(execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon")))
            wait_for_all_runs_to_start(instance)
            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            validate_run_started(run)
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 2

            expected_datetime = pendulum.datetime(
                year=2019, month=2, day=28, hour=0, minute=0, second=29
            )
            validate_tick(
                ticks[0], external_sensor, expected_datetime, JobTickStatus.SUCCESS, [run.run_id],
            )

            captured = capfd.readouterr()
            assert (
                captured.out
                == """2019-02-27 18:00:29 - SensorDaemon - INFO - Checking for new runs for the following sensors: simple_sensor
2019-02-27 18:00:29 - SensorDaemon - INFO - Launching run for simple_sensor
2019-02-27 18:00:29 - SensorDaemon - INFO - Completed launch of run {run_id} for simple_sensor
""".format(
                    run_id=run.run_id
                )
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_error_sensor(external_repo_context, capfd):
    freeze_datetime = pendulum.datetime(
        year=2019, month=2, day=27, hour=23, minute=59, second=59,
    ).in_tz("US/Central")
    with instance_with_sensors(external_repo_context) as (instance, external_repo):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("error_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            list(execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon")))

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                JobTickStatus.FAILURE,
                [],
                "Error occurred during the execution of evaluation_fn for sensor error_sensor",
            )

            captured = capfd.readouterr()
            assert ("Failed to resolve sensor for error_sensor : ") in captured.out

            assert (
                "Error occurred during the execution of evaluation_fn for sensor error_sensor"
            ) in captured.out


@pytest.mark.parametrize("external_repo_context", repos())
def test_wrong_config_sensor(external_repo_context, capfd):
    freeze_datetime = pendulum.datetime(
        year=2019, month=2, day=27, hour=23, minute=59, second=59,
    ).in_tz("US/Central")
    with instance_with_sensors(external_repo_context) as (instance, external_repo):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("wrong_config_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            list(execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon")))
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                JobTickStatus.FAILURE,
                [],
                "Error in config for pipeline the_pipeline",
            )

            captured = capfd.readouterr()
            assert ("Error in config for pipeline the_pipeline") in captured.out

            # Error repeats on subsequent ticks

            list(execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon")))
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 2

            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                JobTickStatus.FAILURE,
                [],
                "Error in config for pipeline the_pipeline",
            )

            captured = capfd.readouterr()
            assert ("Error in config for pipeline the_pipeline") in captured.out


@pytest.mark.parametrize("external_repo_context", repos())
def test_launch_failure(external_repo_context, capfd):
    freeze_datetime = pendulum.datetime(
        year=2019, month=2, day=27, hour=23, minute=59, second=59,
    ).in_tz("US/Central")
    with instance_with_sensors(
        external_repo_context,
        overrides={
            "run_launcher": {"module": "dagster.core.test_utils", "class": "ExplodingRunLauncher",},
        },
    ) as (instance, external_repo):
        with pendulum.test(freeze_datetime):

            external_sensor = external_repo.get_external_sensor("always_on_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            list(execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon")))

            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0], external_sensor, freeze_datetime, JobTickStatus.SUCCESS, [run.run_id]
            )

            captured = capfd.readouterr()
            assert (
                "Run {run_id} created successfully but failed to launch.".format(run_id=run.run_id)
            ) in captured.out


@pytest.mark.parametrize("external_repo_context", repos())
def test_launch_once(external_repo_context, capfd):
    freeze_datetime = pendulum.datetime(
        year=2019, month=2, day=27, hour=23, minute=59, second=59,
    ).in_tz("US/Central")
    with instance_with_sensors(external_repo_context) as (instance, external_repo):
        with pendulum.test(freeze_datetime):

            external_sensor = external_repo.get_external_sensor("run_key_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            list(execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon")))
            wait_for_all_runs_to_start(instance)

            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                JobTickStatus.SUCCESS,
                expected_run_ids=[run.run_id],
            )

        # run again (after 30 seconds), to ensure that the run key maintains idempotence
        freeze_datetime = freeze_datetime.add(seconds=30)
        with pendulum.test(freeze_datetime):
            list(execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon")))
            assert instance.get_runs_count() == 1
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 2
            validate_tick(
                ticks[0], external_sensor, freeze_datetime, JobTickStatus.SKIPPED,
            )
            captured = capfd.readouterr()
            assert (
                f"Run {run.run_id} already completed with the run key `only_once` for run_key_sensor"
                in captured.out
            )

            launched_run = instance.get_runs()[0]

            # Manually create a new run with the same tags
            execute_pipeline(
                the_pipeline,
                run_config=launched_run.run_config,
                tags=launched_run.tags,
                instance=instance,
            )

            # Sensor loop still executes
        freeze_datetime = freeze_datetime.add(seconds=30)
        with pendulum.test(freeze_datetime):
            list(execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon")))
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())

            assert len(ticks) == 3
            validate_tick(
                ticks[0], external_sensor, freeze_datetime, JobTickStatus.SKIPPED,
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_custom_interval_sensor(external_repo_context):
    freeze_datetime = pendulum.datetime(year=2019, month=2, day=28).in_tz("US/Central")
    with instance_with_sensors(external_repo_context) as (instance, external_repo):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("custom_interval_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            list(execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon")))
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(ticks[0], external_sensor, freeze_datetime, JobTickStatus.SKIPPED)

            freeze_datetime = freeze_datetime.add(seconds=30)

        with pendulum.test(freeze_datetime):
            list(execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon")))
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            # no additional tick created after 30 seconds
            assert len(ticks) == 1

            freeze_datetime = freeze_datetime.add(seconds=30)

        with pendulum.test(freeze_datetime):
            list(execute_sensor_iteration(instance, get_default_daemon_logger("SensorDaemon")))
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 2

            expected_datetime = pendulum.datetime(year=2019, month=2, day=28, hour=0, minute=1)
            validate_tick(ticks[0], external_sensor, expected_datetime, JobTickStatus.SKIPPED)
