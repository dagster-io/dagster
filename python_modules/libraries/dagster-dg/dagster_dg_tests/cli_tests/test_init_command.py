import os
import subprocess
from pathlib import Path
from typing import Optional, get_args

import dagster_shared.check as check
import pytest
import tomlkit
from dagster_dg.utils import discover_git_root, ensure_dagster_dg_tests_import, get_toml_node

ensure_dagster_dg_tests_import()
from dagster_dg_tests.cli_tests.test_scaffold_commands import (
    EditableOption,
    validate_pyproject_toml_with_editable,
)

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import ProxyRunner, assert_runner_result


@pytest.mark.parametrize(
    "cli_args,input_str,opts",
    [
        (("--", "."), "y\n", {}),
        # Test preexisting venv in the project directory
        (("--", "."), None, {"use_preexisting_venv": True}),
        # Skip the uv sync prompt and automatically uv sync
        (("--uv-sync", "--", "."), None, {}),
        # Skip the uv sync prompt and don't uv sync
        (("--no-uv-sync", "--", "."), None, {}),
        # Test uv not available. When uv is not available there will be no prompt-- so this test
        # will hang if it's not working because we don't provide an input string.
        (("--", "."), None, {"no_uv": True}),
        (("--", "helloworld"), "y\n", {}),
        (("--project-name", "helloworld"), "y\n", {}),
        (tuple(), "helloworld\ny\n", {}),
        # Test declining to create a venv
        (("--", "helloworld"), "n\n", {}),
    ],
    ids=[
        "dirname_cwd",
        "dirname_cwd_preexisting_venv",
        "dirname_cwd_explicit_uv_sync",
        "dirname_cwd_explicit_no_uv_sync",
        "dirname_cwd_no_uv",
        "dirname_arg",
        "project_name_opt",
        "project_name_prompt",
        "dirname_arg_no_venv",
    ],
)
def test_init_success_project(
    monkeypatch, cli_args: tuple[str, ...], input_str: Optional[str], opts: dict[str, object]
) -> None:
    use_preexisting_venv = check.opt_bool_elem(opts, "use_preexisting_venv") or False
    no_uv = check.opt_bool_elem(opts, "no_uv") or False
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
    if no_uv:
        monkeypatch.setattr("dagster_dg.cli.init.is_uv_installed", lambda: False)
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        if "." in cli_args:  # creating in CWD
            os.mkdir("helloworld")
            os.chdir("helloworld")
            if use_preexisting_venv:
                subprocess.run(["uv", "venv"], check=True)

        result = runner.invoke(
            "init",
            "--use-editable-dagster",
            *cli_args,
            input=input_str,
        )
        assert_runner_result(result)

        if "." in cli_args:  # creating in CWD
            os.chdir("..")

        assert not Path("dagster-workspace").exists()
        assert Path("helloworld").exists()
        assert Path("helloworld/src/helloworld").exists()
        assert Path("helloworld/pyproject.toml").exists()
        assert Path("helloworld/tests").exists()

        # this indicates user opts to create venv and uv.lock
        if not use_preexisting_venv and (
            (input_str and input_str.endswith("y\n")) or "--uv-sync" in cli_args
        ):
            assert Path("helloworld/.venv").exists()
            assert Path("helloworld/uv.lock").exists()
        elif use_preexisting_venv:
            assert Path("helloworld/.venv").exists()
            assert not Path("helloworld/uv.lock").exists()
        else:
            assert not Path("helloworld/.venv").exists()
            assert not Path("helloworld/uv.lock").exists()

        if use_preexisting_venv in cli_args:
            assert "environment used for your project must include" in result.output


