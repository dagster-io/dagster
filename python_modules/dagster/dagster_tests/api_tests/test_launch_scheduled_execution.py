import datetime
import os
import sys
from contextlib import contextmanager

import pytest

from dagster import daily_schedule, pipeline, repository, solid
from dagster.api.launch_scheduled_execution import sync_launch_scheduled_execution
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.instance import DagsterInstance
from dagster.core.origin import RepositoryGrpcServerOrigin
from dagster.core.scheduler import (
    ScheduleTickStatus,
    ScheduledExecutionFailed,
    ScheduledExecutionSkipped,
    ScheduledExecutionSuccess,
)
from dagster.core.test_utils import instance_for_test
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.server import GrpcServerProcess
from dagster.utils import find_free_port

_COUPLE_DAYS_AGO = datetime.datetime.now() - datetime.timedelta(days=2)


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


@contextmanager
def cli_api_schedule_origin(schedule_name):
    recon_repo = ReconstructableRepository.for_file(__file__, "the_repo")
    schedule = recon_repo.get_reconstructable_schedule(schedule_name)
    yield schedule.get_origin()


@contextmanager
def grpc_schedule_origin(schedule_name):
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable, python_file=__file__, attribute="the_repo"
    )
    server_process = GrpcServerProcess(loadable_target_origin=loadable_target_origin)
    with server_process.create_ephemeral_client() as api_client:
        repo_origin = RepositoryGrpcServerOrigin(
            host=api_client.host,
            port=api_client.port,
            socket=api_client.socket,
            repository_name="the_repo",
        )
        yield repo_origin.get_schedule_origin(schedule_name)
    server_process.wait()


@pytest.mark.parametrize(
    "schedule_origin_context", [cli_api_schedule_origin, grpc_schedule_origin,],
)
def test_launch_scheduled_execution(schedule_origin_context):
    with instance_for_test() as instance:
        with schedule_origin_context("simple_schedule") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)
            assert isinstance(result, ScheduledExecutionSuccess)

            run = instance.get_run_by_id(result.run_id)
            assert run is not None

            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert ticks[0].status == ScheduleTickStatus.SUCCESS


@pytest.mark.parametrize("schedule_origin_context", [cli_api_schedule_origin, grpc_schedule_origin])
def test_bad_env_fn(schedule_origin_context):
    with instance_for_test() as instance:
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


@pytest.mark.parametrize("schedule_origin_context", [cli_api_schedule_origin, grpc_schedule_origin])
def test_bad_should_execute(schedule_origin_context):
    with instance_for_test() as instance:
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


@pytest.mark.parametrize("schedule_origin_context", [cli_api_schedule_origin, grpc_schedule_origin])
def test_skip(schedule_origin_context):
    with instance_for_test() as instance:
        with schedule_origin_context("skip_schedule") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)

            assert isinstance(result, ScheduledExecutionSkipped)

            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert ticks[0].status == ScheduleTickStatus.SKIPPED


@pytest.mark.parametrize("schedule_origin_context", [cli_api_schedule_origin, grpc_schedule_origin])
def test_wrong_config(schedule_origin_context):
    with instance_for_test() as instance:
        with schedule_origin_context("wrong_config_schedule") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)

            assert isinstance(result, ScheduledExecutionFailed)
            assert "DagsterInvalidConfigError" in result.errors[0].to_string()

            run = instance.get_run_by_id(result.run_id)
            assert run.is_failure

            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert ticks[0].status == ScheduleTickStatus.SUCCESS


def test_bad_load():
    with instance_for_test() as instance:
        instance = DagsterInstance.get()

        working_directory = os.path.dirname(__file__)
        recon_repo = ReconstructableRepository.for_file(__file__, "doesnt_exist", working_directory)
        schedule = recon_repo.get_reconstructable_schedule("also_doesnt_exist")

        result = sync_launch_scheduled_execution(schedule.get_origin())
        assert isinstance(result, ScheduledExecutionFailed)
        assert "doesnt_exist not found at module scope in file" in result.errors[0].to_string()

        ticks = instance.get_schedule_ticks(schedule.get_origin_id())
        assert ticks[0].status == ScheduleTickStatus.FAILURE
        assert "doesnt_exist not found at module scope in file" in ticks[0].error.message


def test_bad_load_grpc():
    with instance_for_test() as instance:
        with grpc_schedule_origin("doesnt_exist") as schedule_origin:
            result = sync_launch_scheduled_execution(schedule_origin)
            assert isinstance(result, ScheduledExecutionFailed)
            assert "Could not find schedule named doesnt_exist" in result.errors[0].to_string()

            ticks = instance.get_schedule_ticks(schedule_origin.get_id())
            assert ticks[0].status == ScheduleTickStatus.FAILURE
            assert "Could not find schedule named doesnt_exist" in ticks[0].error.message


def test_grpc_server_down():
    with instance_for_test() as instance:
        down_grpc_repo_origin = RepositoryGrpcServerOrigin(
            host="localhost", port=find_free_port(), socket=None, repository_name="down_repo"
        )
        down_grpc_schedule_origin = down_grpc_repo_origin.get_schedule_origin("down_schedule")

        instance = DagsterInstance.get()
        result = sync_launch_scheduled_execution(down_grpc_schedule_origin)

        assert isinstance(result, ScheduledExecutionFailed)
        assert "failed to connect to all addresses" in result.errors[0].to_string()

        ticks = instance.get_schedule_ticks(down_grpc_schedule_origin.get_id())
        assert ticks[0].status == ScheduleTickStatus.FAILURE
        assert "failed to connect to all addresses" in ticks[0].error.message


def test_origin_ids_stable(monkeypatch):
    # This test asserts fixed schedule origin IDs to prevent any changes from
    # accidentally shifting these ids that are persisted to ScheduleStorage

    # stable exe path for test
    monkeypatch.setattr(sys, "executable", "/fake/python")

    file_repo = ReconstructableRepository.for_file(
        "/path/to/file", "the_repo", "/path/to/working_dir"
    )

    # ensure monkeypatch worked
    assert file_repo.get_origin().executable_path == "/fake/python"

    assert file_repo.get_origin_id() == "3766b1c554fd961b88b9301756250febff3d0ffa"
    schedule = file_repo.get_reconstructable_schedule("simple_schedule")
    assert schedule.get_origin_id() == "7c60d01588673ffcaea16b6fd59d998dc63ed3c3"

    module_repo = ReconstructableRepository.for_module("dummy_module", "the_repo")
    assert module_repo.get_origin_id() == "86503fc349d4ecf44bd22ca1de64c10f8ffcebbd"
    module_schedule = module_repo.get_reconstructable_schedule("simple_schedule")
    assert module_schedule.get_origin_id() == "e4c7131b74ad600969876d8fa461f215ced9631a"
