import os
import random
import string
import sys
import tempfile
import threading
import time
from contextlib import contextmanager

import pendulum
import pytest
from dagster import (
    Any,
    AssetKey,
    AssetMaterialization,
    Field,
    Output,
    graph,
    pipeline,
    pipeline_failure_sensor,
    repository,
    run_failure_sensor,
    solid,
)
from dagster.core.definitions.decorators.sensor import asset_sensor, sensor
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.definitions.run_request import JobType
from dagster.core.definitions.run_status_sensor_definition import run_status_sensor
from dagster.core.definitions.sensor_definition import (
    DEFAULT_SENSOR_DAEMON_INTERVAL,
    RunRequest,
    SkipReason,
)
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.events.log import EventLogEntry
from dagster.core.execution.api import execute_pipeline
from dagster.core.host_representation import (
    ExternalJobOrigin,
    ExternalRepositoryOrigin,
    InProcessRepositoryLocationOrigin,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
)
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler.job import JobState, JobStatus, JobTickStatus
from dagster.core.storage.event_log.base import EventRecordsFilter
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import create_test_daemon_workspace, instance_for_test
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.daemon import get_default_daemon_logger
from dagster.daemon.controller import (
    DEFAULT_DAEMON_ERROR_INTERVAL_SECONDS,
    DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
)
from dagster.daemon.daemon import DAEMON_HEARTBEAT_ERROR_LIMIT, SensorDaemon
from dagster.daemon.sensor import execute_sensor_iteration, execute_sensor_iteration_loop
from dagster.seven.compat.pendulum import create_pendulum_time, to_timezone


@solid
def the_solid(_):
    return 1


@pipeline
def the_pipeline():
    the_solid()


@graph()
def the_graph():
    the_solid()


the_job = the_graph.to_job()


@solid(config_schema=Field(Any))
def config_solid(_):
    return 1


@pipeline
def config_pipeline():
    config_solid()


@graph()
def config_graph():
    config_solid()


@solid
def foo_solid():
    yield AssetMaterialization(asset_key=AssetKey("foo"))
    yield Output(1)


@pipeline
def foo_pipeline():
    foo_solid()


@solid
def hanging_solid():
    start_time = time.time()
    while True:
        if time.time() - start_time > 10:
            return
        time.sleep(0.5)


@pipeline
def hanging_pipeline():
    hanging_solid()


@solid
def failure_solid():
    raise Exception("womp womp")


@pipeline
def failure_pipeline():
    failure_solid()


@graph()
def failure_graph():
    failure_solid()


failure_job = failure_graph.to_job()


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


@sensor(pipeline_name="the_pipeline")
def skip_cursor_sensor(context):
    if not context.cursor:
        cursor = 1
    else:
        cursor = int(context.cursor) + 1

    context.update_cursor(str(cursor))
    return SkipReason()


@sensor(pipeline_name="the_pipeline")
def run_cursor_sensor(context):
    if not context.cursor:
        cursor = 1
    else:
        cursor = int(context.cursor) + 1

    context.update_cursor(str(cursor))
    return RunRequest(run_key=None, run_config={}, tags={})


def _random_string(length):
    return "".join(random.choice(string.ascii_lowercase) for x in range(length))


@sensor(pipeline_name="config_pipeline")
def large_sensor(_context):
    # create a gRPC response payload larger than the limit (4194304)
    REQUEST_COUNT = 25
    REQUEST_TAG_COUNT = 5000
    REQUEST_CONFIG_COUNT = 100

    for _ in range(REQUEST_COUNT):
        tags_garbage = {_random_string(10): _random_string(20) for i in range(REQUEST_TAG_COUNT)}
        config_garbage = {
            _random_string(10): _random_string(20) for i in range(REQUEST_CONFIG_COUNT)
        }
        config = {"solids": {"config_solid": {"config": {"foo": config_garbage}}}}
        yield RunRequest(run_key=None, run_config=config, tags=tags_garbage)


@asset_sensor(pipeline_name="the_pipeline", asset_key=AssetKey("foo"))
def asset_foo_sensor(context, _event):
    return RunRequest(run_key=context.cursor, run_config={})


@asset_sensor(asset_key=AssetKey("foo"), job=the_job)
def asset_job_sensor(context, _event):
    return RunRequest(run_key=context.cursor, run_config={})


@pipeline_failure_sensor
def my_pipeline_failure_sensor(context):
    assert isinstance(context.instance, DagsterInstance)


@run_failure_sensor(job_selection=[failure_job])
def my_run_failure_sensor_filtered(context):
    assert isinstance(context.instance, DagsterInstance)


