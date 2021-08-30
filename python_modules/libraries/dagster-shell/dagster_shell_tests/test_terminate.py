import time
from contextlib import contextmanager

import psutil
from dagster import pipeline, repository, solid
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import instance_for_test, poll_for_finished_run, poll_for_step_start
from dagster.core.workspace import WorkspaceProcessContext
from dagster.core.workspace.load_target import PythonFileTarget
from dagster.utils import file_relative_path
from dagster_shell.utils import execute


@solid
def sleepy_solid(context):
    # execute a sleep in the background
    execute("sleep 60", "NONE", context.log)


@pipeline
def sleepy_pipeline():
    sleepy_solid()


@repository
def sleepy_repo():
    return [sleepy_pipeline]


@contextmanager
def get_managed_grpc_server_workspace(instance):
    with WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=file_relative_path(__file__, "test_terminate.py"),
            attribute="sleepy_repo",
            working_directory=None,
            location_name="test",
        ),
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


def poll_for_pid(instance, run_id, timeout=20):
    total_time = 0
    interval = 0.1

    while total_time < timeout:
        logs = instance.all_logs(run_id)

        pid_log = next(
            (log.user_message for log in logs if log.user_message.startswith("Command pid:")), None
        )
        if pid_log is not None:
            return int(pid_log.split(" ")[-1])
        else:
            time.sleep(interval)
            total_time += interval
            if total_time > timeout:
                raise Exception("Timed out")


def test_terminate_kills_subproc():
    with instance_for_test() as instance:
        with get_managed_grpc_server_workspace(instance) as workspace:
            external_pipeline = (
                workspace.get_repository_location("test")
                .get_repository("sleepy_repo")
                .get_full_external_pipeline("sleepy_pipeline")
            )
            pipeline_run = instance.create_run_for_pipeline(
                pipeline_def=sleepy_pipeline,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )

            run_id = pipeline_run.run_id

            assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

            instance.launch_run(pipeline_run.run_id, workspace)

            poll_for_step_start(instance, run_id)

            # find pid of subprocess
            subproc_pid = poll_for_pid(instance, run_id)
            assert psutil.pid_exists(subproc_pid)

            # simulate waiting a bit to terminate the pipeline
            time.sleep(0.5)

            launcher = instance.run_launcher
            assert launcher.can_terminate(run_id)
            assert launcher.terminate(run_id)

            terminated_pipeline_run = poll_for_finished_run(instance, run_id, timeout=30)
            terminated_pipeline_run = instance.get_run_by_id(run_id)
            assert terminated_pipeline_run.status == PipelineRunStatus.CANCELED

            # make sure the subprocess is killed after a short delay
            time.sleep(0.5)
            assert not psutil.pid_exists(subproc_pid)
