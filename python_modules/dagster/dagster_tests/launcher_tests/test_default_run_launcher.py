import json
import os
import re
import sys
import tempfile
import time
from typing import Any, Mapping

import pytest
from dagster import (
    Config,
    DagsterEvent,
    DagsterEventType,
    DefaultRunLauncher,
    Output,
    RetryPolicy,
    _check as check,
    _seven,
    file_relative_path,
    repository,
)
from dagster._core.definitions import op
from dagster._core.errors import DagsterExecutionInterruptedError, DagsterLaunchFailedError
from dagster._core.execution.plan.objects import StepSuccessData
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import GRPC_INFO_TAG
from dagster._core.test_utils import (
    environ,
    instance_for_test,
    poll_for_event,
    poll_for_finished_run,
    poll_for_step_start,
)
from dagster._core.utils import make_new_run_id
from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster._core.workspace.load_target import PythonFileTarget
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.types import CancelExecutionRequest


@op
def noop_op(_):
    pass


from dagster import job


@job
def noop_job():
    pass


@op(
    retry_policy=RetryPolicy(
        max_retries=2,
    )
)
def crashy_op(_):
    os._exit(1)


@job
def crashy_job():
    crashy_op()


@op
def exity_op(_):
    sys.exit(1)


@job
def exity_job():
    exity_op()


class SleepyOpConfig(Config):
    raise_keyboard_interrupt: bool = False
    crash_after_termination: bool = False


@op
def sleepy_op(config: SleepyOpConfig):
    assert not (config.raise_keyboard_interrupt and config.crash_after_termination)

    while True:
        try:
            time.sleep(0.1)

        except DagsterExecutionInterruptedError:
            if config.raise_keyboard_interrupt:
                # simulates a custom signal handler that has overridden ours
                # to raise a normal KeyboardInterrupt
                raise KeyboardInterrupt
            elif config.crash_after_termination:
                # simulates a crash after termination was initiated
                os._exit(1)
            else:
                raise


@job
def sleepy_job():
    sleepy_op()


@op
def slow_sudop(_):
    time.sleep(4)


@job
def slow_job():
    slow_sudop()


@op
def return_one(_):
    return 1


@op
def multiply_by_2(_, num):
    return num * 2


@op
def multiply_by_3(_, num):
    return num * 3


@op
def add(_, num1, num2):
    return num1 + num2


@op
def op_that_emits_duplicate_step_success_event(context):
    # emits a duplicate step success event which will mess up the execution
    # machinery and fail the run worker

    # Wait for the other op to start so that it will be terminated mid-execution
    poll_for_step_start(context.instance, context.dagster_run.run_id, message="sleepy_op")

    yield DagsterEvent.step_success_event(
        context._step_execution_context,  # noqa
        StepSuccessData(duration_ms=50.0),
    )
    yield Output(5)


@job
def job_that_fails_run_worker():
    sleepy_op()
    op_that_emits_duplicate_step_success_event()


@job
def math_diamond():
    one = return_one()
    add(multiply_by_2(one), multiply_by_3(one))


@repository
def nope():
    return [
        noop_job,
        crashy_job,
        exity_job,
        sleepy_job,
        slow_job,
        math_diamond,
        job_that_fails_run_worker,
    ]


def run_configs():
    return [
        None,
        {"execution": {"config": {"in_process": {}}}},
    ]


def _check_event_log_contains(event_log, expected_type_and_message):
    types_and_messages = [
        (e.dagster_event.event_type_value, e.message) for e in event_log if e.is_dagster_event
    ]
    for expected_event_type, expected_message_fragment in expected_type_and_message:
        assert any(
            event_type == expected_event_type and expected_message_fragment in message
            for event_type, message in types_and_messages
        ), f"Missing {expected_event_type}:{expected_message_fragment}"


