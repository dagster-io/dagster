import os
import subprocess
import sys
import time
from typing import Any

import psutil
from dagster._utils.interrupts import setup_interrupt_handlers
from dagster_shared.ipc import (
    get_ipc_shutdown_pipe,
    interrupt_on_ipc_shutdown_message,
    open_ipc_subprocess,
    send_ipc_shutdown_message,
)

_PROCESS_DEPTH = 20


def test_shutdown_pipe():
    proc, write_fd = _run_script(_PROCESS_DEPTH, stdout=subprocess.PIPE, text=True, bufsize=1)
    _wait_for_processes_to_start(proc)
    child_procs = psutil.Process(proc.pid).children(recursive=True)
    send_ipc_shutdown_message(write_fd)
    proc.wait(timeout=10)
    assert proc.stdout
    output = proc.stdout.read()
    for i in range(_PROCESS_DEPTH):
        assert f"({i}) Keyboard interrupt received" in output

    # Make sure all child processes are terminated
    for child_proc in child_procs:
        try:
            assert not child_proc.is_running()
        except psutil.NoSuchProcess:
            pass


def _wait_for_processes_to_start(proc: subprocess.Popen[str]):
    assert proc.stdout
    for line in iter(proc.stdout.readline, ""):
        print(line.strip())  # noqa: T201
        if "(0) Started" in line:
            break


def _run_script(counter: int, **proc_kwargs: Any) -> tuple[subprocess.Popen, int]:
    read_fd, write_fd = get_ipc_shutdown_pipe()
    proc = open_ipc_subprocess(
        # Use -u to force unbuffered output
        [sys.executable, "-u", __file__, str(read_fd)],
        pass_fds=[read_fd],
        env={**os.environ, "DAGSTER_TEST_COUNTER": str(counter)},
        **proc_kwargs,
    )
    return proc, write_fd


def main(counter: int, shutdown_pipe_fd: int):
    setup_interrupt_handlers()
    proc, write_fd = _run_script(counter - 1) if counter > 0 else (None, None)
    with interrupt_on_ipc_shutdown_message(shutdown_pipe_fd):
        print(f"({counter}) Started")  # noqa: T201
        try:
            while True:
                time.sleep(0.01)
        except KeyboardInterrupt:
            print(f"({counter}) Keyboard interrupt received")  # noqa: T201
            if proc and write_fd:
                send_ipc_shutdown_message(write_fd)
                proc.wait(timeout=10)
            print(f"({counter}) Exiting")  # noqa: T201


if __name__ == "__main__":
    counter = int(os.environ["DAGSTER_TEST_COUNTER"])
    shutdown_pipe_fd = int(sys.argv[1])
    main(counter, shutdown_pipe_fd)
