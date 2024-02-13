import contextlib

from dagster import _seven
from dagster._serdes.ipc import interrupt_ipc_subprocess, open_ipc_subprocess


@contextlib.contextmanager
def start_daemon(timeout=60, workspace_file=None, log_level=None):
    p = open_ipc_subprocess(
        ["dagster-daemon", "run"]
        + (["--python-file", workspace_file] if workspace_file else ["--empty-workspace"])
        + (["--log-level", log_level] if log_level else [])
    )
    try:
        yield
    finally:
        interrupt_ipc_subprocess(p)
        _seven.wait_for_process(p, timeout=timeout)
