import contextlib
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import psutil
import requests
from dagster_dg.utils import discover_git_root, ensure_dagster_dg_tests_import, is_windows
from dagster_dg.utils.ipc import (
    get_ipc_shutdown_pipe,
    open_ipc_subprocess,
    send_ipc_shutdown_message,
)
from dagster_graphql.client import DagsterGraphQLClient

ensure_dagster_dg_tests_import()
from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
)


def test_dev_command_workspace_context_success(monkeypatch):
    # The command will use `uv tool run dagster dev` to start the webserver if it
    # cannot find a venv with `dagster` and `dagster-webserver` installed. `uv tool run` will
    # pull the `dagster` package from PyPI. To avoid this, we ensure the workspace directory has a
    # venv with `dagster` and `dagster-webserver` installed.
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with ProxyRunner.test() as runner, isolated_example_workspace(runner, create_venv=True):
        result = runner.invoke(
            "scaffold",
            "project",
            "--use-editable-component-package-only",
            dagster_git_repo_dir,
            "project-1",
        )
        assert_runner_result(result)
        result = runner.invoke(
            "scaffold",
            "project",
            "--use-editable-component-package-only",
            dagster_git_repo_dir,
            "project-2",
        )
        assert_runner_result(result)
        port = _find_free_port()
        projects = {"project-1", "project-2"}
        with _launch_dev_command(["--port", str(port)]) as dev_process:
            _wait_for_webserver_running(port, dev_process)
            assert _query_code_locations(port) == projects
            _validate_expected_child_processes(dev_process, 8)


def test_dev_command_project_context_success():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        port = _find_free_port()
        code_locations = {"foo-bar"}
        with _launch_dev_command(["--port", str(port)]) as dev_process:
            _wait_for_webserver_running(port, dev_process)
            assert _query_code_locations(port) == code_locations
            _validate_expected_child_processes(dev_process, 6)


def test_dev_command_has_options_of_dagster_dev():
    from dagster._cli.dev import dev_command as dagster_dev_command
    from dagster_dg.cli import dev_command as dev_command

    exclude_dagster_dev_params = {
        # Exclude options that are used to set the target. `dg dev` does not use.
        "empty_workspace",
        "workspace",
        "python_file",
        "module_name",
        "package_name",
        "attribute",
        "working_directory",
        "grpc_port",
        "grpc_socket",
        "grpc_host",
        "use_ssl",
        # Misc others to exclude
        "use_legacy_code_server_behavior",
        "shutdown_pipe",
    }

    dg_dev_param_names = {param.name for param in dev_command.params}
    dagster_dev_param_names = {param.name for param in dagster_dev_command.params}
    dagster_dev_params_to_check = dagster_dev_param_names - exclude_dagster_dev_params

    unmatched_params = dagster_dev_params_to_check - dg_dev_param_names
    assert not unmatched_params, f"dg dev missing params: {unmatched_params}"


# Modify this test with a new option whenever a new forwarded option is added to `dagster-dev`.
def test_dev_command_forwards_options_to_dagster_dev():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        port = _find_free_port()
        options = [
            "--code-server-log-level",
            "debug",
            "--log-level",
            "debug",
            "--log-format",
            "json",
            "--port",
            str(port),
            "--live-data-poll-rate",
            "3000",
        ]
        with _launch_dev_command(options) as dev_process:
            _wait_for_webserver_running(port, dev_process)  # Wait for everything to start up
            child_processes = _get_child_processes(dev_process.pid)

            # On Unix, this is reliably the first child process, but the situation is more
            # complicated on Windows. So explicitly find the `uv run dagster dev` process.
            uv_run_proc = next(p for p in child_processes if p.cmdline()[0] == "uv")

            # Remove the `--shutdown-pipe N` option from the command line. This is added
            # automatically by `dg dev` and is not a forwarded option.
            cmdline = uv_run_proc.cmdline()
            rm_index = cmdline.index("--shutdown-pipe")
            filtered_cmdline = cmdline[:rm_index] + cmdline[rm_index + 2 :]

            expected_cmdline = [
                "uv",
                "run",
                "dagster",
                "dev",
                *options,
            ]
            assert filtered_cmdline == expected_cmdline


# ########################
# ##### HELPERS
# ########################


