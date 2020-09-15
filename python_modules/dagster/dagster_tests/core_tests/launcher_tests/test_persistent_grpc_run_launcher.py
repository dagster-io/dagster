import os
import time
from contextlib import contextmanager

import pytest

from dagster import file_relative_path, pipeline, repository, seven, solid
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.errors import DagsterLaunchFailedError
from dagster.core.host_representation.handle import RepositoryLocationHandle
from dagster.core.host_representation.repository_location import GrpcServerRepositoryLocation
from dagster.core.instance import DagsterInstance
from dagster.core.launcher.grpc_run_launcher import GrpcRunLauncher
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import (
    instance_for_test,
    poll_for_event,
    poll_for_finished_run,
    poll_for_step_start,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.server import GrpcServerProcess


@solid
def noop_solid(_):
    pass


@pipeline
def noop_pipeline():
    pass


@solid
def slow_solid(_):
    time.sleep(4)


@pipeline
def slow_pipeline():
    slow_solid()


@solid
def crashy_solid(_):
    os._exit(1)  # pylint: disable=W0212


@pipeline
def crashy_pipeline():
    crashy_solid()


@solid
def sleepy_solid(_):
    while True:
        time.sleep(0.1)


@pipeline
def sleepy_pipeline():
    sleepy_solid()


@solid
def return_one(_):
    return 1


@solid
def multiply_by_2(_, num):
    return num * 2


@solid
def multiply_by_3(_, num):
    return num * 3


@solid
def add(_, num1, num2):
    return num1 + num2


@pipeline
def math_diamond():
    one = return_one()
    add(multiply_by_2(one), multiply_by_3(one))


@repository
def nope():
    return [noop_pipeline, crashy_pipeline, sleepy_pipeline, slow_pipeline, math_diamond]


def grpc_instance():
    return instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster.core.launcher.grpc_run_launcher",
                "class": "GrpcRunLauncher",
            }
        },
    )


def test_repo_construction():
    repo_yaml = file_relative_path(__file__, "repo.yaml")
    assert ReconstructableRepository.from_legacy_repository_yaml(repo_yaml).get_definition()


@contextmanager
def get_external_pipeline_from_grpc_server_repository(pipeline_name):
    repo_yaml = file_relative_path(__file__, "repo.yaml")
    recon_repo = ReconstructableRepository.from_legacy_repository_yaml(repo_yaml)
    loadable_target_origin = recon_repo.get_origin().loadable_target_origin
    server_process = GrpcServerProcess(loadable_target_origin=loadable_target_origin)

    try:
        with server_process.create_ephemeral_client() as api_client:
            repository_location = GrpcServerRepositoryLocation(
                RepositoryLocationHandle.create_grpc_server_location(
                    location_name="test",
                    port=api_client.port,
                    socket=api_client.socket,
                    host=api_client.host,
                )
            )

            yield repository_location.get_repository("nope").get_full_external_pipeline(
                pipeline_name
            )
    finally:
        server_process.wait()


@contextmanager
def get_external_pipeline_from_managed_grpc_python_env_repository(pipeline_name):
    repository_location_handle = RepositoryLocationHandle.create_process_bound_grpc_server_location(
        loadable_target_origin=LoadableTargetOrigin(
            attribute="nope",
            python_file=file_relative_path(__file__, "test_cli_api_run_launcher.py"),
        ),
        location_name="nope",
    )
    repository_location = GrpcServerRepositoryLocation(repository_location_handle)
    try:
        yield repository_location.get_repository("nope").get_full_external_pipeline(pipeline_name)
    finally:
        repository_location_handle.cleanup()


@pytest.mark.parametrize(
    "get_external_pipeline",
    [
        get_external_pipeline_from_grpc_server_repository,
        get_external_pipeline_from_managed_grpc_python_env_repository,
    ],
)
def test_successful_run(get_external_pipeline):  # pylint: disable=redefined-outer-name
    with grpc_instance() as instance:
        pipeline_run = instance.create_run_for_pipeline(pipeline_def=noop_pipeline, run_config=None)

        with get_external_pipeline(pipeline_run.pipeline_name) as external_pipeline:
            run_id = pipeline_run.run_id

            assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

            launcher = instance.run_launcher
            launcher.launch_run(
                instance=instance, run=pipeline_run, external_pipeline=external_pipeline
            )

            pipeline_run = instance.get_run_by_id(run_id)
            assert pipeline_run
            assert pipeline_run.run_id == run_id

            pipeline_run = poll_for_finished_run(instance, run_id)
            assert pipeline_run.status == PipelineRunStatus.SUCCESS