@pytest.mark.parametrize(
    "run_config",
    run_configs(),
)
def test_successful_run(
    instance: DagsterInstance,
    workspace: WorkspaceRequestContext,
    run_config: Mapping[str, Any],
):
    remote_job = workspace.get_code_location("test").get_repository("nope").get_full_job("noop_job")

    dagster_run = instance.create_run_for_job(
        job_def=noop_job,
        run_config=run_config,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )
    run_id = dagster_run.run_id

    run = instance.get_run_by_id(run_id)
    assert run
    assert run.status == DagsterRunStatus.NOT_STARTED

    instance.launch_run(run_id=dagster_run.run_id, workspace=workspace)

    dagster_run = instance.get_run_by_id(run_id)
    assert dagster_run
    assert dagster_run.run_id == run_id

    dagster_run = poll_for_finished_run(instance, run_id)
    assert dagster_run.status == DagsterRunStatus.SUCCESS


def test_successful_run_from_pending(
    instance: DagsterInstance, pending_workspace: WorkspaceRequestContext
):
    run_id = make_new_run_id()
    code_location = pending_workspace.get_code_location("test2")
    remote_job = code_location.get_repository("pending").get_full_job("my_cool_asset_job")
    external_execution_plan = code_location.get_external_execution_plan(
        remote_job=remote_job,
        run_config={},
        step_keys_to_execute=None,
        known_state=None,
    )

    call_counts = instance.run_storage.get_cursor_values(
        {
            "compute_cacheable_data_called_a",
            "compute_cacheable_data_called_b",
            "get_definitions_called_a",
            "get_definitions_called_b",
        }
    )
    assert call_counts.get("compute_cacheable_data_called_a") == "1"
    assert call_counts.get("compute_cacheable_data_called_b") == "1"
    assert call_counts.get("get_definitions_called_a") == "1"
    assert call_counts.get("get_definitions_called_b") == "1"

    created_run = instance.create_run(
        job_name="my_cool_asset_job",
        run_id=run_id,
        run_config=None,
        resolved_op_selection=None,
        step_keys_to_execute=None,
        status=None,
        tags=None,
        root_run_id=None,
        parent_run_id=None,
        job_snapshot=remote_job.job_snapshot,
        execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
        parent_job_snapshot=remote_job.parent_job_snapshot,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
        asset_selection=None,
        op_selection=None,
        asset_check_selection=None,
        asset_graph=code_location.get_repository(
            remote_job.repository_handle.repository_name
        ).asset_graph,
    )

    run_id = created_run.run_id

    assert check.not_none(instance.get_run_by_id(run_id)).status == DagsterRunStatus.NOT_STARTED

    instance.launch_run(run_id=run_id, workspace=pending_workspace)

    stored_run = check.not_none(instance.get_run_by_id(run_id))
    assert created_run.run_id == stored_run.run_id
    assert created_run.execution_plan_snapshot_id == stored_run.execution_plan_snapshot_id
    assert created_run.has_repository_load_data and stored_run.has_repository_load_data

    finished_run = poll_for_finished_run(instance, run_id)
    assert finished_run.status == DagsterRunStatus.SUCCESS

    call_counts = instance.run_storage.get_cursor_values(
        {
            "compute_cacheable_data_called_a",
            "compute_cacheable_data_called_b",
            "get_definitions_called_a",
            "get_definitions_called_b",
        }
    )
    assert call_counts.get("compute_cacheable_data_called_a") == "1"
    assert call_counts.get("compute_cacheable_data_called_b") == "1"
    # once at initial load time, once inside the run launch process, once for each (3) subprocess
    # upper bound of 5 here because race conditions result in lower count sometimes
    assert int(call_counts["get_definitions_called_a"]) < 6
    assert int(call_counts["get_definitions_called_b"]) < 6


