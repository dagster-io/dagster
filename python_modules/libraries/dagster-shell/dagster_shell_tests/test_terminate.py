import time
from contextlib import contextmanager

import psutil
from dagster import job, op, repository
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import instance_for_test, poll_for_finished_run, poll_for_step_start
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import PythonFileTarget
from dagster._utils import file_relative_path
from dagster_shell.utils import execute


@op
def sleepy_op(context):
    # execute a sleep in the background
    execute("sleep 60", "NONE", context.log)


@job
def sleepy_job():
    sleepy_op()


@repository
def sleepy_repo():
    return [sleepy_job]


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
            remote_job = (
                workspace.get_code_location("test")
                .get_repository("sleepy_repo")
                .get_full_job("sleepy_job")
            )
            dagster_run = instance.create_run_for_job(
                job_def=sleepy_job,
                remote_job_origin=remote_job.get_remote_origin(),
                job_code_origin=remote_job.get_python_origin(),
            )

            run_id = dagster_run.run_id

            assert instance.get_run_by_id(run_id).status == DagsterRunStatus.NOT_STARTED

            instance.launch_run(dagster_run.run_id, workspace)

            poll_for_step_start(instance, run_id)

            # find pid of subprocess
            subproc_pid = poll_for_pid(instance, run_id)
            assert psutil.pid_exists(subproc_pid)

            # simulate waiting a bit to terminate the job
            time.sleep(0.5)

            launcher = instance.run_launcher
            assert launcher.terminate(run_id)

            terminated_dagster_run = poll_for_finished_run(instance, run_id, timeout=30)
            terminated_dagster_run = instance.get_run_by_id(run_id)
            assert terminated_dagster_run.status == DagsterRunStatus.CANCELED

            # make sure the subprocess is killed after a short delay
            time.sleep(0.5)
            assert not psutil.pid_exists(subproc_pid)
