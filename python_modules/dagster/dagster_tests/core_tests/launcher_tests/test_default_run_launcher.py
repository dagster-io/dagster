import os
import re
import sys
import tempfile
import time
from contextlib import contextmanager

import pytest
from dagster import DefaultRunLauncher, file_relative_path, pipeline, repository, seven, solid
from dagster.core.errors import DagsterLaunchFailedError
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import (
    environ,
    instance_for_test,
    poll_for_event,
    poll_for_finished_run,
    poll_for_step_start,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.core.workspace import WorkspaceProcessContext
from dagster.core.workspace.load_target import GrpcServerTarget, PythonFileTarget
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


@contextmanager
def get_deployed_grpc_server_workspace(instance):
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        attribute="nope",
        python_file=file_relative_path(__file__, "test_default_run_launcher.py"),
    )
    server_process = GrpcServerProcess(loadable_target_origin=loadable_target_origin)

    try:
        with server_process.create_ephemeral_client():  # shuts down when leaves this context
            with WorkspaceProcessContext(
                instance,
                GrpcServerTarget(
                    host="localhost",
                    socket=server_process.socket,
                    port=server_process.port,
                    location_name="test",
                ),
            ) as workspace_process_context:
                yield workspace_process_context.create_request_context()
    finally:
        server_process.wait()


@contextmanager
def get_managed_grpc_server_workspace(instance):
    with WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=file_relative_path(__file__, "test_default_run_launcher.py"),
            attribute="nope",
            working_directory=None,
            location_name="test",
        ),
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


def run_configs():
    return [
        None,
        {"execution": {"multiprocess": {}}, "intermediate_storage": {"filesystem": {}}},
    ]


def _is_multiprocess(run_config):
    return run_config and "execution" in run_config and "multiprocess" in run_config["execution"]


def _check_event_log_contains(event_log, expected_type_and_message):
    types_and_messages = [
        (e.dagster_event.event_type_value, e.message) for e in event_log if e.is_dagster_event
    ]
    for expected_event_type, expected_message_fragment in expected_type_and_message:
        assert any(
            event_type == expected_event_type and expected_message_fragment in message
            for event_type, message in types_and_messages
        ), "Missing {expected_event_type}:{expected_message_fragment}".format(
            expected_event_type=expected_event_type,
            expected_message_fragment=expected_message_fragment,
        )


@pytest.mark.parametrize(
    "get_workspace",
    [
        get_deployed_grpc_server_workspace,
        get_managed_grpc_server_workspace,
    ],
)
@pytest.mark.parametrize(
    "run_config",
    run_configs(),
)
def test_successful_run(get_workspace, run_config):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        with get_workspace(instance) as workspace:

            external_pipeline = (
                workspace.get_repository_location("test")
                .get_repository("nope")
                .get_full_external_pipeline("noop_pipeline")
            )

            pipeline_run = instance.create_run_for_pipeline(
                pipeline_def=noop_pipeline,
                run_config=run_config,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )
            run_id = pipeline_run.run_id

            assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

            instance.launch_run(run_id=pipeline_run.run_id, workspace=workspace)

            pipeline_run = instance.get_run_by_id(run_id)
            assert pipeline_run
            assert pipeline_run.run_id == run_id

            pipeline_run = poll_for_finished_run(instance, run_id)
            assert pipeline_run.status == PipelineRunStatus.SUCCESS


@pytest.mark.parametrize(
    "get_workspace",
    [
        get_deployed_grpc_server_workspace,
        get_managed_grpc_server_workspace,
    ],
)
def test_invalid_instance_run(get_workspace):
    with tempfile.TemporaryDirectory() as temp_dir:
        correct_run_storage_dir = os.path.join(temp_dir, "history", "")
        wrong_run_storage_dir = os.path.join(temp_dir, "wrong", "")

        with environ({"RUN_STORAGE_ENV": correct_run_storage_dir}):
            with instance_for_test(
                temp_dir=temp_dir,
                overrides={
                    "run_storage": {
                        "module": "dagster.core.storage.runs",
                        "class": "SqliteRunStorage",
                        "config": {"base_dir": {"env": "RUN_STORAGE_ENV"}},
                    }
                },
            ) as instance:
                # Server won't be able to load the run from run storage
                with environ({"RUN_STORAGE_ENV": wrong_run_storage_dir}):
                    with get_workspace(instance) as workspace:
                        external_pipeline = (
                            workspace.get_repository_location("test")
                            .get_repository("nope")
                            .get_full_external_pipeline("noop_pipeline")
                        )

                        pipeline_run = instance.create_run_for_pipeline(
                            pipeline_def=noop_pipeline,
                            external_pipeline_origin=external_pipeline.get_external_origin(),
                            pipeline_code_origin=external_pipeline.get_python_origin(),
                        )
                        with pytest.raises(
                            DagsterLaunchFailedError,
                            match=re.escape(
                                "gRPC server could not load run {run_id} in order to execute it".format(
                                    run_id=pipeline_run.run_id
                                )
                            ),
                        ):
                            instance.launch_run(run_id=pipeline_run.run_id, workspace=workspace)

                        failed_run = instance.get_run_by_id(pipeline_run.run_id)
                        assert failed_run.status == PipelineRunStatus.FAILURE


