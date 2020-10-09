import os
import sys
import time
from contextlib import contextmanager

import pytest

from dagster import DefaultRunLauncher, file_relative_path, pipeline, repository, seven, solid
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation.handle import RepositoryLocationHandle
from dagster.core.host_representation.repository_location import (
    GrpcServerRepositoryLocation,
    PythonEnvRepositoryLocation,
)
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
def slow_solid(_):
    time.sleep(4)


@pipeline
def slow_pipeline():
    slow_solid()


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
            python_file=file_relative_path(__file__, "test_default_run_launcher.py"),
        ),
        location_name="nope",
    )
    repository_location = GrpcServerRepositoryLocation(repository_location_handle)
    try:
        yield repository_location.get_repository("nope").get_full_external_pipeline(pipeline_name)
    finally:
        repository_location_handle.cleanup()


@contextmanager
def get_external_pipeline_from_python_location(pipeline_name):
    repository_location_handle = RepositoryLocationHandle.create_python_env_location(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="nope",
            python_file=file_relative_path(__file__, "test_default_run_launcher.py"),
        ),
        location_name="nope",
    )

    yield (
        PythonEnvRepositoryLocation(repository_location_handle)
        .get_repository("nope")
        .get_full_external_pipeline(pipeline_name)
    )


def run_configs():
    return [
        None,
        pytest.param(
            {"execution": {"multiprocess": {}}, "storage": {"filesystem": {}}},
            marks=pytest.mark.skipif(
                seven.IS_WINDOWS, reason="multiprocessing tests flaky on windows"
            ),
        ),
    ]


def _is_multiprocess(run_config):
    return run_config and "execution" in run_config and "multiprocess" in run_config["execution"]


def _check_event_log(event_log, expected_type_and_message):
    assert len(event_log) == len(expected_type_and_message)
    log_iter = iter(event_log)

    for event_type, message in expected_type_and_message:
        next_log = next(log_iter)
        assert next_log.dagster_event.event_type_value == event_type
        assert message in next_log.message


@pytest.mark.parametrize(
    "get_external_pipeline",
    [
        get_external_pipeline_from_grpc_server_repository,
        get_external_pipeline_from_managed_grpc_python_env_repository,
        get_external_pipeline_from_python_location,
    ],
)
@pytest.mark.parametrize(
    "run_config", run_configs(),
)
def test_successful_run(get_external_pipeline, run_config):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=noop_pipeline, run_config=run_config
        )

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


@pytest.mark.parametrize(
    "get_external_pipeline",
    [
        get_external_pipeline_from_grpc_server_repository,
        get_external_pipeline_from_managed_grpc_python_env_repository,
        get_external_pipeline_from_python_location,
    ],
)
@pytest.mark.parametrize(
    "run_config", run_configs(),
)
def test_crashy_run(get_external_pipeline, run_config):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=crashy_pipeline, run_config=run_config,
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

            if _is_multiprocess(run_config):
                message = (
                    "Multiprocess executor: child process for "
                    "step crashy_solid.compute unexpectedly exited"
                )
            else:
                message = "Pipeline execution process for {run_id} unexpectedly exited.".format(
                    run_id=run_id
                )

            assert _message_exists(event_records, message)


