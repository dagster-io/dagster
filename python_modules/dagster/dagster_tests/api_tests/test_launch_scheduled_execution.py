import json
import os
import sys
from contextlib import contextmanager

import pytest
from dagster import daily_schedule, pipeline, repository, solid
from dagster.api.launch_scheduled_execution import sync_launch_scheduled_execution
from dagster.core.host_representation import (
    ExternalRepositoryOrigin,
    ExternalScheduleOrigin,
    GrpcServerRepositoryLocationOrigin,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
)
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler import (
    ScheduleTickStatus,
    ScheduledExecutionFailed,
    ScheduledExecutionSkipped,
    ScheduledExecutionSuccess,
)
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.telemetry import get_dir_from_dagster_home
from dagster.core.test_utils import instance_for_test, today_at_midnight
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.server import GrpcServerProcess
from dagster.utils import find_free_port

_COUPLE_DAYS_AGO = today_at_midnight().subtract(days=2)


def _throw(_context):
    raise Exception("bananas")


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
    return {"solids": {"the_solid": {"config": {"work_amt": "a lot"}}}}


@daily_schedule(pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO)
def bad_env_fn_schedule():  # forgot context arg
    return {}


@daily_schedule(
    pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO, should_execute=_throw,
)
def bad_should_execute_schedule(_context):
    return {}


@daily_schedule(
    pipeline_name="the_pipeline", start_date=_COUPLE_DAYS_AGO, should_execute=_never,
)
def skip_schedule(_context):
    return {}


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
        bad_env_fn_schedule,
        bad_should_execute_schedule,
        skip_schedule,
        wrong_config_schedule,
    ]


def _default_instance():
    return instance_for_test(
        overrides={
            "run_launcher": {"module": "dagster.core.test_utils", "class": "MockedRunLauncher",}
        },
    )


@contextmanager
def python_schedule_origin(schedule_name):

    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable, python_file=__file__, attribute="the_repo"
    )

    repo_origin = ExternalRepositoryOrigin(
        ManagedGrpcPythonEnvRepositoryLocationOrigin(loadable_target_origin=loadable_target_origin),
        "the_repo",
    )

    yield repo_origin.get_schedule_origin(schedule_name)


@contextmanager
def grpc_schedule_origin(schedule_name):
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable, python_file=__file__, attribute="the_repo"
    )
    server_process = GrpcServerProcess(loadable_target_origin=loadable_target_origin)
    with server_process.create_ephemeral_client() as api_client:
        repo_origin = ExternalRepositoryOrigin(
            GrpcServerRepositoryLocationOrigin(
                host=api_client.host, port=api_client.port, socket=api_client.socket,
            ),
            repository_name="the_repo",
        )

        yield repo_origin.get_schedule_origin(schedule_name)
    server_process.wait()


@pytest.mark.parametrize(
    "schedule_origin_context", [python_schedule_origin, grpc_schedule_origin,],
)
def test_launch_successful_execution(schedule_origin_context):
    with _default_instance() as instance:
        with schedule_origin_context("simple_schedule") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)
            assert isinstance(result, ScheduledExecutionSuccess)

            run = instance.get_run_by_id(result.run_id)
            assert run is not None

            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert ticks[0].status == ScheduleTickStatus.SUCCESS


@pytest.mark.parametrize(
    "schedule_origin_context", [python_schedule_origin],
)
def test_launch_successful_execution_telemetry(schedule_origin_context):
    with _default_instance():
        with schedule_origin_context("simple_schedule") as schedule_origin:
            sync_launch_scheduled_execution(schedule_origin)

            event_log_path = "{logs_dir}/event.log".format(
                logs_dir=get_dir_from_dagster_home("logs")
            )
            with open(event_log_path, "r") as f:
                event_log = f.readlines()
                assert len(event_log) == 2

                message_start = json.loads(event_log[0])
                message_end = json.loads(event_log[1])

                assert message_start.get("action") == "_launch_scheduled_execution_started"
                assert message_end.get("action") == "_launch_scheduled_execution_ended"


@pytest.mark.parametrize("schedule_origin_context", [python_schedule_origin, grpc_schedule_origin])
def test_bad_env_fn(schedule_origin_context):
    with _default_instance() as instance:
        with schedule_origin_context("bad_env_fn_schedule") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)

            assert isinstance(result, ScheduledExecutionFailed)
            assert (
                "Error occurred during the execution of run_config_fn for schedule bad_env_fn_schedule"
                in result.errors[0].to_string()
            )

            assert not result.run_id

            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert ticks[0].status == ScheduleTickStatus.FAILURE
            assert (
                "Error occurred during the execution of run_config_fn for schedule bad_env_fn_schedule"
                in ticks[0].error.message
            )


@pytest.mark.parametrize("schedule_origin_context", [python_schedule_origin, grpc_schedule_origin])
def test_bad_should_execute(schedule_origin_context):
    with _default_instance() as instance:
        with schedule_origin_context("bad_should_execute_schedule") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)
            assert isinstance(result, ScheduledExecutionFailed)
            assert (
                "Error occurred during the execution of should_execute for schedule bad_should_execute_schedule"
                in result.errors[0].to_string()
            )

            assert not result.run_id

            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert ticks[0].status == ScheduleTickStatus.FAILURE
            assert (
                "Error occurred during the execution of should_execute for schedule bad_should_execute_schedule"
                in ticks[0].error.message
            )


