import signal
import subprocess
import time
from pathlib import Path

import psutil
import pytest
import requests
from dagster_dg.utils import discover_git_root, ensure_dagster_dg_tests_import, is_windows
from dagster_graphql.client import DagsterGraphQLClient

ensure_dagster_dg_tests_import()

from dagster_components.test.test_cases import BASIC_INVALID_VALUE, BASIC_MISSING_VALUE
from dagster_dg.utils import ensure_dagster_dg_tests_import, pushd

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    create_project_from_components,
    find_free_port,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
)


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_dev_workspace_context_success(monkeypatch):
    # The command will use `uv tool run dagster dev` to start the webserver if it
    # cannot find a venv with `dagster` and `dagster-webserver` installed. `uv tool run` will
    # pull the `dagster` package from PyPI. To avoid this, we ensure the workspace directory has a
    # venv with `dagster` and `dagster-webserver` installed.
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with ProxyRunner.test() as runner, isolated_example_workspace(runner, create_venv=True):
        result = runner.invoke(
            "scaffold",
            "project",
            "--use-editable-dagster",
            dagster_git_repo_dir,
            "project-1",
        )
        assert_runner_result(result)
        result = runner.invoke(
            "scaffold",
            "project",
            "--use-editable-dagster",
            dagster_git_repo_dir,
            "project-2",
        )
        assert_runner_result(result)
        port = find_free_port()
        dev_process = _launch_dev_command(["--port", str(port)])
        projects = {"project-1", "project-2"}
        _assert_projects_loaded_and_exit(projects, port, dev_process)


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_dev_project_context_success():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        port = find_free_port()
        dev_process = _launch_dev_command(["--port", str(port)])
        _assert_projects_loaded_and_exit({"foo-bar"}, port, dev_process)


@pytest.mark.skipif(
    is_windows() == "Windows", reason="Temporarily skipping (signal issues in CLI).."
)
def test_dev_has_options_of_dagster_dev():
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
@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_dev_forwards_options_to_dagster_dev():
    with ProxyRunner.test() as runner, isolated_example_workspace(runner, "foo-bar"):
        port = find_free_port()
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
            dev_process = _launch_dev_command(options + ["--no-check-yaml"])
            time.sleep(1.5)
            child_process = _get_child_processes(dev_process.pid)[0]
            assert " ".join(options) in " ".join(child_process.cmdline())
        finally:
            dev_process.terminate()  # pyright: ignore[reportPossiblyUnboundVariable]
            dev_process.communicate()  # pyright: ignore[reportPossiblyUnboundVariable]


def test_implicit_yaml_check_from_dg_dev() -> None:
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
        ) as tmpdir,
    ):
        with pushd(str(tmpdir)):
            result = runner.invoke("dev")
            assert result.exit_code != 0, str(result.stdout)

            assert BASIC_INVALID_VALUE.check_error_msg and BASIC_MISSING_VALUE.check_error_msg
            BASIC_INVALID_VALUE.check_error_msg(str(result.stdout))
            BASIC_MISSING_VALUE.check_error_msg(str(result.stdout))


def test_implicit_yaml_check_from_dg_dev_workspace() -> None:
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
        ) as tmpdir,
    ):
        with pushd(Path(tmpdir).parent):
            result = runner.invoke("dev")
            assert result.exit_code != 0, str(result.stdout)

            assert BASIC_MISSING_VALUE.check_error_msg
            BASIC_MISSING_VALUE.check_error_msg(str(result.stdout))


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


def _assert_projects_loaded_and_exit(projects: set[str], port: int, proc: subprocess.Popen) -> None:
    child_processes = []
    try:
        _ping_webserver(port)
        child_processes = _get_child_processes(proc.pid)
        assert _query_code_locations(port) == projects
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
