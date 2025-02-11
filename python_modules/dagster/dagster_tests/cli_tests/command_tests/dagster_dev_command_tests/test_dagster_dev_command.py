import os
import platform
import subprocess
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import psutil
import requests
import yaml
from dagster._cli.utils import TMP_DAGSTER_HOME_PREFIX
from dagster._core.events import DagsterEventType
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import environ
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.server import wait_for_grpc_server
from dagster._serdes.ipc import (
    interrupt_ipc_subprocess,
    interrupt_then_kill_ipc_subprocess,
    open_ipc_subprocess,
)
from dagster._utils import find_free_port, pushd
from dagster_graphql import DagsterGraphQLClient


def test_dagster_dev_command_workspace():
    with tempfile.TemporaryDirectory() as tempdir:
        with environ({"DAGSTER_HOME": ""}):
            with pushd(tempdir):
                webserver_port = find_free_port()
                with _launch_dev_command(
                    [
                        "-w",
                        str(Path(__file__).parent / "workspace.yaml"),
                        "--port",
                        str(webserver_port),
                        "--log-level",
                        "debug",
                    ],
                ) as dev_process:
                    _wait_for_webserver_running(webserver_port)
                    _validate_job_available(webserver_port, "foo_job")
                    _validate_expected_child_processes(dev_process, 4)


def test_dagster_dev_command_module():
    with tempfile.TemporaryDirectory() as tempdir:
        with environ({"DAGSTER_HOME": ""}):
            with pushd(tempdir):
                webserver_port = find_free_port()
                with _launch_dev_command(
                    [
                        "-m",
                        "repo",
                        "--working-directory",
                        str(Path(__file__).parent),
                        "--port",
                        str(webserver_port),
                        "--log-level",
                        "debug",
                    ],
                ) as dev_process:
                    _wait_for_webserver_running(webserver_port)
                    _validate_job_available(webserver_port, "foo_job")
                    _validate_expected_child_processes(dev_process, 4)


# E2E test that spins up "dagster dev", accesses webserver,
# and waits for a schedule run to launch
def test_dagster_dev_command_no_dagster_home():
    environment_patch = {
        "DAGSTER_HOME": "",  # unset dagster home
        "CHECK_DAGSTER_DEV": "1",  # trigger target user code to check for DAGSTER_DEV env var
    }
    dagster_yaml = {
        "run_coordinator": {
            "module": "dagster.core.run_coordinator",
            "class": "QueuedRunCoordinator",
        },
    }

    with tempfile.TemporaryDirectory() as tempdir, environ(environment_patch), pushd(tempdir):
        with open(os.path.join(str(tempdir), "dagster.yaml"), "w") as config_file:
            yaml.dump(dagster_yaml, config_file)

        webserver_port = find_free_port()
        with _launch_dev_command(
            [
                "-f",
                str(Path(__file__).parent / "repo.py"),
                "--working-directory",
                str(Path(__file__).parent),
                "--port",
                str(webserver_port),
                "--dagit-host",
                "127.0.0.1",
            ],
        ) as dev_process:
            _wait_for_webserver_running(webserver_port)
            _validate_job_available(webserver_port, "foo_job")
            _validate_expected_child_processes(dev_process, 4)

            instance_dir = _wait_for_instance_dir_to_be_written(Path(tempdir))

            # Wait for schedule to launch
            with DagsterInstance.from_config(str(instance_dir)) as instance:
                start_time = time.time()
                while True:
                    if (
                        len(instance.get_runs()) > 0
                        and len(
                            instance.fetch_run_status_changes(
                                DagsterEventType.PIPELINE_ENQUEUED, limit=1
                            ).records
                        )
                        > 0
                    ):
                        # Verify the run was queued (so the dagster.yaml was applied)
                        break

                    if time.time() - start_time > 30:
                        raise Exception("Timed out waiting for queued run to exist")

                    time.sleep(1)


