import os
import time
from contextlib import contextmanager

import pytest

from dagster import DefaultRunLauncher, file_relative_path, pipeline, repository, seven, solid
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation.handle import RepositoryLocationHandle
from dagster.core.host_representation.repository_location import (
    GrpcServerRepositoryLocation,
    InProcessRepositoryLocation,
)
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.grpc.server import GrpcServerProcess
from dagster.grpc.types import LoadableTargetOrigin


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
    return [noop_pipeline, crashy_pipeline, sleepy_pipeline, math_diamond]


@pytest.fixture(scope='module')
def temp_instance():
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(
            temp_dir,
            overrides={'run_launcher': {'module': 'dagster', 'class': 'DefaultRunLauncher',}},
        )
        try:
            yield instance
        finally:
            instance.run_launcher.join()


def test_repo_construction():
    repo_yaml = file_relative_path(__file__, 'repo.yaml')
    assert ReconstructableRepository.from_legacy_repository_yaml(repo_yaml).get_definition()


def poll_for_run(instance, run_id, timeout=20):
    total_time = 0
    interval = 0.01

    while True:
        run = instance.get_run_by_id(run_id)
        if run.is_finished:
            return run
        else:
            time.sleep(interval)
            total_time += interval
            if total_time > timeout:
                raise Exception('Timed out')


def poll_for_step_start(instance, run_id, timeout=10):
    poll_for_event(instance, run_id, event_type='STEP_START', message=None, timeout=timeout)


def poll_for_event(instance, run_id, event_type, message, timeout=10):
    total_time = 0
    backoff = 0.01

    while True:
        time.sleep(backoff)
        logs = instance.all_logs(run_id)
        matching_events = [
            log_record.dagster_event
            for log_record in logs
            if log_record.dagster_event.event_type_value == event_type
        ]
        if matching_events:
            if message is None:
                return
            for matching_message in (event.message for event in matching_events):
                if message in matching_message:
                    return

        total_time += backoff
        backoff = backoff * 2
        if total_time > timeout:
            raise Exception('Timed out')


@contextmanager
def get_external_pipeline_from_grpc_server_repository(pipeline_name):
    repo_yaml = file_relative_path(__file__, 'repo.yaml')
    recon_repo = ReconstructableRepository.from_legacy_repository_yaml(repo_yaml)
    loadable_target_origin = LoadableTargetOrigin.from_python_origin(recon_repo.get_origin())
    with GrpcServerProcess(
        loadable_target_origin=loadable_target_origin
    ).create_ephemeral_client() as server:
        repository_location = GrpcServerRepositoryLocation(
            RepositoryLocationHandle.create_grpc_server_location(
                location_name='test', port=server.port, socket=server.socket, host='localhost',
            )
        )

        yield repository_location.get_repository('nope').get_full_external_pipeline(pipeline_name)


@contextmanager
def get_external_pipeline_from_managed_grpc_python_env_repository(pipeline_name):

    repository_location_handle = RepositoryLocationHandle.create_process_bound_grpc_server_location(
        loadable_target_origin=LoadableTargetOrigin(
            attribute='nope',
            python_file=file_relative_path(__file__, 'test_cli_api_run_launcher.py'),
        ),
        location_name='nope',
    )

    repository_location = GrpcServerRepositoryLocation(repository_location_handle)

    yield repository_location.get_repository('nope').get_full_external_pipeline(pipeline_name)


@contextmanager
def get_external_pipeline_from_in_process_location(pipeline_name):
    repo_yaml = file_relative_path(__file__, 'repo.yaml')
    recon_repo = ReconstructableRepository.from_legacy_repository_yaml(repo_yaml)
    yield (
        InProcessRepositoryLocation(recon_repo)
        .get_repository('nope')
        .get_full_external_pipeline(pipeline_name)
    )


