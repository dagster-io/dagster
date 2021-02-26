import json
import os
import subprocess
import sys
from contextlib import contextmanager

import pytest
from dagster import check, daily_schedule, pipeline, repository, solid
from dagster.core.errors import DagsterSubprocessError
from dagster.core.host_representation import (
    ExternalJobOrigin,
    ExternalRepositoryOrigin,
    GrpcServerRepositoryLocationOrigin,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
)
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler import (
    ScheduledExecutionFailed,
    ScheduledExecutionResult,
    ScheduledExecutionSkipped,
    ScheduledExecutionSuccess,
)
from dagster.core.scheduler.job import JobTickStatus
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.telemetry import get_dir_from_dagster_home
from dagster.core.test_utils import instance_for_test, today_at_midnight
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.server import GrpcServerProcess
from dagster.serdes.ipc import IPCErrorMessage, read_unary_response
from dagster.seven import xplat_shlex_split
from dagster.utils import find_free_port
from dagster.utils.temp_file import get_temp_file_name

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
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    should_execute=_throw,
)
def bad_should_execute_schedule(_context):
    return {}


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    should_execute=_never,
)
def skip_schedule(_context):
    return {}


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
)
def wrong_config_schedule(_context):
    return {}


@daily_schedule(
    pipeline_name="the_pipeline",
    start_date=_COUPLE_DAYS_AGO,
    execution_timezone="US/Pacific",
)
def pacific_time_schedule(_context):
    return {"solids": {"the_solid": {"config": {"work_amt": "a lot"}}}}


@repository
def the_repo():
    return [
        the_pipeline,
        simple_schedule,
        bad_env_fn_schedule,
        bad_should_execute_schedule,
        skip_schedule,
        wrong_config_schedule,
        pacific_time_schedule,
    ]


def _default_instance():
    return instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster.core.test_utils",
                "class": "MockedRunLauncher",
            }
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

    yield repo_origin.get_job_origin(schedule_name)


@contextmanager
def grpc_schedule_origin(schedule_name):
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable, python_file=__file__, attribute="the_repo"
    )
    server_process = GrpcServerProcess(loadable_target_origin=loadable_target_origin)
    with server_process.create_ephemeral_client() as api_client:
        repo_origin = ExternalRepositoryOrigin(
            GrpcServerRepositoryLocationOrigin(
                host=api_client.host,
                port=api_client.port,
                socket=api_client.socket,
            ),
            repository_name="the_repo",
        )

        yield repo_origin.get_job_origin(schedule_name)
    server_process.wait()


def sync_launch_scheduled_execution(schedule_origin, system_tz=None):
    check.inst_param(schedule_origin, "schedule_origin", ExternalJobOrigin)

    with get_temp_file_name() as output_file:

        parts = (
            [
                sys.executable,
                "-m",
                "dagster",
                "api",
                "launch_scheduled_execution",
                output_file,
            ]
            + xplat_shlex_split(schedule_origin.get_repo_cli_args())
            + ["--schedule_name={}".format(schedule_origin.job_name)]
            + (["--override-system-timezone={}".format(system_tz)] if system_tz else [])
        )
        subprocess.check_call(parts)
        result = read_unary_response(output_file)
        if isinstance(result, ScheduledExecutionResult):
            return result
        elif isinstance(result, IPCErrorMessage):
            error = result.serializable_error_info
            raise DagsterSubprocessError(
                "Error in API subprocess: {message}\n\n{err}".format(
                    message=result.message, err=error.to_string()
                ),
                subprocess_error_infos=[error],
            )
        else:
            check.failed("Unexpected result {}".format(result))


@pytest.mark.parametrize(
    "schedule_origin_context",
    [
        python_schedule_origin,
        grpc_schedule_origin,
    ],
)
def test_launch_successful_execution(schedule_origin_context):
    with _default_instance() as instance:
        with schedule_origin_context("simple_schedule") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)
            assert isinstance(result, ScheduledExecutionSuccess)

            run = instance.get_run_by_id(result.run_id)
            assert run is not None

            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert ticks[0].status == JobTickStatus.SUCCESS


