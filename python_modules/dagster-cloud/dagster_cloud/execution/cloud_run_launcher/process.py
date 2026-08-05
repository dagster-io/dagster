import os
import time

import dagster._check as check
from dagster._core.launcher import RunLauncher
from dagster._core.launcher.base import LaunchRunContext
from dagster._core.utils import parse_env_var
from dagster._grpc.types import ExecuteRunArgs
from dagster_shared.ipc import open_ipc_subprocess

from dagster_cloud.execution.utils import TaskStatus
from dagster_cloud.execution.utils.process import check_on_process, kill_process
from dagster_cloud.workspace.user_code_launcher.utils import get_instance_ref_for_user_code

PID_TAG = "process/pid"


class CloudProcessRunLauncher(RunLauncher):
    def __init__(self):
        self._run_ids = set()
        super().__init__()

    def launch_run(self, context: LaunchRunContext) -> None:
        run = context.dagster_run
        pipeline_code_origin = check.not_none(context.job_code_origin)

        run_args = ExecuteRunArgs(
            job_origin=pipeline_code_origin,
            run_id=run.run_id,
            instance_ref=get_instance_ref_for_user_code(self._instance.get_ref()),
        )
        args = run_args.get_command_args()

        kwargs = {}
        if (
            run.job_code_origin
            and run.job_code_origin.repository_origin.container_context
            and run.job_code_origin.repository_origin.container_context.get("env_vars")
        ):
            kwargs["env"] = {**os.environ}
            for kev in run.job_code_origin.repository_origin.container_context["env_vars"]:
                key, value = parse_env_var(kev)
                kwargs["env"][key] = value

        p = open_ipc_subprocess(args, **kwargs)
        pid = p.pid

        self._run_ids.add(run.run_id)

        self._instance.add_run_tags(run.run_id, {PID_TAG: str(pid)})

    def join(self, timeout=30):
        total_time = 0
        interval = 0.01

        while True:
            active_run_ids = [
                run_id
                for run_id in self._run_ids
                if (
                    self._instance.get_run_by_id(run_id)
                    and not self._instance.get_run_by_id(run_id).is_finished  # ty: ignore[unresolved-attribute]
                )
            ]

            if len(active_run_ids) == 0:
                return

            if total_time >= timeout:
                raise Exception(f"Timed out waiting for these runs to finish: {active_run_ids!r}")

            total_time += interval
            time.sleep(interval)
            interval = interval * 2

    def _get_pid(self, run):
        if not run or run.is_finished:
            return None

        tags = run.tags

        if PID_TAG not in tags:
            return None

        return int(tags[PID_TAG])

    def can_terminate(self, run_id):
        run = self._instance.get_run_by_id(run_id)
        if not run:
            return False

        pid = self._get_pid(run)
        if not pid:
            return False

        return check_on_process(pid) == TaskStatus.RUNNING

    def terminate(self, run_id):
        run = self._instance.get_run_by_id(run_id)
        if not run or run.is_finished:
            return False

        self._instance.report_run_canceling(run)

        pid = self._get_pid(run)
        if not pid:
            return False

        kill_process(pid)

        return True