@pytest.mark.parametrize(
    "cli_args,input_str,opts",
    [
        (("--project-name", "helloworld", "."), "y\n", {}),
        # Test declining to create a venv
        (("--project-name", "helloworld", "."), "n\n", {}),
        # Skip the uv sync prompt and automatically uv sync
        (("--uv-sync", "--project-name", "helloworld", "."), None, {}),
        # Skip the uv sync prompt and don't uv sync
        (("--no-uv-sync", "--project-name", "helloworld", "."), None, {}),
        # Test uv not available. When uv is not available there will be no prompt-- so this test
        # will hang if it's not working because we don't provide an input string.
        (("--project-name", "helloworld", "."), None, {"no_uv": True}),
        (("--project-name", "helloworld", "dagster-workspace"), "y\n", {}),
        (("--", "dagster-workspace"), "helloworld\ny\n", {}),
        (tuple(), "dagster-workspace\nhelloworld\ny\n", {}),
    ],
    ids=[
        "dirname_cwd_and_project_name",
        "dirname_cwd_and_project_name_decline_venv",
        "dirname_cwd_and_project_name_explicit_uv_sync",
        "dirname_cwd_and_project_name_explicit_no_uv_sync",
        "dirname_cwd_and_project_name_no_uv",
        "dirname_arg_and_project_name",
        "dirname_arg_no_project_name",
        "no_dirname_arg_no_project_name",
    ],
)
def test_init_success_workspace(
    monkeypatch, cli_args: tuple[str, ...], input_str: Optional[str], opts: dict[str, object]
) -> None:
    no_uv = check.opt_bool_elem(opts, "no_uv") or False
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
    if no_uv:
        monkeypatch.setattr("dagster_dg.cli.init.is_uv_installed", lambda: False)
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        if "." in cli_args:  # creating in CWD
            os.mkdir("dagster-workspace")
            os.chdir("dagster-workspace")

        result = runner.invoke(
            "init",
            "--workspace",
            "--use-editable-dagster",
            *cli_args,
            input=input_str,
        )
        assert_runner_result(result)

        if "." in cli_args:  # creating in CWD
            os.chdir("..")

        assert Path("dagster-workspace").exists()
        assert Path("dagster-workspace/dg.toml").exists()
        assert Path("dagster-workspace/projects").exists()
        assert not Path("dagster-workspace/libraries").exists()
        assert Path("dagster-workspace/projects/helloworld").exists()
        assert Path("dagster-workspace/projects/helloworld/src/helloworld").exists()
        assert Path("dagster-workspace/projects/helloworld/pyproject.toml").exists()
        assert Path("dagster-workspace/projects/helloworld/tests").exists()

        # this indicates user opts to create venv and uv.lock
        if not no_uv and ((input_str and input_str.endswith("y\n")) or "--uv-sync" in cli_args):
            assert Path("dagster-workspace/projects/helloworld/.venv").exists()
            assert Path("dagster-workspace/projects/helloworld/uv.lock").exists()
        else:
            assert not Path("dagster-workspace/projects/helloworld/.venv").exists()
            assert not Path("dagster-workspace/projects/helloworld/uv.lock").exists()

        # Check workspace TOML content
        toml = tomlkit.parse(Path("dagster-workspace/dg.toml").read_text())
        assert (
            get_toml_node(toml, ("workspace", "projects", 0, "path"), str) == "projects/helloworld"
        )


def test_init_workspace_already_exists_failure(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        os.mkdir("dagster-workspace")
        result = runner.invoke(
            "init",
            "--use-editable-dagster",
            "--workspace",
            "dagster-workspace",
            input="\nhelloworld\n",
        )
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_init_project_already_exists_failure(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        os.mkdir("foo")
        result = runner.invoke("init", "--use-editable-dagster", "--", "foo")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


@pytest.mark.parametrize("option", get_args(EditableOption))
@pytest.mark.parametrize("value_source", ["env_var", "arg"])
def test_init_use_editable_dagster(option: EditableOption, value_source: str, monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    if value_source == "env_var":
        monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
        editable_args = [option, "--"]
    else:
        editable_args = [option, str(dagster_git_repo_dir)]

    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke(
            "init",
            "--workspace",
            *editable_args,
            "dagster-workspace",
            input="helloworld\ny\n",
        )
        assert_runner_result(result)

        assert Path("dagster-workspace").exists()

        workspace_config = Path("dagster-workspace/dg.toml")
        with workspace_config.open() as f:
            toml = tomlkit.parse(f.read())
            option_key = option[2:].replace("-", "_")
            option_value = True if value_source == "env_var" else str(dagster_git_repo_dir)
            assert (
                get_toml_node(
                    toml,
                    ("workspace", "scaffold_project_options", option_key),
                    (bool, str),
                )
                == option_value
            )

        project_config = Path("dagster-workspace/projects/helloworld/pyproject.toml")
        assert project_config.exists()
        with project_config.open() as f:
            toml = tomlkit.parse(f.read())
            validate_pyproject_toml_with_editable(toml, option, dagster_git_repo_dir)


@pytest.mark.parametrize("option", get_args(EditableOption))
def test_init_project_editable_dagster_no_env_var_no_value_fails(
    option: EditableOption, monkeypatch
) -> None:
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", "")
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("init", option, input="helloworld\n")
        assert_runner_result(result, exit_0=False)
        assert "requires the `DAGSTER_GIT_REPO_DIR`" in result.output


def test_init_project_python_environment_uv_managed_succeeds() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("init", "helloworld", "--python-environment", "uv_managed")
        assert_runner_result(result)
        assert Path("helloworld").exists()
        assert Path("helloworld/src/helloworld").exists()
        assert Path("helloworld/pyproject.toml").exists()
        assert Path("helloworld/tests").exists()

        # Make sure venv created
        assert Path("helloworld/.venv").exists()
        assert Path("helloworld/uv.lock").exists()
