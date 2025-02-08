import signal
import subprocess
import tempfile
import time
from collections import deque

import pytest
import requests
from dagster import (
    _seven as seven,
    job,
    op,
)
from dagster._core.test_utils import environ, new_cwd
from dagster._utils import find_free_port


def _wait_for_dagit_running(dagit_port):
    start_time = time.time()
    while True:
        try:
            dagit_json = requests.get(f"http://localhost:{dagit_port}/server_info").json()
            if dagit_json:
                return
        except:
            print("Waiting for Dagit to be ready..")  # noqa: T201

        if time.time() - start_time > 30:
            raise Exception("Timed out waiting for Dagit to serve requests")

        time.sleep(1)


def _find_child_processes(pid: int):
    children = set()
    # Get full process tree
    cmd = ["ps", "-eo", "pid,ppid"]
    output = subprocess.check_output(cmd, text=True)

    # Create pid -> parent_pid mapping
    processes = {}
    for line in output.splitlines()[1:]:  # Skip header
        parts = line.strip().split()
        if len(parts) == 2:
            child_pid, parent_pid = map(int, parts)
            processes[child_pid] = parent_pid

    # Use BFS to find all descendants
    queue = deque([pid])
    while queue:
        current_pid = queue.popleft()
        # Find all processes whose parent is current_pid
        for child_pid, parent_pid in processes.items():
            if parent_pid == current_pid:
                children.add(child_pid)
                queue.append(child_pid)

    return children


@op
def my_op():
    pass


@job
def my_job():
    my_op()


@pytest.mark.parametrize(
    "use_legacy_code_server_behavior",
    [
        #        True,
        False,
    ],
)
def test_dagster_dev_command_module(use_legacy_code_server_behavior):
    with tempfile.TemporaryDirectory() as tempdir:
        with environ({"DAGSTER_HOME": ""}):
            with new_cwd(tempdir):
                dagit_port = find_free_port()
                dev_process = subprocess.Popen(
                    [
                        "dagster",
                        "dev",
                        "-f",
                        __file__,
                        "--dagit-port",
                        str(dagit_port),
                        "--log-level",
                        "debug",
                    ]
                    + (
                        [
                            "--use-legacy-code-server-behavior",
                        ]
                        if use_legacy_code_server_behavior
                        else []
                    ),
                    cwd=tempdir,
                )
                try:
                    _wait_for_dagit_running(dagit_port)

                    # child_processes = _find_child_processes(dev_process.pid)

                    # # legacy behavior has 2 code servers, new behavior has a proxy server and a code server
                    # assert len(child_processes) == 4
                finally:
                    if seven.IS_WINDOWS:
                        dev_process.terminate()
                    else:
                        dev_process.send_signal(signal.SIGINT)
                    dev_process.communicate()