@pytest.mark.parametrize(
    "schedule_origin_context",
    [python_schedule_origin],
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

                assert message_start.get("action") == "_launch_scheduled_executions_started"
                assert message_end.get("action") == "_launch_scheduled_executions_ended"


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

            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert ticks[0].status == JobTickStatus.FAILURE
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

            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert ticks[0].status == JobTickStatus.FAILURE
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

            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert ticks[0].status == JobTickStatus.SKIPPED


@pytest.mark.parametrize("schedule_origin_context", [python_schedule_origin, grpc_schedule_origin])
def test_wrong_config(schedule_origin_context):
    with _default_instance() as instance:
        with schedule_origin_context("wrong_config_schedule") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)

            assert isinstance(result, ScheduledExecutionFailed)
            assert "DagsterInvalidConfigError" in result.errors[0].to_string()

            run = instance.get_run_by_id(result.run_id)
            assert run.is_failure

            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert ticks[0].status == JobTickStatus.SUCCESS


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

        schedule_origin = repo_origin.get_job_origin("also_doesnt_exist")

        result = sync_launch_scheduled_execution(schedule_origin)
        assert isinstance(result, ScheduledExecutionFailed)
        assert "doesnt_exist not found at module scope in file" in result.errors[0].to_string()

        ticks = instance.get_job_ticks(schedule_origin.get_id())
        assert ticks[0].status == JobTickStatus.FAILURE
        assert "doesnt_exist not found at module scope in file" in ticks[0].error.message


def test_bad_load_grpc():
    with _default_instance() as instance:
        with grpc_schedule_origin("doesnt_exist") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)
            assert isinstance(result, ScheduledExecutionFailed)
            assert "Could not find schedule named doesnt_exist" in result.errors[0].to_string()

            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert ticks[0].status == JobTickStatus.FAILURE
            assert "Could not find schedule named doesnt_exist" in ticks[0].error.message


def test_grpc_server_down():
    with _default_instance() as instance:
        down_grpc_repo_origin = ExternalRepositoryOrigin(
            GrpcServerRepositoryLocationOrigin(
                host="localhost",
                port=find_free_port(),
                socket=None,
            ),
            repository_name="down_repo",
        )

        down_grpc_schedule_origin = down_grpc_repo_origin.get_job_origin("down_schedule")

        instance = DagsterInstance.get()
        result = sync_launch_scheduled_execution(down_grpc_schedule_origin)

        assert isinstance(result, ScheduledExecutionFailed)
        assert "failed to connect to all addresses" in result.errors[0].to_string()

        ticks = instance.get_job_ticks(down_grpc_schedule_origin.get_id())
        assert ticks[0].status == JobTickStatus.FAILURE
        assert "failed to connect to all addresses" in ticks[0].error.message


@pytest.mark.parametrize("schedule_origin_context", [python_schedule_origin, grpc_schedule_origin])
def test_launch_failure(schedule_origin_context):
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster.core.test_utils",
                "class": "ExplodingRunLauncher",
            },
        },
    ) as instance:
        with schedule_origin_context("simple_schedule") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)
            assert isinstance(result, ScheduledExecutionFailed)

            assert "NotImplementedError" in result.errors[0]

            run = instance.get_run_by_id(result.run_id)
            assert run is not None

            assert run.status == PipelineRunStatus.FAILURE

            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert ticks[0].status == JobTickStatus.SUCCESS


@pytest.mark.parametrize("schedule_origin_context", [grpc_schedule_origin])
def test_launch_schedule_with_timezone(schedule_origin_context):
    with _default_instance() as instance:
        with schedule_origin_context("pacific_time_schedule") as schedule_origin:
            # Launch fails if system timezone doesn't match schedule timezone
            result = sync_launch_scheduled_execution(schedule_origin, system_tz="US/Eastern")
            assert isinstance(result, ScheduledExecutionFailed)
            assert (
                "Schedule pacific_time_schedule is set to execute in US/Pacific, but this scheduler can only run in the system timezone, US/Eastern"
                in result.errors[0].to_string()
            )

            # and succeeds if it does
            result = sync_launch_scheduled_execution(schedule_origin, system_tz="US/Pacific")
            assert isinstance(result, ScheduledExecutionSuccess)
            run = instance.get_run_by_id(result.run_id)
            assert run is not None
            ticks = instance.get_job_ticks(schedule_origin.get_id())
            assert ticks[0].status == JobTickStatus.SUCCESS


def test_origin_ids_stable():
    # This test asserts fixed schedule origin IDs to prevent any changes from
    # accidentally shifting these ids that are persisted to ScheduleStorage

    python_origin = ExternalJobOrigin(
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
    assert python_origin.get_id() == "eb01cc697463ba614a67567fdeaafcccc60f0fc4"

    grpc_origin = ExternalJobOrigin(
        ExternalRepositoryOrigin(
            GrpcServerRepositoryLocationOrigin(host="fakehost", port=52618), "repo_name"
        ),
        "fake_schedule",
    )

    assert grpc_origin.get_id() == "0961ecddbddfc71104adf036ebe8cd97a94dc77b"