def test_run_always_finishes():  # pylint: disable=redefined-outer-name
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(
            temp_dir,
            overrides={
                "run_launcher": {
                    "module": "dagster.core.launcher.grpc_run_launcher",
                    "class": "GrpcRunLauncher",
                }
            },
        )

        pipeline_run = instance.create_run_for_pipeline(pipeline_def=slow_pipeline, run_config=None)
        run_id = pipeline_run.run_id

        recon_repo = ReconstructableRepository.for_file(__file__, "nope")
        loadable_target_origin = recon_repo.get_origin().loadable_target_origin

        server_process = GrpcServerProcess(
            loadable_target_origin=loadable_target_origin, max_workers=4
        )
        with server_process.create_ephemeral_client() as api_client:
            repository_location = GrpcServerRepositoryLocation(
                RepositoryLocationHandle.create_grpc_server_location(
                    location_name="test",
                    port=api_client.port,
                    socket=api_client.socket,
                    host=api_client.host,
                )
            )

            external_pipeline = repository_location.get_repository(
                "nope"
            ).get_full_external_pipeline("slow_pipeline")

            assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

            launcher = instance.run_launcher
            launcher.launch_run(
                instance=instance, run=pipeline_run, external_pipeline=external_pipeline
            )

        # Server process now receives shutdown event, run has not finished yet
        pipeline_run = instance.get_run_by_id(run_id)
        assert not pipeline_run.is_finished
        assert server_process.server_process.poll() is None

        # Server should wait until run finishes, then shutdown
        pipeline_run = poll_for_finished_run(instance, run_id)
        assert pipeline_run.status == PipelineRunStatus.SUCCESS

        start_time = time.time()
        while server_process.server_process.poll() is None:
            time.sleep(0.05)
            # Verify server process cleans up eventually
            assert time.time() - start_time < 5

        server_process.wait()


@pytest.mark.parametrize(
    "get_external_pipeline",
    [
        get_external_pipeline_from_grpc_server_repository,
        get_external_pipeline_from_managed_grpc_python_env_repository,
    ],
)
def test_crashy_run(get_external_pipeline):  # pylint: disable=redefined-outer-name
    with grpc_instance() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=crashy_pipeline, run_config=None
        )

        with get_external_pipeline(pipeline_run.pipeline_name) as external_pipeline:

            run_id = pipeline_run.run_id

            assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

            launcher = instance.run_launcher
            launcher.launch_run(instance, pipeline_run, external_pipeline)

            failed_pipeline_run = instance.get_run_by_id(run_id)

            assert failed_pipeline_run
            assert failed_pipeline_run.run_id == run_id

            failed_pipeline_run = poll_for_finished_run(instance, run_id, timeout=5)
            assert failed_pipeline_run.status == PipelineRunStatus.FAILURE

            event_records = instance.all_logs(run_id)

            message = "Pipeline execution process for {run_id} unexpectedly exited.".format(
                run_id=run_id
            )

            assert _message_exists(event_records, message)


def test_terminate_after_shutdown():
    with grpc_instance() as instance:
        repository_location_handle = RepositoryLocationHandle.create_process_bound_grpc_server_location(
            loadable_target_origin=LoadableTargetOrigin(
                attribute="nope",
                python_file=file_relative_path(__file__, "test_cli_api_run_launcher.py"),
            ),
            location_name="nope",
        )
        repository_location = GrpcServerRepositoryLocation(repository_location_handle)

        external_pipeline = repository_location.get_repository("nope").get_full_external_pipeline(
            "sleepy_pipeline"
        )

        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=sleepy_pipeline, run_config=None
        )

        launcher = instance.run_launcher
        launcher.launch_run(instance, pipeline_run, external_pipeline)

        poll_for_step_start(instance, pipeline_run.run_id)

        # Tell the server to shut down once executions finish
        repository_location_handle.client.cleanup_server()

        # Trying to start another run fails
        doomed_to_fail_external_pipeline = repository_location.get_repository(
            "nope"
        ).get_full_external_pipeline("math_diamond")
        doomed_to_fail_pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=math_diamond, run_config=None
        )

        with pytest.raises(DagsterLaunchFailedError):
            launcher.launch_run(
                instance, doomed_to_fail_pipeline_run, doomed_to_fail_external_pipeline
            )

        # Can terminate the run even after the shutdown event has been received
        assert launcher.can_terminate(pipeline_run.run_id)
        assert launcher.terminate(pipeline_run.run_id)

        # Server process now shuts down cleanly since there are no more executions