def test_invalid_instance_run():
    with tempfile.TemporaryDirectory() as temp_dir:
        correct_run_storage_dir = os.path.join(temp_dir, "history", "")
        wrong_run_storage_dir = os.path.join(temp_dir, "wrong", "")

        with environ({"RUN_STORAGE_ENV": correct_run_storage_dir}):
            with instance_for_test(
                temp_dir=temp_dir,
                overrides={
                    "run_storage": {
                        "module": "dagster._core.storage.runs",
                        "class": "SqliteRunStorage",
                        "config": {"base_dir": {"env": "RUN_STORAGE_ENV"}},
                    }
                },
            ) as instance:
                # Server won't be able to load the run from run storage
                with environ({"RUN_STORAGE_ENV": wrong_run_storage_dir}):
                    with WorkspaceProcessContext(
                        instance,
                        PythonFileTarget(
                            python_file=file_relative_path(
                                __file__, "test_default_run_launcher.py"
                            ),
                            attribute="nope",
                            working_directory=None,
                            location_name="test",
                        ),
                    ) as workspace_process_context:
                        workspace = workspace_process_context.create_request_context()
                        remote_job = (
                            workspace.get_code_location("test")
                            .get_repository("nope")
                            .get_full_job("noop_job")
                        )

                        run = instance.create_run_for_job(
                            job_def=noop_job,
                            remote_job_origin=remote_job.get_remote_origin(),
                            job_code_origin=remote_job.get_python_origin(),
                        )
                        with pytest.raises(
                            DagsterLaunchFailedError,
                            match=re.escape(
                                f"gRPC server could not load run {run.run_id} in order to execute it"
                            ),
                        ):
                            instance.launch_run(run_id=run.run_id, workspace=workspace)

                        failed_run = instance.get_run_by_id(run.run_id)
                        assert failed_run.status == DagsterRunStatus.FAILURE


@pytest.mark.parametrize(
    "run_config",
    run_configs(),
)
@pytest.mark.skipif(
    _seven.IS_WINDOWS,
    reason="Crashy jobs leave resources open on windows, causing filesystem contention",
)
def test_crashy_run(
    instance: DagsterInstance,
    workspace: WorkspaceRequestContext,
    run_config: Mapping[str, Any],
):
    remote_job = (
        workspace.get_code_location("test").get_repository("nope").get_full_job("crashy_job")
    )

    run = instance.create_run_for_job(
        job_def=crashy_job,
        run_config=run_config,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )

    run_id = run.run_id

    run = instance.get_run_by_id(run_id)
    assert run
    assert run.status == DagsterRunStatus.NOT_STARTED

    instance.launch_run(run.run_id, workspace)

    failed_run = instance.get_run_by_id(run_id)

    assert failed_run
    assert failed_run.run_id == run_id

    failed_run = poll_for_finished_run(instance, run_id, timeout=5)
    assert failed_run.status == DagsterRunStatus.FAILURE

    event_records = instance.all_logs(run_id)

    if run_config is None:
        message = "Multiprocess executor: child process for step crashy_op unexpectedly exited"
    else:
        message = f"Run execution process for {run_id} unexpectedly exited"

    assert _message_exists(event_records, message)

    if run_config is None:
        # verify the step retried once before failing
        run_logs = instance.all_logs(run_id)
        _check_event_log_contains(
            run_logs,
            [
                (
                    "STEP_UP_FOR_RETRY",
                    'Execution of step "crashy_op" failed and has requested a retry.',
                ),
                (
                    "STEP_RESTARTED",
                    'Started re-execution (attempt # 2) of step "crashy_op"',
                ),
                (
                    "ENGINE_EVENT",
                    "Multiprocess executor: child process for step crashy_op unexpectedly exited",
                ),
                (
                    "STEP_UP_FOR_RETRY",
                    'Execution of step "crashy_op" failed and has requested a retry.',
                ),
                (
                    "STEP_RESTARTED",
                    'Started re-execution (attempt # 3) of step "crashy_op"',
                ),
                (
                    "STEP_FAILURE",
                    'Execution of step "crashy_op" failed.',
                ),
            ],
        )