@run_status_sensor(pipeline_run_status=PipelineRunStatus.SUCCESS)
def my_pipeline_success_sensor(context):
    assert isinstance(context.instance, DagsterInstance)


config_job = config_graph.to_job()


@sensor(jobs=[the_job, config_job])
def two_job_sensor(context):
    counter = int(context.cursor) if context.cursor else 0
    if counter % 2 == 0:
        yield RunRequest(run_key=str(counter), job_name=the_job.name)
    else:
        yield RunRequest(
            run_key=str(counter),
            job_name=config_job.name,
            run_config={"solids": {"config_solid": {"config": {"foo": "blah"}}}},
        )
    context.update_cursor(str(counter + 1))


@sensor()
def bad_request_untargeted(_ctx):
    yield RunRequest(run_key=None, job_name="should_fail")


@sensor(job=the_job)
def bad_request_mismatch(_ctx):
    yield RunRequest(run_key=None, job_name="config_pipeline")


@sensor(jobs=[the_job, config_job])
def bad_request_unspecified(_ctx):
    yield RunRequest(run_key=None)


@repository
def the_repo():
    return [
        the_pipeline,
        the_job,
        config_pipeline,
        config_graph,
        foo_pipeline,
        large_sensor,
        simple_sensor,
        error_sensor,
        wrong_config_sensor,
        always_on_sensor,
        run_key_sensor,
        custom_interval_sensor,
        skip_cursor_sensor,
        run_cursor_sensor,
        asset_foo_sensor,
        asset_job_sensor,
        my_pipeline_failure_sensor,
        my_run_failure_sensor_filtered,
        my_pipeline_success_sensor,
        failure_pipeline,
        failure_job,
        hanging_pipeline,
        two_job_sensor,
        bad_request_untargeted,
        bad_request_mismatch,
        bad_request_unspecified,
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
        with create_test_daemon_workspace() as workspace:
            with external_repo_context() as external_repo:
                yield (instance, workspace, external_repo)


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
    ).create_test_location() as location:
        yield location.get_repository("the_repo")


def repos():
    return [default_repo]


def evaluate_sensors(instance, workspace):
    list(
        execute_sensor_iteration(
            instance,
            get_default_daemon_logger("SensorDaemon"),
            workspace,
        )
    )


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
    if expected_run_ids is not None:
        assert set(tick_data.run_ids) == set(expected_run_ids)
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


def wait_for_all_runs_to_finish(instance, timeout=10):
    start_time = time.time()
    FINISHED_STATES = [
        PipelineRunStatus.SUCCESS,
        PipelineRunStatus.FAILURE,
        PipelineRunStatus.CANCELED,
    ]
    while True:
        if time.time() - start_time > timeout:
            raise Exception("Timed out waiting for runs to start")
        time.sleep(0.5)

        not_finished_runs = [
            run for run in instance.get_runs() if run.status not in FINISHED_STATES
        ]

        if len(not_finished_runs) == 0:
            break