@pytest.mark.parametrize(
    "get_workspace",
    [
        get_deployed_grpc_server_workspace,
        get_managed_grpc_server_workspace,
    ],
)
@pytest.mark.parametrize(
    "run_config",
    run_configs(),
)
@pytest.mark.skipif(
    seven.IS_WINDOWS,
    reason="Crashy pipelines leave resources open on windows, causing filesystem contention",
)
def test_crashy_run(get_workspace, run_config):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        with get_workspace(instance) as workspace:

            external_pipeline = (
                workspace.get_repository_location("test")
                .get_repository("nope")
                .get_full_external_pipeline("crashy_pipeline")
            )

            pipeline_run = instance.create_run_for_pipeline(
                pipeline_def=crashy_pipeline,
                run_config=run_config,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )

            run_id = pipeline_run.run_id

            assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

            instance.launch_run(pipeline_run.run_id, workspace)

            failed_pipeline_run = instance.get_run_by_id(run_id)

            assert failed_pipeline_run
            assert failed_pipeline_run.run_id == run_id

            failed_pipeline_run = poll_for_finished_run(instance, run_id, timeout=5)
            assert failed_pipeline_run.status == PipelineRunStatus.FAILURE

            event_records = instance.all_logs(run_id)

            if _is_multiprocess(run_config):
                message = (
                    "Multiprocess executor: child process for "
                    "step crashy_solid unexpectedly exited"
                )
            else:
                message = "Pipeline execution process for {run_id} unexpectedly exited".format(
                    run_id=run_id
                )

            assert _message_exists(event_records, message)