@pytest.mark.parametrize("schedule_origin_context", [python_schedule_origin, grpc_schedule_origin])
def test_skip(schedule_origin_context):
    with _default_instance() as instance:
        with schedule_origin_context("skip_schedule") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)

            assert isinstance(result, ScheduledExecutionSkipped)

            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert ticks[0].status == ScheduleTickStatus.SKIPPED


@pytest.mark.parametrize("schedule_origin_context", [python_schedule_origin, grpc_schedule_origin])
def test_wrong_config(schedule_origin_context):
    with _default_instance() as instance:
        with schedule_origin_context("wrong_config_schedule") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)

            assert isinstance(result, ScheduledExecutionFailed)
            assert "DagsterInvalidConfigError" in result.errors[0].to_string()

            run = instance.get_run_by_id(result.run_id)
            assert run.is_failure

            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert ticks[0].status == ScheduleTickStatus.SUCCESS


def test_bad_load():
    with _default_instance() as instance:
        instance = DagsterInstance.get()

        working_directory = os.path.dirname(__file__)

        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            python_file=__file__,
            attribute="doesnt_exist",
            working_directory=working_directory,
        )

        repo_origin = ExternalRepositoryOrigin(
            ManagedGrpcPythonEnvRepositoryLocationOrigin(
                loadable_target_origin=loadable_target_origin
            ),
            "doesnt_exist",
        )

        schedule_origin = repo_origin.get_schedule_origin("also_doesnt_exist")

        result = sync_launch_scheduled_execution(schedule_origin)
        assert isinstance(result, ScheduledExecutionFailed)
        assert "doesnt_exist not found at module scope in file" in result.errors[0].to_string()

        ticks = instance.get_schedule_ticks(schedule_origin.get_id())
        assert ticks[0].status == ScheduleTickStatus.FAILURE
        assert "doesnt_exist not found at module scope in file" in ticks[0].error.message


def test_bad_load_grpc():
    with _default_instance() as instance:
        with grpc_schedule_origin("doesnt_exist") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)
            assert isinstance(result, ScheduledExecutionFailed)
            assert "Could not find schedule named doesnt_exist" in result.errors[0].to_string()

            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert ticks[0].status == ScheduleTickStatus.FAILURE
            assert "Could not find schedule named doesnt_exist" in ticks[0].error.message


def test_grpc_server_down():
    with _default_instance() as instance:
        down_grpc_repo_origin = ExternalRepositoryOrigin(
            GrpcServerRepositoryLocationOrigin(
                host="localhost", port=find_free_port(), socket=None,
            ),
            repository_name="down_repo",
        )

        down_grpc_schedule_origin = down_grpc_repo_origin.get_schedule_origin("down_schedule")

        instance = DagsterInstance.get()
        result = sync_launch_scheduled_execution(down_grpc_schedule_origin)

        assert isinstance(result, ScheduledExecutionFailed)
        assert "failed to connect to all addresses" in result.errors[0].to_string()

        ticks = instance.get_schedule_ticks(down_grpc_schedule_origin.get_id())
        assert ticks[0].status == ScheduleTickStatus.FAILURE
        assert "failed to connect to all addresses" in ticks[0].error.message


@pytest.mark.parametrize("schedule_origin_context", [python_schedule_origin, grpc_schedule_origin])
def test_launch_failure(schedule_origin_context):
    with instance_for_test(
        overrides={
            "run_launcher": {"module": "dagster.core.test_utils", "class": "ExplodingRunLauncher",},
        },
    ) as instance:
        with schedule_origin_context("simple_schedule") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)
            assert isinstance(result, ScheduledExecutionFailed)

            assert "NotImplementedError" in result.errors[0]

            run = instance.get_run_by_id(result.run_id)
            assert run is not None

            assert run.status == PipelineRunStatus.FAILURE

            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert ticks[0].status == ScheduleTickStatus.SUCCESS


def test_origin_ids_stable():
    # This test asserts fixed schedule origin IDs to prevent any changes from
    # accidentally shifting these ids that are persisted to ScheduleStorage

    python_origin = ExternalScheduleOrigin(
        ExternalRepositoryOrigin(
            ManagedGrpcPythonEnvRepositoryLocationOrigin(
                LoadableTargetOrigin(
                    executable_path="/fake/executable",
                    python_file="/fake/file/path",
                    attribute="fake_attribute",
                )
            ),
            "fake_repo",
        ),
        "fake_schedule",
    )
    assert python_origin.get_id() == "be50189ea5d28dedf78acc475cb46050d780364a"

    grpc_origin = ExternalScheduleOrigin(
        ExternalRepositoryOrigin(
            GrpcServerRepositoryLocationOrigin(host="fakehost", port=52618), "repo_name"
        ),
        "fake_schedule",
    )

    assert grpc_origin.get_id() == "db2ef19777de79ca7ccaff32fa6ea47f389260a1"