@pytest.mark.parametrize("external_repo_context", repos())
def test_simple_sensor(external_repo_context, capfd):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("simple_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            evaluate_sensors(instance, workspace)

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                JobTickStatus.SKIPPED,
            )

            captured = capfd.readouterr()
            assert (
                captured.out
                == """2019-02-27 17:59:59 - SensorDaemon - INFO - Checking for new runs for sensor: simple_sensor
2019-02-27 17:59:59 - SensorDaemon - INFO - Sensor returned false for simple_sensor, skipping
"""
            )

            freeze_datetime = freeze_datetime.add(seconds=30)

        with pendulum.test(freeze_datetime):
            evaluate_sensors(instance, workspace)
            wait_for_all_runs_to_start(instance)
            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            validate_run_started(run)
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 2

            expected_datetime = create_pendulum_time(
                year=2019, month=2, day=28, hour=0, minute=0, second=29
            )
            validate_tick(
                ticks[0],
                external_sensor,
                expected_datetime,
                JobTickStatus.SUCCESS,
                [run.run_id],
            )

            captured = capfd.readouterr()
            assert (
                captured.out
                == """2019-02-27 18:00:29 - SensorDaemon - INFO - Checking for new runs for sensor: simple_sensor
2019-02-27 18:00:29 - SensorDaemon - INFO - Launching run for simple_sensor
2019-02-27 18:00:29 - SensorDaemon - INFO - Completed launch of run {run_id} for simple_sensor
""".format(
                    run_id=run.run_id
                )
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_bad_load_sensor_repository(external_repo_context, capfd):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("simple_sensor")

            valid_origin = external_sensor.get_external_origin()

            # Swap out a new repository name
            invalid_repo_origin = ExternalJobOrigin(
                ExternalRepositoryOrigin(
                    valid_origin.external_repository_origin.repository_location_origin,
                    "invalid_repo_name",
                ),
                valid_origin.job_name,
            )

            instance.add_job_state(JobState(invalid_repo_origin, JobType.SENSOR, JobStatus.RUNNING))

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(invalid_repo_origin.get_id())
            assert len(ticks) == 0

            evaluate_sensors(instance, workspace)

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(invalid_repo_origin.get_id())
            assert len(ticks) == 0

            captured = capfd.readouterr()
            assert "Sensor daemon caught an error for sensor simple_sensor" in captured.out
            assert (
                "Could not find repository invalid_repo_name in location test_location to run sensor simple_sensor"
                in captured.out
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_bad_load_sensor(external_repo_context, capfd):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("simple_sensor")

            valid_origin = external_sensor.get_external_origin()

            # Swap out a new repository name
            invalid_repo_origin = ExternalJobOrigin(
                valid_origin.external_repository_origin,
                "invalid_sensor",
            )

            instance.add_job_state(JobState(invalid_repo_origin, JobType.SENSOR, JobStatus.RUNNING))

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(invalid_repo_origin.get_id())
            assert len(ticks) == 0

            evaluate_sensors(instance, workspace)

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(invalid_repo_origin.get_id())
            assert len(ticks) == 0

            captured = capfd.readouterr()
            assert "Sensor daemon caught an error for sensor invalid_sensor" in captured.out
            assert "Could not find sensor invalid_sensor in repository the_repo." in captured.out


@pytest.mark.parametrize("external_repo_context", repos())
def test_error_sensor(external_repo_context, capfd):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("error_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            evaluate_sensors(instance, workspace)

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
            assert (
                "Error occurred during the execution of evaluation_fn for sensor error_sensor"
            ) in captured.out


@pytest.mark.parametrize("external_repo_context", repos())
def test_wrong_config_sensor(external_repo_context, capfd):
    freeze_datetime = to_timezone(
        create_pendulum_time(
            year=2019,
            month=2,
            day=27,
            hour=23,
            minute=59,
            second=59,
        ),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("wrong_config_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            evaluate_sensors(instance, workspace)
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1

            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                JobTickStatus.FAILURE,
                [],
                "Error in config for pipeline",
            )

            captured = capfd.readouterr()
            assert ("Error in config for pipeline") in captured.out

            # Error repeats on subsequent ticks

            evaluate_sensors(instance, workspace)
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 2

            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                JobTickStatus.FAILURE,
                [],
                "Error in config for pipeline",
            )

            captured = capfd.readouterr()
            assert ("Error in config for pipeline") in captured.out


@pytest.mark.parametrize("external_repo_context", repos())
def test_launch_failure(external_repo_context, capfd):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, hour=23, minute=59, second=59, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(
        external_repo_context,
        overrides={
            "run_launcher": {
                "module": "dagster.core.test_utils",
                "class": "ExplodingRunLauncher",
            },
        },
    ) as (instance, workspace, external_repo):
        with pendulum.test(freeze_datetime):

            external_sensor = external_repo.get_external_sensor("always_on_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            evaluate_sensors(instance, workspace)

            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0], external_sensor, freeze_datetime, JobTickStatus.SUCCESS, [run.run_id]
            )

            captured = capfd.readouterr()
            assert (
                "Run {run_id} created successfully but failed to launch:".format(run_id=run.run_id)
            ) in captured.out

            assert "The entire purpose of this is to throw on launch" in captured.out


@pytest.mark.parametrize("external_repo_context", repos())
def test_launch_once(external_repo_context, capfd):
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
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):

            external_sensor = external_repo.get_external_sensor("run_key_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            evaluate_sensors(instance, workspace)
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
            evaluate_sensors(instance, workspace)
            assert instance.get_runs_count() == 1
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                JobTickStatus.SKIPPED,
            )
            captured = capfd.readouterr()
            assert (
                'Skipping 1 run for sensor run_key_sensor already completed with run keys: ["only_once"]'
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
            evaluate_sensors(instance, workspace)
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())

            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                JobTickStatus.SKIPPED,
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_custom_interval_sensor(external_repo_context):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=28, tz="UTC"), "US/Central"
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("custom_interval_sensor")
            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 0

            evaluate_sensors(instance, workspace)
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(ticks[0], external_sensor, freeze_datetime, JobTickStatus.SKIPPED)

            freeze_datetime = freeze_datetime.add(seconds=30)

        with pendulum.test(freeze_datetime):
            evaluate_sensors(instance, workspace)
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            # no additional tick created after 30 seconds
            assert len(ticks) == 1

            freeze_datetime = freeze_datetime.add(seconds=30)

        with pendulum.test(freeze_datetime):
            evaluate_sensors(instance, workspace)
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 2

            expected_datetime = create_pendulum_time(year=2019, month=2, day=28, hour=0, minute=1)
            validate_tick(ticks[0], external_sensor, expected_datetime, JobTickStatus.SKIPPED)