@pytest.mark.parametrize(
    "get_workspace",
    [
        get_deployed_grpc_server_workspace,
        get_managed_grpc_server_workspace,
    ],
)
@pytest.mark.parametrize(
    "run_config",
    run_configs(),
)
def test_terminated_run(get_workspace, run_config):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        with get_workspace(instance) as workspace:
            external_pipeline = (
                workspace.get_repository_location("test")
                .get_repository("nope")
                .get_full_external_pipeline("sleepy_pipeline")
            )
            pipeline_run = instance.create_run_for_pipeline(
                pipeline_def=sleepy_pipeline,
                run_config=run_config,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )

            run_id = pipeline_run.run_id

            assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

            instance.launch_run(pipeline_run.run_id, workspace)

            poll_for_step_start(instance, run_id)

            launcher = instance.run_launcher
            assert launcher.can_terminate(run_id)
            assert launcher.terminate(run_id)

            terminated_pipeline_run = poll_for_finished_run(instance, run_id, timeout=30)
            terminated_pipeline_run = instance.get_run_by_id(run_id)
            assert terminated_pipeline_run.status == PipelineRunStatus.CANCELED

            poll_for_event(
                instance,
                run_id,
                event_type="ENGINE_EVENT",
                message="Process for pipeline exited",
            )

            run_logs = instance.all_logs(run_id)

            if _is_multiprocess(run_config):
                _check_event_log_contains(
                    run_logs,
                    [
                        ("PIPELINE_CANCELING", "Sending pipeline termination request."),
                        (
                            "ENGINE_EVENT",
                            "Multiprocess executor: received termination signal - forwarding to active child process",
                        ),
                        (
                            "ENGINE_EVENT",
                            "Multiprocess executor: interrupted all active child processes",
                        ),
                        ("STEP_FAILURE", 'Execution of step "sleepy_solid" failed.'),
                        (
                            "PIPELINE_CANCELED",
                            'Execution of pipeline "sleepy_pipeline" canceled.',
                        ),
                        ("ENGINE_EVENT", "Process for pipeline exited"),
                    ],
                )
            else:
                _check_event_log_contains(
                    run_logs,
                    [
                        ("PIPELINE_CANCELING", "Sending pipeline termination request."),
                        ("STEP_FAILURE", 'Execution of step "sleepy_solid" failed.'),
                        (
                            "PIPELINE_CANCELED",
                            'Execution of pipeline "sleepy_pipeline" canceled.',
                        ),
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
    "get_workspace",
    [
        get_deployed_grpc_server_workspace,
        get_managed_grpc_server_workspace,
    ],
)
@pytest.mark.parametrize(
    "run_config",
    run_configs(),
)
def test_single_solid_selection_execution(
    get_workspace,
    run_config,
):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        with get_workspace(instance) as workspace:
            external_pipeline = (
                workspace.get_repository_location("test")
                .get_repository("nope")
                .get_full_external_pipeline("math_diamond")
            )
            pipeline_run = instance.create_run_for_pipeline(
                pipeline_def=math_diamond,
                run_config=run_config,
                solids_to_execute={"return_one"},
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )
            run_id = pipeline_run.run_id

            assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

            instance.launch_run(pipeline_run.run_id, workspace)
            finished_pipeline_run = poll_for_finished_run(instance, run_id)

            event_records = instance.all_logs(run_id)

            assert finished_pipeline_run
            assert finished_pipeline_run.run_id == run_id
            assert finished_pipeline_run.status == PipelineRunStatus.SUCCESS

            assert _get_successful_step_keys(event_records) == {"return_one"}


@pytest.mark.parametrize(
    "get_workspace",
    [
        get_deployed_grpc_server_workspace,
        get_managed_grpc_server_workspace,
    ],
)
@pytest.mark.parametrize(
    "run_config",
    run_configs(),
)
def test_multi_solid_selection_execution(
    get_workspace,
    run_config,
):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        with get_workspace(instance) as workspace:
            external_pipeline = (
                workspace.get_repository_location("test")
                .get_repository("nope")
                .get_full_external_pipeline("math_diamond")
            )

            pipeline_run = instance.create_run_for_pipeline(
                pipeline_def=math_diamond,
                run_config=run_config,
                solids_to_execute={"return_one", "multiply_by_2"},
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )
            run_id = pipeline_run.run_id

            assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

            instance.launch_run(pipeline_run.run_id, workspace)
            finished_pipeline_run = poll_for_finished_run(instance, run_id)

            event_records = instance.all_logs(run_id)

            assert finished_pipeline_run
            assert finished_pipeline_run.run_id == run_id
            assert finished_pipeline_run.status == PipelineRunStatus.SUCCESS

            assert _get_successful_step_keys(event_records) == {
                "return_one",
                "multiply_by_2",
            }


@pytest.mark.parametrize(
    "get_workspace",
    [
        get_deployed_grpc_server_workspace,
        get_managed_grpc_server_workspace,
    ],
)
@pytest.mark.parametrize(
    "run_config",
    run_configs(),
)
def test_engine_events(get_workspace, run_config):  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        with get_workspace(instance) as workspace:
            external_pipeline = (
                workspace.get_repository_location("test")
                .get_repository("nope")
                .get_full_external_pipeline("math_diamond")
            )
            pipeline_run = instance.create_run_for_pipeline(
                pipeline_def=math_diamond,
                run_config=run_config,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )
            run_id = pipeline_run.run_id

            assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

            instance.launch_run(pipeline_run.run_id, workspace)
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
                    "Launching subprocess for return_one",
                    "Executing step return_one in subprocess",
                    "Starting initialization of resources",
                    "Finished initialization of resources",
                    # multiply_by_2 and multiply_by_3 launch and execute in non-deterministic order
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "Launching subprocess for add",
                    "Executing step add in subprocess",
                    "Starting initialization of resources",
                    "Finished initialization of resources",
                    "Multiprocess executor: parent process exiting",
                    "Process for pipeline exited",
                ]
            else:
                messages = [
                    "Started process for pipeline",
                    "Executing steps in process",
                    "Starting initialization of resources",
                    "Finished initialization of resources",
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
