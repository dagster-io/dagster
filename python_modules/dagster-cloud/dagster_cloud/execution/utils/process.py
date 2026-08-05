import os
import sys
from collections.abc import Sequence

from dagster_shared.ipc import interrupt_ipc_subprocess_pid, open_ipc_subprocess

from dagster_cloud.execution.utils import TaskStatus


def launch_process(args: Sequence[str]) -> int:
    """Launch a process and return the PID."""
    p = open_ipc_subprocess(args)
    pid = p.pid
    return pid


def check_on_process(pid: int) -> TaskStatus:
    # TODO: implement cross platform process check
    if sys.platform == "win32":
        return TaskStatus.NOT_IMPLEMENTED
    else:
        try:
            # Send a no-op. If the process is not running, it will respond with an error
            # https://stackoverflow.com/a/568285/14656695
            os.kill(pid, 0)
        except OSError:
            return TaskStatus.NOT_FOUND
        else:
            return TaskStatus.RUNNING


def kill_process(pid: int):
    interrupt_ipc_subprocess_pid(pid)