@pytest.mark.parametrize("run_config", run_configs())
@pytest.mark.skipif(
    _seven.IS_WINDOWS,
    reason="Crashy jobs leave resources open on windows, causing filesystem contention",
)
def test_exity_run(
    instance: DagsterInstance,
    workspace: WorkspaceRequestContext,
    run_config: Mapping[str, Any],
):
    remote_job = (
        workspace.get_code_location("test").get_repository("nope").get_full_job("exity_job")
    )

    run = instance.create_run_for_job(
        job_def=exity_job,
        run_config=run_config,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )

    run_id = run.run_id

    run = instance.get_run_by_id(run_id)
    assert run
    assert run.status == DagsterRunStatus.NOT_STARTED

    instance.launch_run(run.run_id, workspace)

    failed_run = instance.get_run_by_id(run_id)

    assert failed_run
    assert failed_run.run_id == run_id

    failed_run = poll_for_finished_run(instance, run_id, timeout=5)
    assert failed_run.status == DagsterRunStatus.FAILURE

    event_records = instance.all_logs(run_id)

    assert _message_exists(event_records, 'Execution of step "exity_op" failed.')
    assert _message_exists(
        event_records,
        "Execution of run for \"exity_job\" failed. Steps failed: ['exity_op']",
    )


@pytest.mark.parametrize(
    "run_config",
    [
        None,  # multiprocess
        {"execution": {"config": {"in_process": {}}}},  # in-process
        {  # raise KeyboardInterrupt on termination
            "ops": {"sleepy_op": {"config": {"raise_keyboard_interrupt": True}}}
        },
        pytest.param(
            {  # crash on termination
                "ops": {"sleepy_op": {"config": {"crash_after_termination": True}}}
            },
            marks=pytest.mark.skipif(
                _seven.IS_WINDOWS, reason="Crashes manifest differently on windows"
            ),
        ),
    ],
)
def test_terminated_run(
    instance: DagsterInstance,
    workspace: WorkspaceRequestContext,
    run_config: Mapping[str, Any],
):
    remote_job = (
        workspace.get_code_location("test").get_repository("nope").get_full_job("sleepy_job")
    )
    run = instance.create_run_for_job(
        job_def=sleepy_job,
        run_config=run_config,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )

    run_id = run.run_id

    run = instance.get_run_by_id(run_id)
    assert run and run.status == DagsterRunStatus.NOT_STARTED

    instance.launch_run(run.run_id, workspace)

    poll_for_step_start(instance, run_id)

    launcher = instance.run_launcher
    assert launcher.terminate(run_id)

    terminated_run = poll_for_finished_run(instance, run_id, timeout=30)
    terminated_run = instance.get_run_by_id(run_id)
    assert terminated_run and terminated_run.status == DagsterRunStatus.CANCELED

    # termination is a no-op once run is finished
    assert not launcher.terminate(run_id)

    poll_for_event(
        instance,
        run_id,
        event_type="ENGINE_EVENT",
        message="Process for run exited",
    )

    run_logs = instance.all_logs(run_id)

    if run_config is None:  # multiprocess
        _check_event_log_contains(
            run_logs,
            [
                ("PIPELINE_CANCELING", "Sending run termination request."),
                (
                    "ENGINE_EVENT",
                    (
                        "Multiprocess executor: received termination signal - forwarding to active"
                        " child process"
                    ),
                ),
                (
                    "ENGINE_EVENT",
                    "Multiprocess executor: interrupted all active child processes",
                ),
                ("STEP_FAILURE", 'Execution of step "sleepy_op" failed.'),
                (
                    "PIPELINE_CANCELED",
                    'Execution of run for "sleepy_job" canceled.',
                ),
                ("ENGINE_EVENT", "Process for run exited"),
            ],
        )
    elif (
        run_config.get("ops", {})
        .get("sleepy_op", {})
        .get("config", {})
        .get("crash_after_termination")
    ):
        _check_event_log_contains(
            run_logs,
            [
                ("PIPELINE_CANCELING", "Sending run termination request."),
                ("STEP_FAILURE", 'Execution of step "sleepy_op" failed.'),
                (
                    "PIPELINE_CANCELED",
                    "Run failed after it was requested to be terminated.",
                ),
                ("ENGINE_EVENT", "Process for run exited"),
            ],
        )
    else:
        _check_event_log_contains(
            run_logs,
            [
                ("PIPELINE_CANCELING", "Sending run termination request."),
                ("STEP_FAILURE", 'Execution of step "sleepy_op" failed.'),
                (
                    "PIPELINE_CANCELED",
                    'Execution of run for "sleepy_job" canceled.',
                ),
                ("ENGINE_EVENT", "Process for run exited"),
            ],
        )