@pytest.mark.parametrize("external_repo_context", repos())
def test_custom_interval_sensor_with_offset(external_repo_context, monkeypatch):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=28, tz="UTC"), "US/Central"
    )

    sleeps = []

    def fake_sleep(s):
        sleeps.append(s)
        pendulum.set_test_now(pendulum.now().add(seconds=s))

    monkeypatch.setattr(time, "sleep", fake_sleep)

    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):

            # 60 second custom interval
            external_sensor = external_repo.get_external_sensor("custom_interval_sensor")

            instance.add_job_state(
                JobState(external_sensor.get_external_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )

            # create a tick
            evaluate_sensors(instance, workspace)
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1

            # calling for another iteration should not generate another tick because time has not
            # advanced
            evaluate_sensors(instance, workspace)
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1

            # call the sensor_iteration_loop, which should loop, and call the monkeypatched sleep
            # to advance 30 seconds
            list(
                execute_sensor_iteration_loop(
                    instance,
                    workspace,
                    get_default_daemon_logger("SensorDaemon"),
                    until=freeze_datetime.add(seconds=65).timestamp(),
                )
            )

            assert pendulum.now() == freeze_datetime.add(seconds=65)
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 2
            assert sum(sleeps) == 65


def _get_unloadable_sensor_origin():
    working_directory = os.path.dirname(__file__)
    recon_repo = ReconstructableRepository.for_file(__file__, "doesnt_exist", working_directory)
    return ExternalRepositoryOrigin(
        InProcessRepositoryLocationOrigin(recon_repo), "fake_repository"
    ).get_job_origin("doesnt_exist")


@pytest.mark.parametrize("external_repo_context", repos())
def test_error_sensor_daemon(external_repo_context, monkeypatch):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=28, tz="UTC"), "US/Central"
    )

    sleeps = []

    def fake_sleep(s):
        sleeps.append(s)
        pendulum.set_test_now(pendulum.now().add(seconds=s))

    monkeypatch.setattr(time, "sleep", fake_sleep)

    with instance_with_sensors(
        external_repo_context,
        overrides={
            "run_launcher": {
                "module": "dagster.core.test_utils",
                "class": "ExplodingRunLauncher",
            },
        },
    ) as (instance, workspace, _external_repo):

        @contextmanager
        def _gen_workspace(_instance):
            yield workspace

        with pendulum.test(freeze_datetime):
            instance.add_job_state(
                JobState(_get_unloadable_sensor_origin(), JobType.SENSOR, JobStatus.RUNNING)
            )
            sensor_daemon = SensorDaemon(interval_seconds=DEFAULT_SENSOR_DAEMON_INTERVAL)
            daemon_shutdown_event = threading.Event()
            sensor_daemon.run_loop(
                instance.get_ref(),
                "my_uuid",
                daemon_shutdown_event,
                _gen_workspace,
                heartbeat_interval_seconds=DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
                error_interval_seconds=DEFAULT_DAEMON_ERROR_INTERVAL_SECONDS,
                until=freeze_datetime.add(seconds=65),
            )

            heartbeats = instance.get_daemon_heartbeats()
            heartbeat = heartbeats["SENSOR"]
            assert heartbeat
            assert heartbeat.errors
            assert len(heartbeat.errors) == DAEMON_HEARTBEAT_ERROR_LIMIT