def test_dagster_dev_command_grpc_port():
    with tempfile.TemporaryDirectory() as tempdir, pushd(tempdir):
        webserver_port = find_free_port()
        grpc_port = find_free_port()

        subprocess_args = [
            "dagster",
            "api",
            "grpc",
            "-f",
            str(Path(__file__).parent / "repo.py"),
            "--working-directory",
            str(Path(__file__).parent),
            "-p",
            str(grpc_port),
        ]
        grpc_process = open_ipc_subprocess(subprocess_args)
        try:
            client = DagsterGrpcClient(port=grpc_port, host="localhost")
            wait_for_grpc_server(grpc_process, client, subprocess_args)
            with _launch_dev_command(
                [
                    "--port",
                    str(webserver_port),
                    "--dagit-host",
                    "127.0.0.1",
                    "--grpc-port",
                    str(grpc_port),
                    "--grpc-host",
                    "localhost",
                ],
            ) as dev_process:
                _wait_for_webserver_running(webserver_port)
                _validate_job_available(webserver_port, "foo_job")
                # daemon, webserver only since the grpc server is separate
                _validate_expected_child_processes(dev_process, 2)
                client = DagsterGraphQLClient(hostname="localhost", port_number=webserver_port)
                client.submit_job_execution("foo_job")

                # For some reason if we don't shut down the gRPC server before the dev server, there
                # is a database access error when shutting down the gRPC server.
                interrupt_then_kill_ipc_subprocess(grpc_process)
                grpc_process.communicate()
        finally:
            if psutil.pid_exists(grpc_process.pid):
                interrupt_then_kill_ipc_subprocess(grpc_process)


def test_dagster_dev_command_legacy_code_server_behavior():
    environment_patch = {
        "DAGSTER_HOME": "",  # unset dagster home
    }
    with tempfile.TemporaryDirectory() as tempdir, environ(environment_patch), pushd(tempdir):
        webserver_port = find_free_port()
        with _launch_dev_command(
            [
                "-m",
                "repo",
                "--working-directory",
                str(Path(__file__).parent),
                "--port",
                str(webserver_port),
                "--log-level",
                "debug",
                "--use-legacy-code-server-behavior",
            ],
        ) as dev_process:
            _wait_for_webserver_running(webserver_port)
            _validate_job_available(webserver_port, "foo_job")

            # 4 processes:
            # - dagster-daemon
            # - dagster-webserver
            # - dagster api grpc (for daemon)
            # - dagster api grpc (for webserver)
            _validate_expected_child_processes(dev_process, 4)


# ########################
# ##### HELPERS
# ########################


@contextmanager
def _launch_dev_command(
    options: list[str], capture_output: bool = False
) -> Iterator[subprocess.Popen]:
    proc = open_ipc_subprocess(
        ["dagster", "dev", *options],
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None,
        cwd=os.getcwd(),
    )
    try:
        yield proc
    finally:
        child_processes = _get_child_processes(proc.pid)
        interrupt_ipc_subprocess(proc)
        proc.wait(timeout=10)
        # The `dagster dev` command exits before the gRPC servers it spins up have shutdown. Wait
        # for the child processes to exit here to make sure we don't leave any hanging processes.
        #
        # We disable this check on Windows because interrupt signal propagation does not work in a
        # CI environment. Interrupt propagation is dependent on processes sharing a console (which
        # is the case in a user terminal session, but not in a CI environment). So on windows, we
        # force kill the processes after a timeout.
        _wait_for_child_processes_to_exit(
            child_processes, timeout=30, force_kill=platform.system() == "Windows"
        )


def _wait_for_webserver_running(dagit_port):
    start_time = time.time()
    while True:
        try:
            server_info = requests.get(f"http://localhost:{dagit_port}/server_info").json()
            if server_info:
                return
        except:
            print("Waiting for webserver to be ready..")  # noqa: T201

        if time.time() - start_time > 30:
            raise Exception("Timed out waiting for webserver to serve requests")

        time.sleep(1)