@pytest.mark.parametrize(
    "get_external_pipeline",
    [
        get_external_pipeline_from_grpc_server_repository,
        get_external_pipeline_from_managed_grpc_python_env_repository,
    ],
)
def test_terminated_run(get_external_pipeline):  # pylint: disable=redefined-outer-name
    with grpc_instance() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=sleepy_pipeline, run_config=None
        )

        with get_external_pipeline(pipeline_run.pipeline_name) as external_pipeline:
            run_id = pipeline_run.run_id

            assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

            launcher = instance.run_launcher
            launcher.launch_run(instance, pipeline_run, external_pipeline)

            poll_for_step_start(instance, run_id)

            assert launcher.can_terminate(run_id)
            assert launcher.terminate(run_id)

            terminated_pipeline_run = poll_for_finished_run(instance, run_id, timeout=30)
            terminated_pipeline_run = instance.get_run_by_id(run_id)
            assert terminated_pipeline_run.status == PipelineRunStatus.FAILURE

            poll_for_event(
                instance, run_id, event_type="ENGINE_EVENT", message="Process for pipeline exited"
            )

            run_logs = instance.all_logs(run_id)
            event_types = [event.dagster_event.event_type_value for event in run_logs]
            assert event_types == [
                "ENGINE_EVENT",
                "PIPELINE_START",
                "ENGINE_EVENT",
                "STEP_START",
                "STEP_FAILURE",
                "PIPELINE_FAILURE",
                "ENGINE_EVENT",
                "ENGINE_EVENT",
            ]


def _get_engine_events(event_records):
    for er in event_records:
        if er.dagster_event and er.dagster_event.is_engine_event:
            yield er


def _get_successful_step_keys(event_records):

    step_keys = set()

    for er in event_records:
        if er.dagster_event and er.dagster_event.is_step_success:
            step_keys.add(er.dagster_event.step_key)

    return step_keys


def _message_exists(event_records, message_text):
    for event_record in event_records:
        if message_text in event_record.message:
            return True

    return False


@pytest.mark.parametrize(
    "get_external_pipeline",
    [
        get_external_pipeline_from_grpc_server_repository,
        get_external_pipeline_from_managed_grpc_python_env_repository,
    ],
)
def test_single_solid_selection_execution(
    get_external_pipeline,
):  # pylint: disable=redefined-outer-name
    with grpc_instance() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=math_diamond, run_config=None, solids_to_execute={"return_one"}
        )
        run_id = pipeline_run.run_id

        assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

        with get_external_pipeline(pipeline_run.pipeline_name) as external_pipeline:
            launcher = instance.run_launcher
            launcher.launch_run(instance, pipeline_run, external_pipeline)
            finished_pipeline_run = poll_for_finished_run(instance, run_id)

            event_records = instance.all_logs(run_id)

            assert finished_pipeline_run
            assert finished_pipeline_run.run_id == run_id
            assert finished_pipeline_run.status == PipelineRunStatus.SUCCESS

            assert _get_successful_step_keys(event_records) == {"return_one.compute"}


@pytest.mark.parametrize(
    "get_external_pipeline",
    [
        get_external_pipeline_from_grpc_server_repository,
        get_external_pipeline_from_managed_grpc_python_env_repository,
    ],
)
def test_multi_solid_selection_execution(
    get_external_pipeline,
):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=math_diamond,
            run_config=None,
            solids_to_execute={"return_one", "multiply_by_2"},
        )
        run_id = pipeline_run.run_id

        assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

        with get_external_pipeline(pipeline_run.pipeline_name) as external_pipeline:
            launcher = instance.run_launcher
            launcher.launch_run(instance, pipeline_run, external_pipeline)
            finished_pipeline_run = poll_for_finished_run(instance, run_id)

            event_records = instance.all_logs(run_id)

            assert finished_pipeline_run
            assert finished_pipeline_run.run_id == run_id
            assert finished_pipeline_run.status == PipelineRunStatus.SUCCESS

            assert _get_successful_step_keys(event_records) == {
                "return_one.compute",
                "multiply_by_2.compute",
            }


@pytest.mark.parametrize(
    "get_external_pipeline",
    [
        get_external_pipeline_from_grpc_server_repository,
        get_external_pipeline_from_managed_grpc_python_env_repository,
    ],
)
def test_engine_events(get_external_pipeline):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        pipeline_run = instance.create_run_for_pipeline(pipeline_def=math_diamond, run_config=None)
        run_id = pipeline_run.run_id

        assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

        with get_external_pipeline(pipeline_run.pipeline_name) as external_pipeline:
            launcher = instance.run_launcher
            launcher.launch_run(instance, pipeline_run, external_pipeline)
            finished_pipeline_run = poll_for_finished_run(instance, run_id)

            assert finished_pipeline_run
            assert finished_pipeline_run.run_id == run_id
            assert finished_pipeline_run.status == PipelineRunStatus.SUCCESS

            poll_for_event(
                instance, run_id, event_type="ENGINE_EVENT", message="Process for pipeline exited"
            )
            event_records = instance.all_logs(run_id)

            (started_process, executing_steps, finished_steps, process_exited) = tuple(
                _get_engine_events(event_records)
            )

            assert "Started process for pipeline" in started_process.message
            assert "Executing steps in process" in executing_steps.message
            assert "Finished steps in process" in finished_steps.message
            assert "Process for pipeline exited" in process_exited.message


def test_not_initialized():  # pylint: disable=redefined-outer-name
    run_launcher = GrpcRunLauncher()
    run_id = "dummy"

    assert run_launcher.join() is None
    assert run_launcher.can_terminate(run_id) is False
    assert run_launcher.terminate(run_id) is False