@pytest.mark.parametrize(
    "get_external_pipeline",
    [
        get_external_pipeline_from_grpc_server_repository,
        get_external_pipeline_from_managed_grpc_python_env_repository,
        get_external_pipeline_from_in_process_location,
    ],
)
def test_successful_run(
    temp_instance, get_external_pipeline
):  # pylint: disable=redefined-outer-name
    instance = temp_instance

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

        pipeline_run = poll_for_run(instance, run_id)
        assert pipeline_run.status == PipelineRunStatus.SUCCESS


@pytest.mark.parametrize(
    "get_external_pipeline",
    [
        get_external_pipeline_from_grpc_server_repository,
        get_external_pipeline_from_managed_grpc_python_env_repository,
        get_external_pipeline_from_in_process_location,
    ],
)
def test_crashy_run(temp_instance, get_external_pipeline):  # pylint: disable=redefined-outer-name
    instance = temp_instance

    pipeline_run = instance.create_run_for_pipeline(pipeline_def=crashy_pipeline, run_config=None)

    with get_external_pipeline(pipeline_run.pipeline_name) as external_pipeline:

        run_id = pipeline_run.run_id

        assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

        launcher = instance.run_launcher
        launcher.launch_run(instance, pipeline_run, external_pipeline)

        failed_pipeline_run = instance.get_run_by_id(run_id)

        assert failed_pipeline_run
        assert failed_pipeline_run.run_id == run_id

        failed_pipeline_run = poll_for_run(instance, run_id, timeout=5)
        assert failed_pipeline_run.status == PipelineRunStatus.FAILURE

        event_records = instance.all_logs(run_id)

        message = 'Pipeline execution process for {run_id} unexpectedly exited.'.format(
            run_id=run_id
        )

        assert _message_exists(event_records, message)


@pytest.mark.parametrize(
    "get_external_pipeline,in_process",
    [
        (get_external_pipeline_from_grpc_server_repository, False),
        (get_external_pipeline_from_managed_grpc_python_env_repository, False),
        (get_external_pipeline_from_in_process_location, True),
    ],
)
def test_terminated_run(
    temp_instance, get_external_pipeline, in_process
):  # pylint: disable=redefined-outer-name
    instance = temp_instance

    pipeline_run = instance.create_run_for_pipeline(pipeline_def=sleepy_pipeline, run_config=None)

    with get_external_pipeline(pipeline_run.pipeline_name) as external_pipeline:
        run_id = pipeline_run.run_id

        assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

        launcher = instance.run_launcher
        launcher.launch_run(instance, pipeline_run, external_pipeline)

        poll_for_step_start(instance, run_id)

        assert launcher.can_terminate(run_id)
        assert launcher.terminate(run_id)

        terminated_pipeline_run = poll_for_run(instance, run_id)
        terminated_pipeline_run = instance.get_run_by_id(run_id)
        assert terminated_pipeline_run.status == PipelineRunStatus.FAILURE

        poll_for_run(instance, run_id)

        poll_for_event(
            instance, run_id, event_type='ENGINE_EVENT', message='Process for pipeline exited'
        )

        run_logs = instance.all_logs(run_id)
        event_types = [event.dagster_event.event_type_value for event in run_logs]
        if in_process:
            assert event_types == [
                'ENGINE_EVENT',
                'ENGINE_EVENT',
                'PIPELINE_START',
                'ENGINE_EVENT',
                'STEP_START',
                'STEP_FAILURE',
                'PIPELINE_FAILURE',
                'ENGINE_EVENT',
            ]
        else:
            assert event_types == [
                'ENGINE_EVENT',
                'PIPELINE_START',
                'ENGINE_EVENT',
                'STEP_START',
                'STEP_FAILURE',
                'PIPELINE_FAILURE',
                'ENGINE_EVENT',
                'ENGINE_EVENT',
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
        get_external_pipeline_from_in_process_location,
    ],
)
def test_single_solid_selection_execution(
    temp_instance, get_external_pipeline
):  # pylint: disable=redefined-outer-name
    instance = temp_instance

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=math_diamond, run_config=None, solids_to_execute={'return_one'}
    )
    run_id = pipeline_run.run_id

    assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

    with get_external_pipeline(pipeline_run.pipeline_name) as external_pipeline:
        launcher = instance.run_launcher
        launcher.launch_run(instance, pipeline_run, external_pipeline)
        finished_pipeline_run = poll_for_run(instance, run_id)

        event_records = instance.all_logs(run_id)

        assert finished_pipeline_run
        assert finished_pipeline_run.run_id == run_id
        assert finished_pipeline_run.status == PipelineRunStatus.SUCCESS

        assert _get_successful_step_keys(event_records) == {'return_one.compute'}