@pytest.mark.parametrize(
    "get_external_pipeline",
    [
        get_external_pipeline_from_grpc_server_repository,
        get_external_pipeline_from_managed_grpc_python_env_repository,
        get_external_pipeline_from_python_location,
    ],
)
@pytest.mark.parametrize(
    "run_config", run_configs(),
)
def test_terminated_run(get_external_pipeline, run_config):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=sleepy_pipeline, run_config=run_config,
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
                instance, run_id, event_type="ENGINE_EVENT", message="Process for pipeline exited",
            )

            run_logs = instance.all_logs(run_id)

            if _is_multiprocess(run_config):
                _check_event_log(
                    run_logs,
                    [
                        ("ENGINE_EVENT", "Started process for pipeline"),
                        ("PIPELINE_START", 'Started execution of pipeline "sleepy_pipeline".'),
                        ("ENGINE_EVENT", "Executing steps using multiprocess executor"),
                        ("ENGINE_EVENT", "Launching subprocess for sleepy_solid.compute"),
                        ("ENGINE_EVENT", "Executing step sleepy_solid.compute in subprocess"),
                        ("STEP_START", 'Started execution of step "sleepy_solid.compute".'),
                        ("ENGINE_EVENT", "Received pipeline termination request"),
                        (
                            "ENGINE_EVENT",
                            "Multiprocess executor: received termination signal - forwarding to active child process",
                        ),
                        ("STEP_FAILURE", 'Execution of step "sleepy_solid.compute" failed.'),
                        (
                            "PIPELINE_FAILURE",
                            'Execution of pipeline "sleepy_pipeline" failed. An exception was thrown during execution.',
                        ),
                        ("ENGINE_EVENT", "Process for pipeline exited"),
                    ],
                )
            else:
                _check_event_log(
                    run_logs,
                    [
                        ("ENGINE_EVENT", "Started process for pipeline"),
                        ("PIPELINE_START", 'Started execution of pipeline "sleepy_pipeline".'),
                        ("ENGINE_EVENT", "Executing steps in process"),
                        ("STEP_START", 'Started execution of step "sleepy_solid.compute".'),
                        ("ENGINE_EVENT", "Received pipeline termination request"),
                        ("STEP_FAILURE", 'Execution of step "sleepy_solid.compute" failed.'),
                        ("PIPELINE_FAILURE", 'Execution of pipeline "sleepy_pipeline" failed.'),
                        ("ENGINE_EVENT", "Pipeline execution terminated by interrupt"),
                        ("ENGINE_EVENT", "Process for pipeline exited"),
                    ],
                )


def _get_engine_events(event_records):
    return [er for er in event_records if er.dagster_event and er.dagster_event.is_engine_event]


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
        get_external_pipeline_from_python_location,
    ],
)
@pytest.mark.parametrize(
    "run_config", run_configs(),
)
def test_single_solid_selection_execution(
    get_external_pipeline, run_config,
):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=math_diamond, run_config=run_config, solids_to_execute={"return_one"}
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
        get_external_pipeline_from_python_location,
    ],
)
@pytest.mark.parametrize(
    "run_config", run_configs(),
)
def test_multi_solid_selection_execution(
    get_external_pipeline, run_config,
):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=math_diamond,
            run_config=run_config,
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
        get_external_pipeline_from_python_location,
    ],
)
@pytest.mark.parametrize(
    "run_config", run_configs(),
)
def test_engine_events(get_external_pipeline, run_config):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=math_diamond, run_config=run_config
        )
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

            engine_events = _get_engine_events(event_records)

            if _is_multiprocess(run_config):
                messages = [
                    "Started process for pipeline",
                    "Executing steps using multiprocess executor",
                    "Launching subprocess for return_one.compute",
                    "Executing step return_one.compute in subprocess",
                    # multiply_by_2 and multiply_by_3 launch and execute in non-deterministic order
                    "",
                    "",
                    "",
                    "",
                    "Launching subprocess for add.compute",
                    "Executing step add.compute in subprocess",
                    "Multiprocess executor: parent process exiting",
                    "Process for pipeline exited",
                ]
            else:
                messages = [
                    "Started process for pipeline",
                    "Executing steps in process",
                    "Finished steps in process",
                    "Process for pipeline exited",
                ]

            events_iter = iter(engine_events)
            assert len(engine_events) == len(messages)

            for message in messages:
                next_log = next(events_iter)
                assert message in next_log.message


def test_not_initialized():  # pylint: disable=redefined-outer-name
    run_launcher = DefaultRunLauncher()
    run_id = "dummy"

    assert run_launcher.join() is None
    assert run_launcher.can_terminate(run_id) is False
    assert run_launcher.terminate(run_id) is False
