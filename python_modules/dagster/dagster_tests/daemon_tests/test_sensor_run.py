import os
import random
import string
import sys
import threading
import time
from contextlib import contextmanager

import pendulum
import pytest
from dagster import Any, Field, pipeline, repository, solid
from dagster.cli.workspace.dynamic_workspace import DynamicWorkspace
from dagster.core.definitions.decorators.sensor import sensor
from dagster.core.definitions.job import JobType
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.definitions.sensor import RunRequest, SkipReason
from dagster.core.execution.api import execute_pipeline
from dagster.core.host_representation import (
    ExternalJobOrigin,
    ExternalRepositoryOrigin,
    InProcessRepositoryLocationOrigin,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
)
from dagster.core.host_representation.grpc_server_registry import ProcessGrpcServerRegistry
from dagster.core.scheduler.job import JobState, JobStatus, JobTickStatus
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import instance_for_test
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.daemon import get_default_daemon_logger
from dagster.daemon.controller import (
    DEFAULT_DAEMON_ERROR_INTERVAL_SECONDS,
    DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
)
from dagster.daemon.daemon import DAEMON_HEARTBEAT_ERROR_LIMIT, SensorDaemon
from dagster.daemon.sensor import execute_sensor_iteration, execute_sensor_iteration_loop
from dagster.seven import create_pendulum_time, to_timezone


@solid
def the_solid(_):
    return 1


@pipeline
def the_pipeline():
    the_solid()


@solid(config_schema=Field(Any))
def config_solid(_):
    return 1


@pipeline
def config_pipeline():
    config_solid()


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


@repository
def the_repo():
    return [
        the_pipeline,
        config_pipeline,
        large_sensor,
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
        with ProcessGrpcServerRegistry() as grpc_server_registry:
            with DynamicWorkspace(grpc_server_registry) as workspace:
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
                "Error in config for pipeline the_pipeline",
            )

            captured = capfd.readouterr()
            assert ("Error in config for pipeline the_pipeline") in captured.out

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
                "Error in config for pipeline the_pipeline",
            )

            captured = capfd.readouterr()
            assert ("Error in config for pipeline the_pipeline") in captured.out


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
            sensor_daemon = SensorDaemon.create_from_instance(instance)
            daemon_shutdown_event = threading.Event()
            sensor_daemon.run_loop(
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