@pytest.mark.parametrize(
    "get_external_pipeline",
    [
        get_external_pipeline_from_grpc_server_repository,
        get_external_pipeline_from_managed_grpc_python_env_repository,
        get_external_pipeline_from_in_process_location,
    ],
)
def test_multi_solid_selection_execution(
    temp_instance, get_external_pipeline
):  # pylint: disable=redefined-outer-name
    instance = temp_instance

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=math_diamond,
        run_config=None,
        solids_to_execute={'return_one', 'multiply_by_2'},
    )
    run_id = pipeline_run.run_id

    assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

    with get_external_pipeline(pipeline_run.pipeline_name) as external_pipeline:
        launcher = instance.run_launcher
        launcher.launch_run(instance, pipeline_run, external_pipeline)
        finished_pipeline_run = poll_for_run(instance, run_id)

        event_records = instance.all_logs(run_id)

        assert finished_pipeline_run
        assert finished_pipeline_run.run_id == run_id
        assert finished_pipeline_run.status == PipelineRunStatus.SUCCESS

        assert _get_successful_step_keys(event_records) == {
            'return_one.compute',
            'multiply_by_2.compute',
        }


@pytest.mark.parametrize(
    "get_external_pipeline,in_process",
    [
        (get_external_pipeline_from_grpc_server_repository, False),
        (get_external_pipeline_from_managed_grpc_python_env_repository, False),
        (get_external_pipeline_from_in_process_location, True),
    ],
)
def test_engine_events(
    temp_instance, get_external_pipeline, in_process
):  # pylint: disable=redefined-outer-name
    instance = temp_instance

    pipeline_run = instance.create_run_for_pipeline(pipeline_def=math_diamond, run_config=None)
    run_id = pipeline_run.run_id

    assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

    with get_external_pipeline(pipeline_run.pipeline_name) as external_pipeline:
        launcher = instance.run_launcher
        launcher.launch_run(instance, pipeline_run, external_pipeline)
        finished_pipeline_run = poll_for_run(instance, run_id)

        assert finished_pipeline_run
        assert finished_pipeline_run.run_id == run_id
        assert finished_pipeline_run.status == PipelineRunStatus.SUCCESS

        poll_for_event(
            instance, run_id, event_type='ENGINE_EVENT', message='Process for pipeline exited'
        )
        event_records = instance.all_logs(run_id)

        if in_process:
            (
                about_to_start,
                started_process,
                executing_steps,
                finished_steps,
                process_exited,
            ) = tuple(_get_engine_events(event_records))

            assert 'About to start process' in about_to_start.message
            assert 'Started process for pipeline' in started_process.message
            assert 'Executing steps in process' in executing_steps.message
            assert 'Finished steps in process' in finished_steps.message
            assert 'Process for pipeline exited' in process_exited.message
        else:
            (started_process, executing_steps, finished_steps, process_exited) = tuple(
                _get_engine_events(event_records)
            )

            assert 'Started process for pipeline' in started_process.message
            assert 'Executing steps in process' in executing_steps.message
            assert 'Finished steps in process' in finished_steps.message
            assert 'Process for pipeline exited' in process_exited.message


def test_not_initialized():  # pylint: disable=redefined-outer-name
    run_launcher = DefaultRunLauncher()
    run_id = 'dummy'

    assert run_launcher.join() is None
    assert run_launcher.can_terminate(run_id) is False
    assert run_launcher.terminate(run_id) is False