@pytest.mark.parametrize("external_repo_context", repos())
def test_sensor_start_stop(external_repo_context):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("always_on_sensor")
            external_origin_id = external_sensor.get_external_origin_id()
            instance.start_sensor(external_sensor)

            assert instance.get_runs_count() == 0
            ticks = instance.get_job_ticks(external_origin_id)
            assert len(ticks) == 0

            evaluate_sensors(instance, workspace)

            assert instance.get_runs_count() == 1
            run = instance.get_runs()[0]
            ticks = instance.get_job_ticks(external_origin_id)
            assert len(ticks) == 1
            validate_tick(
                ticks[0], external_sensor, freeze_datetime, JobTickStatus.SUCCESS, [run.run_id]
            )

            freeze_datetime = freeze_datetime.add(seconds=15)

        with pendulum.test(freeze_datetime):
            evaluate_sensors(instance, workspace)
            # no new ticks, no new runs, we are below the 30 second min interval
            assert instance.get_runs_count() == 1
            ticks = instance.get_job_ticks(external_origin_id)
            assert len(ticks) == 1

            # stop / start
            instance.stop_sensor(external_origin_id)
            instance.start_sensor(external_sensor)

            evaluate_sensors(instance, workspace)
            # no new ticks, no new runs, we are below the 30 second min interval
            assert instance.get_runs_count() == 1
            ticks = instance.get_job_ticks(external_origin_id)
            assert len(ticks) == 1

            freeze_datetime = freeze_datetime.add(seconds=16)

        with pendulum.test(freeze_datetime):
            evaluate_sensors(instance, workspace)
            # should have new tick, new run, we are after the 30 second min interval
            assert instance.get_runs_count() == 2
            ticks = instance.get_job_ticks(external_origin_id)
            assert len(ticks) == 2


@pytest.mark.parametrize("external_repo_context", repos())
def test_large_sensor(external_repo_context):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            external_sensor = external_repo.get_external_sensor("large_sensor")
            instance.start_sensor(external_sensor)
            evaluate_sensors(instance, workspace)
            ticks = instance.get_job_ticks(external_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                external_sensor,
                freeze_datetime,
                JobTickStatus.SUCCESS,
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_cursor_sensor(external_repo_context):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            skip_sensor = external_repo.get_external_sensor("skip_cursor_sensor")
            run_sensor = external_repo.get_external_sensor("run_cursor_sensor")
            instance.start_sensor(skip_sensor)
            instance.start_sensor(run_sensor)
            evaluate_sensors(instance, workspace)

            skip_ticks = instance.get_job_ticks(skip_sensor.get_external_origin_id())
            assert len(skip_ticks) == 1
            validate_tick(
                skip_ticks[0],
                skip_sensor,
                freeze_datetime,
                JobTickStatus.SKIPPED,
            )
            assert skip_ticks[0].cursor == "1"

            run_ticks = instance.get_job_ticks(run_sensor.get_external_origin_id())
            assert len(run_ticks) == 1
            validate_tick(
                run_ticks[0],
                run_sensor,
                freeze_datetime,
                JobTickStatus.SUCCESS,
            )
            assert run_ticks[0].cursor == "1"

        freeze_datetime = freeze_datetime.add(seconds=60)
        with pendulum.test(freeze_datetime):
            evaluate_sensors(instance, workspace)

            skip_ticks = instance.get_job_ticks(skip_sensor.get_external_origin_id())
            assert len(skip_ticks) == 2
            validate_tick(
                skip_ticks[0],
                skip_sensor,
                freeze_datetime,
                JobTickStatus.SKIPPED,
            )
            assert skip_ticks[0].cursor == "2"

            run_ticks = instance.get_job_ticks(run_sensor.get_external_origin_id())
            assert len(run_ticks) == 2
            validate_tick(
                run_ticks[0],
                run_sensor,
                freeze_datetime,
                JobTickStatus.SUCCESS,
            )
            assert run_ticks[0].cursor == "2"


@pytest.mark.parametrize("external_repo_context", repos())
def test_asset_sensor(external_repo_context):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            foo_sensor = external_repo.get_external_sensor("asset_foo_sensor")
            instance.start_sensor(foo_sensor)

            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(foo_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                foo_sensor,
                freeze_datetime,
                JobTickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)
        with pendulum.test(freeze_datetime):

            # should generate the foo asset
            execute_pipeline(foo_pipeline, instance=instance)

            # should fire the asset sensor
            evaluate_sensors(instance, workspace)
            ticks = instance.get_job_ticks(foo_sensor.get_external_origin_id())
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                foo_sensor,
                freeze_datetime,
                JobTickStatus.SUCCESS,
            )
            run = instance.get_runs()[0]
            assert run.run_config == {}
            assert run.tags
            assert run.tags.get("dagster/sensor_name") == "asset_foo_sensor"


