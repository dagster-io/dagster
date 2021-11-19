import contextlib

from dagster import seven
from dagster.serdes.ipc import interrupt_ipc_subprocess, open_ipc_subprocess


@contextlib.contextmanager
def start_daemon(timeout=60):
    p = open_ipc_subprocess(["dagster-daemon", "run"])
    try:
        yield
    finally:
        interrupt_ipc_subprocess(p)
        seven.wait_for_process(p, timeout=timeout)