def _wait_for_instance_dir_to_be_written(parent_dir: Path) -> Path:
    # Wait for instance files to exist
    start_time = time.time()
    while True:
        if time.time() - start_time > 30:
            raise Exception("Timed out waiting for instance files to exist")
        subfolders = [
            child
            for child in parent_dir.iterdir()
            if child.name.startswith(TMP_DAGSTER_HOME_PREFIX) and (child / "history").exists()
        ]

        if len(subfolders):
            assert len(subfolders) == 1
            break

        time.sleep(1)
    return subfolders[0]


def _validate_job_available(port: int, job_name: str):
    client = DagsterGraphQLClient(hostname="localhost", port_number=port)
    locations_and_names = client._get_repo_locations_and_names_with_pipeline(job_name)  # noqa: SLF001
    assert (
        len(locations_and_names) > 0
    ), f"repo failed to load or was missing a job called '{job_name}'"


def _validate_expected_child_processes(dev_process: subprocess.Popen, expected_count: int) -> None:
    # Skip windows here-- it spawns a lot more processes than Unix when running through tox, due to
    # tox shimming creating persistent processes. We are still checking that all child processes
    # shut down later.
    if platform.system() != "Windows":
        # 4 processes:
        # - dagster-daemon
        # - dagster-webserver
        # - dagster code-server start
        # - dagster api grpc (started by dagster code-server start)
        #
        # Some of the tests above execute jobs, which result in additional child processes that may
        # or may not be running/cleaned up by the time we get here. We aren't interested in these,
        # exclude them.
        child_processes = _get_child_processes(dev_process.pid, exclude_job_processes=True)
        if len(child_processes) != expected_count:
            proc_info = "\n".join([_get_proc_repr(proc) for proc in child_processes])
            raise Exception(
                f"Expected {expected_count} child processes, found {len(child_processes)}:\n{proc_info}"
            )


def _get_child_processes(pid, exclude_job_processes: bool = False) -> list[psutil.Process]:
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    if exclude_job_processes:
        return [c for c in children if not _is_job_execution_process(c)]
    else:
        return children


def _is_job_execution_process(proc: psutil.Process) -> bool:
    return any(x.startswith("from multiprocessing") for x in proc.cmdline())


def _wait_for_child_processes_to_exit(
    child_procs: list[psutil.Process], timeout: int, force_kill: bool = False
) -> None:
    start_time = time.time()
    while True:
        running_child_procs = [proc for proc in child_procs if proc.is_running()]
        if not running_child_procs:
            break
        if time.time() - start_time > timeout:
            stopped_child_procs = [proc for proc in child_procs if not proc.is_running()]
            stopped_proc_lines = [_get_proc_repr(proc) for proc in stopped_child_procs]
            running_proc_lines = [_get_proc_repr(proc) for proc in running_child_procs]
            desc = "\n".join(
                [
                    "STOPPED:",
                    *stopped_proc_lines,
                    "RUNNING:",
                    *running_proc_lines,
                ]
            )
            if force_kill:
                for proc in running_child_procs:
                    try:
                        proc.kill()
                    # Can happen if the process shut down from another shutting down in the
                    # iteration.
                    except psutil.NoSuchProcess:
                        pass
            else:
                raise Exception(
                    f"Timed out waiting for all child processes to exit. Remaining:\n{desc}"
                )
        time.sleep(0.5)


def _get_proc_repr(proc: psutil.Process) -> str:
    return f"PID [{proc.pid}] PPID [{_get_ppid(proc)}]: {_get_cmdline(proc)}"


def _get_ppid(proc: psutil.Process) -> str:
    try:
        return str(proc.ppid())
    except psutil.NoSuchProcess:
        return "IRRETRIEVABLE"


def _get_cmdline(proc: psutil.Process) -> str:
    try:
        return str(proc.cmdline())
    except psutil.NoSuchProcess:
        return "CMDLINE IRRETRIEVABLE"