@pytest.mark.parametrize("external_repo_context", repos())
def test_asset_job_sensor(external_repo_context):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            job_sensor = external_repo.get_external_sensor("asset_job_sensor")
            instance.start_sensor(job_sensor)

            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(job_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                job_sensor,
                freeze_datetime,
                JobTickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)
        with pendulum.test(freeze_datetime):

            # should generate the foo asset
            execute_pipeline(foo_pipeline, instance=instance)

            # should fire the asset sensor
            evaluate_sensors(instance, workspace)
            ticks = instance.get_job_ticks(job_sensor.get_external_origin_id())
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                job_sensor,
                freeze_datetime,
                JobTickStatus.SUCCESS,
            )
            run = instance.get_runs()[0]
            assert run.run_config == {}
            assert run.tags
            assert run.tags.get("dagster/sensor_name") == "asset_job_sensor"


@pytest.mark.parametrize("external_repo_context", repos())
def test_pipeline_failure_sensor(external_repo_context):
    freeze_datetime = pendulum.now()
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            failure_sensor = external_repo.get_external_sensor("my_pipeline_failure_sensor")
            instance.start_sensor(failure_sensor)

            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(failure_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                failure_sensor,
                freeze_datetime,
                JobTickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)
            time.sleep(1)

        with pendulum.test(freeze_datetime):
            external_pipeline = external_repo.get_full_external_pipeline("failure_pipeline")
            run = instance.create_run_for_pipeline(
                failure_pipeline,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )
            instance.submit_run(run.run_id, workspace)
            wait_for_all_runs_to_finish(instance)
            run = instance.get_runs()[0]
            assert run.status == PipelineRunStatus.FAILURE
            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            # should fire the failure sensor
            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(failure_sensor.get_external_origin_id())
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                failure_sensor,
                freeze_datetime,
                JobTickStatus.SUCCESS,
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_run_failure_sensor_filtered(external_repo_context):
    freeze_datetime = pendulum.now()
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            failure_sensor = external_repo.get_external_sensor("my_run_failure_sensor_filtered")
            instance.start_sensor(failure_sensor)

            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(failure_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                failure_sensor,
                freeze_datetime,
                JobTickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)
            time.sleep(1)

        with pendulum.test(freeze_datetime):
            external_pipeline = external_repo.get_full_external_pipeline("failure_pipeline")
            run = instance.create_run_for_pipeline(
                failure_pipeline,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )
            instance.submit_run(run.run_id, workspace)
            wait_for_all_runs_to_finish(instance)
            run = instance.get_runs()[0]
            assert run.status == PipelineRunStatus.FAILURE
            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            # should not fire the failure sensor (filtered to failure job)
            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(failure_sensor.get_external_origin_id())
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                failure_sensor,
                freeze_datetime,
                JobTickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)
            time.sleep(1)

        with pendulum.test(freeze_datetime):
            external_pipeline = external_repo.get_full_external_pipeline("failure_graph")
            run = instance.create_run_for_pipeline(
                failure_job,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )
            instance.submit_run(run.run_id, workspace)
            wait_for_all_runs_to_finish(instance)
            run = instance.get_runs()[0]
            assert run.status == PipelineRunStatus.FAILURE

            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            # should not fire the failure sensor (filtered to failure job)
            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(failure_sensor.get_external_origin_id())
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                failure_sensor,
                freeze_datetime,
                JobTickStatus.SUCCESS,
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_run_status_sensor(external_repo_context):
    freeze_datetime = pendulum.now()
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            success_sensor = external_repo.get_external_sensor("my_pipeline_success_sensor")
            instance.start_sensor(success_sensor)

            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(success_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                success_sensor,
                freeze_datetime,
                JobTickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)
            time.sleep(1)

        with pendulum.test(freeze_datetime):
            external_pipeline = external_repo.get_full_external_pipeline("failure_pipeline")
            run = instance.create_run_for_pipeline(
                failure_pipeline,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )
            instance.submit_run(run.run_id, workspace)
            wait_for_all_runs_to_finish(instance)
            run = instance.get_runs()[0]
            assert run.status == PipelineRunStatus.FAILURE
            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            # should not fire the success sensor
            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(success_sensor.get_external_origin_id())
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                success_sensor,
                freeze_datetime,
                JobTickStatus.SKIPPED,
            )

        with pendulum.test(freeze_datetime):
            external_pipeline = external_repo.get_full_external_pipeline("foo_pipeline")
            run = instance.create_run_for_pipeline(
                foo_pipeline,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )
            instance.submit_run(run.run_id, workspace)
            wait_for_all_runs_to_finish(instance)
            run = instance.get_runs()[0]
            assert run.status == PipelineRunStatus.SUCCESS
            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            # should fire the success sensor
            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(success_sensor.get_external_origin_id())
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                success_sensor,
                freeze_datetime,
                JobTickStatus.SUCCESS,
            )