@pytest.mark.parametrize("run_config", run_configs())
def test_cleanup_after_force_terminate(
    instance: DagsterInstance,
    workspace: WorkspaceRequestContext,
    run_config: Mapping[str, Any],
):
    remote_job = (
        workspace.get_code_location("test").get_repository("nope").get_full_job("sleepy_job")
    )
    run = instance.create_run_for_job(
        job_def=sleepy_job,
        run_config=run_config,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )

    run_id = run.run_id

    instance.launch_run(run.run_id, workspace)

    poll_for_step_start(instance, run_id)

    # simulate the sequence of events that happen during force-termination:
    # run moves immediately into canceled status while termination happens
    instance.report_run_canceling(run)

    instance.report_run_canceled(run)

    reloaded_run = instance.get_run_by_id(run_id)
    assert reloaded_run
    grpc_info = json.loads(reloaded_run.tags[GRPC_INFO_TAG])
    client = DagsterGrpcClient(
        port=grpc_info.get("port"),
        socket=grpc_info.get("socket"),
        host=grpc_info.get("host"),
    )
    client.cancel_execution(CancelExecutionRequest(run_id=run_id))

    # Wait for the run worker to clean up
    start_time = time.time()
    while True:
        if time.time() - start_time > 30:
            raise Exception("Timed out waiting for cleanup message")

        logs = instance.all_logs(run_id)
        if any(
            [
                "Computational resources were cleaned up after the run was forcibly marked as"
                " canceled." in str(event)
                for event in logs
            ]
        ):
            break

        time.sleep(1)

    run = instance.get_run_by_id(run_id)
    assert run and run.status == DagsterRunStatus.CANCELED


def _get_engine_events(event_records):
    return [
        er
        for er in event_records
        if er.dagster_event
        and er.dagster_event.event_type
        in {
            DagsterEventType.ENGINE_EVENT,
            DagsterEventType.STEP_WORKER_STARTING,
            DagsterEventType.STEP_WORKER_STARTED,
            DagsterEventType.RESOURCE_INIT_STARTED,
            DagsterEventType.RESOURCE_INIT_SUCCESS,
            DagsterEventType.RESOURCE_INIT_FAILURE,
        }
    ]


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
    "run_config",
    run_configs(),
)
def test_single_op_selection_execution(
    instance: DagsterInstance,
    workspace: WorkspaceRequestContext,
    run_config: Mapping[str, Any],
):
    remote_job = (
        workspace.get_code_location("test").get_repository("nope").get_full_job("math_diamond")
    )
    run = instance.create_run_for_job(
        job_def=math_diamond,
        run_config=run_config,
        op_selection=["return_one"],
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )
    run_id = run.run_id

    run = instance.get_run_by_id(run_id)
    assert run and run.status == DagsterRunStatus.NOT_STARTED

    instance.launch_run(run.run_id, workspace)
    finished_run = poll_for_finished_run(instance, run_id)

    event_records = instance.all_logs(run_id)

    assert finished_run
    assert finished_run.run_id == run_id
    assert finished_run.status == DagsterRunStatus.SUCCESS

    assert _get_successful_step_keys(event_records) == {"return_one"}