@contextlib.contextmanager
def _launch_dev_command(
    options: list[str], capture_output: bool = False
) -> Iterator[subprocess.Popen]:
    # We start a new process instead of using the runner to avoid blocking the test. We need to
    # poll the webserver to know when it is ready.
    read_fd, write_fd = get_ipc_shutdown_pipe()
    proc = open_ipc_subprocess(
        ["dg", "dev", *options, "--shutdown-pipe", str(read_fd)],
        pass_fds=[read_fd],
    )
    try:
        yield proc
    finally:
        if psutil.pid_exists(proc.pid):
            child_processes = psutil.Process(proc.pid).children(recursive=True)
            send_ipc_shutdown_message(write_fd)
            proc.wait(timeout=10)
            # The `dagster dev` command exits before the gRPC servers it spins up have shutdown. Wait
            # for the child processes to exit here to make sure we don't leave any hanging processes.
            #
            # We disable this check on Windows because interrupt signal propagation does not work in a
            # CI environment. Interrupt propagation is dependent on processes sharing a console (which
            # is the case in a user terminal session, but not in a CI environment). So on windows, we
            # force kill the processes after a timeout.
            _wait_for_child_processes_to_exit(child_processes, timeout=120)


def _validate_expected_child_processes(dev_process: subprocess.Popen, expected_count: int) -> None:
    # Note that on Windows, each
    # tox shimming creating persistent processes. We are still checking that all child processes
    # shut down later.

    # 6 (1 code loc) or 8 (2 code loc) processes:
    # - uv run
    # - dg dev
    # - dagster-daemon
    # - dagster-webserver
    # - 2x dagster code-server start (code servers 1 and 2)
    # - 2x dagster api grpc (started by dagster code-server start) (code servers 1 and 2)
    #
    # Some of the tests above execute jobs, which result in additional child processes that may
    # or may not be running/cleaned up by the time we get here. These are identifiable because
    # they are spawned by the Python multiprocessing module. We aren't interested in these,
    # exclude them.
    child_processes = _get_child_processes(dev_process.pid)

    # On Windows, we make two adjustments:
    # - Exclude any processes that are themselves `dg dev` commands. This happens because
    #   windows will sometimes return a PID as a child of itself.
    # - Exclude any processes that are shims from tox or a venv. When executing these tests through tox, each
    #   launched process runs through a shim that is itself a persistent process.
    if is_windows():
        child_processes = [
            proc
            for proc in child_processes
            if not (
                "dg" in proc.cmdline()
                or ".tox\\" in proc.cmdline()[1]
                or ".venv\\" in proc.cmdline()[0]
                or proc.cmdline()[1].startswith("C:\\")  # another shim variant
            )
        ]
    if len(child_processes) != expected_count:
        proc_info = "\n".join([_get_proc_repr(proc) for proc in child_processes])
        raise Exception(
            f"Expected {expected_count} child processes, found {len(child_processes)}:\n{proc_info}"
        )


def _assert_no_child_processes_running(child_procs: list[psutil.Process]) -> None:
    for proc in child_procs:
        assert not proc.is_running(), f"Process {proc.pid} ({proc.cmdline()}) is still running"


def _get_child_processes(pid) -> list[psutil.Process]:
    parent = psutil.Process(pid)
    return parent.children(recursive=True)


def _find_free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def _wait_for_webserver_running(port: int, proc: subprocess.Popen) -> None:
    start_time = time.time()
    while True:
        if proc.poll() is not None:
            raise Exception(
                f"dg dev process shut down unexpectedly with return code {proc.returncode}."
            )
        try:
            server_info = requests.get(f"http://localhost:{port}/server_info").json()
            if server_info:
                return
        except:
            print("Waiting for dagster-webserver to be ready..")  # noqa: T201

        # Can take a while to start up in CI
        if time.time() - start_time > 120:
            raise Exception("Timed out waiting for dagster-webserver to serve requests")

        time.sleep(1)


_GET_CODE_LOCATION_NAMES_QUERY = """
query GetCodeLocationNames {
  repositoriesOrError {
    __typename
    ... on RepositoryConnection {
      nodes {
        name
        location {
          name
        }
      }
    }
    ... on PythonError {
      message
    }
  }
}
"""


def _query_code_locations(port: int) -> set[str]:
    gql_client = DagsterGraphQLClient(hostname="localhost", port_number=port)
    result = gql_client._execute(_GET_CODE_LOCATION_NAMES_QUERY)  # noqa: SLF001
    assert result["repositoriesOrError"]["__typename"] == "RepositoryConnection"
    return {node["location"]["name"] for node in result["repositoriesOrError"]["nodes"]}


def _wait_for_child_processes_to_exit(child_procs: list[psutil.Process], timeout: int) -> None:
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