def sqlite_storage_config_fn(temp_dir):
    # non-run sharded storage
    return {
        "run_storage": {
            "module": "dagster.core.storage.runs",
            "class": "SqliteRunStorage",
            "config": {"base_dir": temp_dir},
        },
        "event_log_storage": {
            "module": "dagster.core.storage.event_log",
            "class": "SqliteEventLogStorage",
            "config": {"base_dir": temp_dir},
        },
    }


def default_storage_config_fn(_):
    # run sharded storage
    return {}


def sql_event_log_storage_config_fn(temp_dir):
    return {
        "event_log_storage": {
            "module": "dagster.core.storage.event_log",
            "class": "ConsolidatedSqliteEventLogStorage",
            "config": {"base_dir": temp_dir},
        },
    }


@pytest.mark.parametrize("external_repo_context", repos())
@pytest.mark.parametrize(
    "storage_config_fn",
    [default_storage_config_fn, sqlite_storage_config_fn],
)
def test_run_status_sensor_interleave(external_repo_context, storage_config_fn):
    freeze_datetime = pendulum.now()
    with tempfile.TemporaryDirectory() as temp_dir:

        with instance_with_sensors(
            external_repo_context, overrides=storage_config_fn(temp_dir)
        ) as (
            instance,
            workspace,
            external_repo,
        ):
            # start sensor
            with pendulum.test(freeze_datetime):
                failure_sensor = external_repo.get_external_sensor("my_pipeline_failure_sensor")
                instance.start_sensor(failure_sensor)

                evaluate_sensors(instance, workspace)

                ticks = instance.get_job_ticks(failure_sensor.get_external_origin_id())
                assert len(ticks) == 1
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    JobTickStatus.SKIPPED,
                )

                freeze_datetime = freeze_datetime.add(seconds=60)
                time.sleep(1)

            with pendulum.test(freeze_datetime):
                external_pipeline = external_repo.get_full_external_pipeline("hanging_pipeline")
                # start run 1
                run1 = instance.create_run_for_pipeline(
                    hanging_pipeline,
                    external_pipeline_origin=external_pipeline.get_external_origin(),
                    pipeline_code_origin=external_pipeline.get_python_origin(),
                )
                instance.submit_run(run1.run_id, workspace)
                freeze_datetime = freeze_datetime.add(seconds=60)
                # start run 2
                run2 = instance.create_run_for_pipeline(
                    hanging_pipeline,
                    external_pipeline_origin=external_pipeline.get_external_origin(),
                    pipeline_code_origin=external_pipeline.get_python_origin(),
                )
                instance.submit_run(run2.run_id, workspace)
                freeze_datetime = freeze_datetime.add(seconds=60)
                # fail run 2
                instance.report_run_failed(run2)
                freeze_datetime = freeze_datetime.add(seconds=60)
                run = instance.get_runs()[0]
                assert run.status == PipelineRunStatus.FAILURE
                assert run.run_id == run2.run_id

            # check sensor
            with pendulum.test(freeze_datetime):

                # should fire for run 2
                evaluate_sensors(instance, workspace)

                ticks = instance.get_job_ticks(failure_sensor.get_external_origin_id())
                assert len(ticks) == 2
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    JobTickStatus.SUCCESS,
                )
                assert len(ticks[0].origin_run_ids) == 1
                assert ticks[0].origin_run_ids[0] == run2.run_id

            # fail run 1
            with pendulum.test(freeze_datetime):
                # fail run 2
                instance.report_run_failed(run1)
                freeze_datetime = freeze_datetime.add(seconds=60)
                time.sleep(1)

            # check sensor
            with pendulum.test(freeze_datetime):

                # should fire for run 1
                evaluate_sensors(instance, workspace)

                ticks = instance.get_job_ticks(failure_sensor.get_external_origin_id())
                assert len(ticks) == 3
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    JobTickStatus.SUCCESS,
                )
                assert len(ticks[0].origin_run_ids) == 1
                assert ticks[0].origin_run_ids[0] == run1.run_id


