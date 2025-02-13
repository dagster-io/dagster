import contextlib
import signal
import socket
import subprocess
import time

import psutil
import pytest
import requests
from dagster_dg.utils import ensure_dagster_dg_tests_import, is_windows
from dagster_graphql.client import DagsterGraphQLClient

ensure_dagster_dg_tests_import()
from dagster_dg_tests.utils import (
    ProxyRunner,
    isolated_example_code_location_foo_bar,
    isolated_example_deployment_foo,
)


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_dev_command_deployment_context_success():
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        runner.invoke("code-location", "scaffold", "code-location-1")
        runner.invoke("code-location", "scaffold", "code-location-2")

        port = _find_free_port()
        dev_process = _launch_dev_command(["--port", str(port)])
        code_locations = {"code-location-1", "code-location-2"}
        _assert_code_locations_loaded_and_exit(code_locations, port, dev_process)


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_dev_command_code_location_context_success():
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        port = _find_free_port()
        dev_process = _launch_dev_command(["--port", str(port)])
        _assert_code_locations_loaded_and_exit({"foo-bar"}, port, dev_process)


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_dev_command_outside_project_context_fails():
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        port = _find_free_port()
        dev_process = _launch_dev_command(["--port", str(port)], capture_output=True)
        assert dev_process.wait() != 0
        assert dev_process.stdout
        assert (
            "This command must be run inside a code location or deployment directory."
            in dev_process.stdout.read().decode()
        )


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
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
    }

    dg_dev_param_names = {param.name for param in dev_command.params}
    dagster_dev_param_names = {param.name for param in dagster_dev_command.params}
    dagster_dev_params_to_check = dagster_dev_param_names - exclude_dagster_dev_params

    unmatched_params = dagster_dev_params_to_check - dg_dev_param_names
    assert not unmatched_params, f"dg dev missing params: {unmatched_params}"


# Modify this test with a new option whenever a new forwarded option is added to `dagster-dev`.
@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_dev_command_forwards_options_to_dagster_dev():
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
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
            "--host",
            "localhost",
            "--live-data-poll-rate",
            "3000",
        ]
        try:
            dev_process = _launch_dev_command(options)
            time.sleep(0.5)
            child_process = _get_child_processes(dev_process.pid)[0]
            expected_cmdline = [
                "uv",
                "run",
                "dagster",
                "dev",
                *options,
            ]
            assert child_process.cmdline() == expected_cmdline
        finally:
            dev_process.terminate()
            dev_process.communicate()


# ########################
# ##### HELPERS
# ########################


def _launch_dev_command(options: list[str], capture_output: bool = False) -> subprocess.Popen:
    # We start a new process instead of using the runner to avoid blocking the test. We need to
    # poll the webserver to know when it is ready.
    return subprocess.Popen(
        [
            "dg",
            "dev",
            *options,
        ],
        stdout=subprocess.PIPE if capture_output else None,
    )


def _assert_code_locations_loaded_and_exit(
    code_locations: set[str], port: int, proc: subprocess.Popen
) -> None:
    child_processes = []
    try:
        _ping_webserver(port)
        child_processes = _get_child_processes(proc.pid)
        assert _query_code_locations(port) == code_locations
    finally:
        proc.send_signal(signal.SIGINT)
        proc.communicate()
        time.sleep(3)
        _assert_no_child_processes_running(child_processes)


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


def _ping_webserver(port: int) -> None:
    start_time = time.time()
    while True:
        try:
            server_info = requests.get(f"http://localhost:{port}/server_info").json()
            if server_info:
                return
        except:
            print("Waiting for dagster-webserver to be ready..")  # noqa: T201

        if time.time() - start_time > 30:
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
