import tempfile
import textwrap
from pathlib import Path

import pytest
from dagster_dg_core.utils import activate_venv, discover_git_root, is_windows, pushd
from dagster_shared.utils import environ
from dagster_test.components.test_utils.test_cases import BASIC_INVALID_VALUE, BASIC_MISSING_VALUE
from dagster_test.dg_utils.utils import (
    ProxyRunner,
    assert_projects_loaded_and_exit,
    assert_runner_result,
    create_project_from_components,
    find_free_port,
    install_editable_dg_dev_packages_to_venv,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
    launch_dev_command,
)


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_dev_workspace_context_success(monkeypatch):
    # The command will use `uv tool run dagster dev` to start the webserver if it
    # cannot find a venv with `dagster` and `dagster-webserver` installed. `uv tool run` will
    # pull the `dagster` package from PyPI. To avoid this, we ensure the workspace directory has a
    # venv with `dagster` and `dagster-webserver` installed.
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, create_venv=True) as workspace_path,
        environ({"DAGSTER_GIT_REPO_DIR": dagster_git_repo_dir}),
    ):
        with activate_venv(workspace_path / ".venv"):
            result = runner.invoke_create_dagster(
                "project",
                "--use-editable-dagster",
                "project-1",
                "--uv-sync",
            )
            assert_runner_result(result)
            result = runner.invoke_create_dagster(
                "project",
                "--use-editable-dagster",
                "project-2",
                "--uv-sync",
            )
            assert_runner_result(result)

            (Path("project-2") / "src" / "project_2" / "defs" / "my_asset.py").write_text(
                "import dagster as dg\n\n@dg.asset\ndef my_asset(): pass"
            )
            port = find_free_port()
            dev_process = launch_dev_command(["--port", str(port)])
            projects = {"project-1", "project-2"}
            assert_projects_loaded_and_exit(projects, port, dev_process)


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_dev_workspace_load_env_files(monkeypatch):
    """Test that the dg dev command properly loads env files from the workspace and projects."""
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, create_venv=True) as workspace_path,
        environ({"DAGSTER_GIT_REPO_DIR": dagster_git_repo_dir}),
    ):
        with activate_venv(workspace_path / ".venv"):
            Path(".env").write_text("WORKSPACE_ENV_VAR=1\nOVERWRITTEN_ENV_VAR=3")
            result = runner.invoke_create_dagster(
                "project",
                "--use-editable-dagster",
                "project-1",
                "--uv-sync",
            )
            assert_runner_result(result)
            result = runner.invoke_create_dagster(
                "project",
                "--use-editable-dagster",
                "project-2",
                "--uv-sync",
            )
            assert_runner_result(result)

            (Path("project-2") / ".env").write_text("PROJECT_ENV_VAR=2\nOVERWRITTEN_ENV_VAR=4")

            (Path("project-2") / "src" / "project_2" / "defs" / "my_def.py").write_text(
                textwrap.dedent("""
                import os

                assert os.environ["PROJECT_ENV_VAR"] == "2"
                assert os.environ["WORKSPACE_ENV_VAR"] == "1"
                assert os.environ["OVERWRITTEN_ENV_VAR"] == "4"
                """).strip()
            )
            port = find_free_port()
            with (
                tempfile.NamedTemporaryFile() as stdout_file,
                open(stdout_file.name, "w") as stdout,
            ):
                dev_process = launch_dev_command(["--port", str(port)], stdout=stdout)
                projects = {"project-1", "project-2"}
                assert_projects_loaded_and_exit(projects, port, dev_process)

                assert ("Environment variables will not be injected") not in Path(
                    stdout_file.name
                ).read_text()


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_dev_project_context_success():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, uv_sync=True) as project_path,
    ):
        venv_path = project_path / ".venv"
        install_editable_dg_dev_packages_to_venv(venv_path)

        with activate_venv(venv_path):
            port = find_free_port()
            dev_process = launch_dev_command(["--port", str(port)])
            assert_projects_loaded_and_exit({"foo-bar"}, port, dev_process)


@pytest.mark.skipif(
    is_windows() == "Windows", reason="Temporarily skipping (signal issues in CLI).."
)
def test_dev_has_options_of_dagster_dev():
    from dagster._cli.dev import dev_command as dagster_dev_command
    from dagster_dg_cli.cli import dev_command as dev_command

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


def test_implicit_yaml_check_from_dg_dev() -> None:
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
            in_workspace=False,
        ) as tmpdir,
    ):
        with pushd(str(tmpdir)):
            result = runner.invoke("dev")
            assert result.exit_code != 0, str(result.output)

            assert BASIC_INVALID_VALUE.check_error_msg and BASIC_MISSING_VALUE.check_error_msg
            BASIC_INVALID_VALUE.check_error_msg(str(result.output))
            BASIC_MISSING_VALUE.check_error_msg(str(result.output))


def test_implicit_yaml_check_from_dg_dev_in_workspace_context() -> None:
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
            in_workspace=True,
        ) as tmpdir,
    ):
        with pushd(Path(tmpdir).parent):
            result = runner.invoke("dev", "--check-yaml")
            assert result.exit_code != 0, str(result.output)

            assert "--check-yaml is not currently supported in a workspace context" in str(
                result.output
            )

        # It is supported and is the default in a project context within a workspace
        with pushd(tmpdir):
            result = runner.invoke("dev", "--check-yaml")
            assert result.exit_code != 0, str(result.output)

            assert BASIC_INVALID_VALUE.check_error_msg and BASIC_MISSING_VALUE.check_error_msg
            BASIC_INVALID_VALUE.check_error_msg(str(result.output))
            BASIC_MISSING_VALUE.check_error_msg(str(result.output))