@pytest.mark.parametrize("external_repo_context", repos())
@pytest.mark.parametrize("storage_config_fn", [sql_event_log_storage_config_fn])
def test_pipeline_failure_sensor_empty_run_records(external_repo_context, storage_config_fn):
    freeze_datetime = pendulum.now()
    with tempfile.TemporaryDirectory() as temp_dir:

        with instance_with_sensors(
            external_repo_context, overrides=storage_config_fn(temp_dir)
        ) as (
            instance,
            workspace,
            external_repo,
        ):

            with pendulum.test(freeze_datetime):
                failure_sensor = external_repo.get_external_sensor("my_pipeline_failure_sensor")
                instance.start_sensor(failure_sensor)

                evaluate_sensors(instance, workspace)

                ticks = instance.get_job_ticks(failure_sensor.get_external_origin_id())
                assert len(ticks) == 1
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    JobTickStatus.SKIPPED,
                )

                freeze_datetime = freeze_datetime.add(seconds=60)
                time.sleep(1)

            with pendulum.test(freeze_datetime):
                # create a mismatch between event storage and run storage
                instance.event_log_storage.store_event(
                    EventLogEntry(
                        None,
                        "fake failure event",
                        "debug",
                        "",
                        "fake_run_id",
                        time.time(),
                        dagster_event=DagsterEvent(
                            DagsterEventType.PIPELINE_FAILURE.value,
                            "foo",
                        ),
                    )
                )
                runs = instance.get_runs()
                assert len(runs) == 0
                failure_events = instance.get_event_records(
                    EventRecordsFilter(event_type=DagsterEventType.PIPELINE_FAILURE)
                )
                assert len(failure_events) == 1
                freeze_datetime = freeze_datetime.add(seconds=60)

            with pendulum.test(freeze_datetime):
                # shouldn't fire the failure sensor due to the mismatch
                evaluate_sensors(instance, workspace)

                ticks = instance.get_job_ticks(failure_sensor.get_external_origin_id())
                assert len(ticks) == 2
                validate_tick(
                    ticks[0],
                    failure_sensor,
                    freeze_datetime,
                    JobTickStatus.SKIPPED,
                )


@pytest.mark.parametrize("external_repo_context", repos())
def test_multi_job_sensor(external_repo_context):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            job_sensor = external_repo.get_external_sensor("two_job_sensor")
            instance.start_sensor(job_sensor)

            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(job_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                job_sensor,
                freeze_datetime,
                JobTickStatus.SUCCESS,
            )

            run = instance.get_runs()[0]
            assert run.run_config == {}
            assert run.tags.get("dagster/sensor_name") == "two_job_sensor"
            assert run.pipeline_name == "the_graph"

            freeze_datetime = freeze_datetime.add(seconds=60)
        with pendulum.test(freeze_datetime):

            # should fire the asset sensor
            evaluate_sensors(instance, workspace)
            ticks = instance.get_job_ticks(job_sensor.get_external_origin_id())
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                job_sensor,
                freeze_datetime,
                JobTickStatus.SUCCESS,
            )
            run = instance.get_runs()[0]
            assert run.run_config == {"solids": {"config_solid": {"config": {"foo": "blah"}}}}
            assert run.tags
            assert run.tags.get("dagster/sensor_name") == "two_job_sensor"
            assert run.pipeline_name == "config_graph"


@pytest.mark.parametrize("external_repo_context", repos())
def test_bad_run_request_untargeted(external_repo_context):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            job_sensor = external_repo.get_external_sensor("bad_request_untargeted")
            instance.start_sensor(job_sensor)

            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(job_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                job_sensor,
                freeze_datetime,
                JobTickStatus.FAILURE,
                None,
                (
                    "Error in sensor bad_request_untargeted: Sensor evaluation function returned a "
                    "RunRequest for a sensor without a specified target."
                ),
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_bad_run_request_mismatch(external_repo_context):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            job_sensor = external_repo.get_external_sensor("bad_request_mismatch")
            instance.start_sensor(job_sensor)

            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(job_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                job_sensor,
                freeze_datetime,
                JobTickStatus.FAILURE,
                None,
                (
                    "Error in sensor bad_request_mismatch: Sensor returned a RunRequest with "
                    "job_name config_pipeline. Expected one of: ['the_graph']"
                ),
            )


@pytest.mark.parametrize("external_repo_context", repos())
def test_bad_run_request_unspecified(external_repo_context):
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(external_repo_context) as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            job_sensor = external_repo.get_external_sensor("bad_request_unspecified")
            instance.start_sensor(job_sensor)

            evaluate_sensors(instance, workspace)

            ticks = instance.get_job_ticks(job_sensor.get_external_origin_id())
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                job_sensor,
                freeze_datetime,
                JobTickStatus.FAILURE,
                None,
                (
                    "Error in sensor bad_request_unspecified: Sensor returned a RunRequest that "
                    "did not specify job_name for the requested run. Expected one of: "
                    "['the_graph', 'config_graph']"
                ),
            )