@pytest.mark.parametrize(
    "run_config",
    run_configs(),
)
def test_multi_op_selection_execution(
    instance: DagsterInstance,
    workspace: WorkspaceRequestContext,
    run_config: Mapping[str, Any],
):
    remote_job = (
        workspace.get_code_location("test").get_repository("nope").get_full_job("math_diamond")
    )

    run = instance.create_run_for_job(
        job_def=math_diamond,
        run_config=run_config,
        op_selection=["return_one", "multiply_by_2"],
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )
    run_id = run.run_id

    run = instance.get_run_by_id(run_id)
    assert run and run.status == DagsterRunStatus.NOT_STARTED

    instance.launch_run(run.run_id, workspace)
    finished_run = poll_for_finished_run(instance, run_id)

    event_records = instance.all_logs(run_id)

    assert finished_run
    assert finished_run.run_id == run_id
    assert finished_run.status == DagsterRunStatus.SUCCESS

    assert _get_successful_step_keys(event_records) == {
        "return_one",
        "multiply_by_2",
    }


@pytest.mark.skipif(
    _seven.IS_WINDOWS,
    reason="Failure sequence manifests differently on windows",
)
def test_job_that_fails_run_worker(
    instance: DagsterInstance,
    workspace: WorkspaceRequestContext,
):
    remote_job = (
        workspace.get_code_location("test")
        .get_repository("nope")
        .get_full_job("job_that_fails_run_worker")
    )
    run = instance.create_run_for_job(
        job_def=job_that_fails_run_worker,
        run_config={},
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )
    run_id = run.run_id

    run = instance.get_run_by_id(run_id)
    assert run and run.status == DagsterRunStatus.NOT_STARTED

    instance.launch_run(run.run_id, workspace)
    finished_run = poll_for_finished_run(instance, run_id)
    assert finished_run.status == DagsterRunStatus.FAILURE

    run_logs = instance.all_logs(run_id)
    _check_event_log_contains(
        run_logs,
        [
            (
                "ENGINE_EVENT",
                "Unexpected exception while steps were still in-progress - terminating running steps:",
            ),
            (
                "STEP_FAILURE",
                'Execution of step "sleepy_op" failed.',
            ),
            (
                "PIPELINE_FAILURE",
                'Execution of run for "job_that_fails_run_worker" failed. An exception was thrown during execution.',
            ),
        ],
    )


@pytest.mark.parametrize(
    "run_config",
    run_configs(),
)
def test_engine_events(
    instance: DagsterInstance,
    workspace: WorkspaceRequestContext,
    run_config: Mapping[str, Any],
):
    remote_job = (
        workspace.get_code_location("test").get_repository("nope").get_full_job("math_diamond")
    )
    run = instance.create_run_for_job(
        job_def=math_diamond,
        run_config=run_config,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
    )
    run_id = run.run_id

    run = instance.get_run_by_id(run_id)
    assert run and run.status == DagsterRunStatus.NOT_STARTED

    instance.launch_run(run.run_id, workspace)
    finished_run = poll_for_finished_run(instance, run_id)

    assert finished_run
    assert finished_run.run_id == run_id
    assert finished_run.status == DagsterRunStatus.SUCCESS

    poll_for_event(
        instance,
        run_id,
        event_type="ENGINE_EVENT",
        message="Process for run exited",
    )
    event_records = instance.all_logs(run_id)

    engine_events = _get_engine_events(event_records)

    if run_config is None:  # multiprocess
        messages = [
            "Started process for run",
            "Executing steps using multiprocess executor",
            'Launching subprocess for "return_one"',
            'Executing step "return_one" in subprocess.',
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
            'Launching subprocess for "add"',
            'Executing step "add" in subprocess',
            "Starting initialization of resources",
            "Finished initialization of resources",
            "Multiprocess executor: parent process exiting",
            "Process for run exited",
        ]
    else:
        messages = [
            "Started process for run",
            "Executing steps in process",
            "Starting initialization of resources",
            "Finished initialization of resources",
            "Finished steps in process",
            "Process for run exited",
        ]

    events_iter = iter(engine_events)
    assert len(engine_events) == len(messages)

    for message in messages:
        next_log = next(events_iter)
        assert message in next_log.message


def test_not_initialized():
    run_launcher = DefaultRunLauncher()
    run_id = make_new_run_id()

    assert run_launcher.join() is None
    assert run_launcher.terminate(run_id) is False
