import os
from pathlib import Path
from typing import get_args

import pytest
import tomlkit
from dagster_dg.utils import discover_git_root, ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()
from dagster_dg_tests.cli_tests.test_scaffold_commands import (
    EditableOption,
    validate_pyproject_toml_with_editable,
)

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import ProxyRunner, assert_runner_result

runner_opts = {"use_entry_points": True}


def test_dg_init_command_success(monkeypatch) -> None:
    with ProxyRunner.test(**runner_opts) as runner, runner.isolated_filesystem():
        result = runner.invoke("init", input="\nhelloworld\n")
        assert_runner_result(result)
        assert Path("dagster-workspace").exists()
        assert Path("dagster-workspace/pyproject.toml").exists()
        assert Path("dagster-workspace/projects").exists()
        assert Path("dagster-workspace/libraries").exists()
        assert Path("dagster-workspace/projects/helloworld").exists()
        assert Path("dagster-workspace/projects/helloworld/helloworld").exists()
        assert Path("dagster-workspace/projects/helloworld/pyproject.toml").exists()
        assert Path("dagster-workspace/projects/helloworld/helloworld_tests").exists()


def test_dg_init_command_no_project(monkeypatch) -> None:
    with ProxyRunner.test(**runner_opts) as runner, runner.isolated_filesystem():
        result = runner.invoke("init", input="\n\n")
        assert_runner_result(result)
        assert Path("dagster-workspace").exists()
        assert Path("dagster-workspace/pyproject.toml").exists()
        assert Path("dagster-workspace/projects").exists()
        assert Path("dagster-workspace/libraries").exists()


def test_dg_init_override_workspace_name(monkeypatch) -> None:
    with ProxyRunner.test(**runner_opts) as runner, runner.isolated_filesystem():
        result = runner.invoke("init", input="my-workspace\ngoodbyeworld\n")
        assert_runner_result(result)
        assert Path("my-workspace").exists()
        assert Path("my-workspace/pyproject.toml").exists()
        assert Path("my-workspace/projects").exists()
        assert Path("my-workspace/libraries").exists()
        assert Path("my-workspace/projects/goodbyeworld").exists()
        assert Path("my-workspace/projects/goodbyeworld/goodbyeworld").exists()
        assert Path("my-workspace/projects/goodbyeworld/pyproject.toml").exists()
        assert Path("my-workspace/projects/goodbyeworld/goodbyeworld_tests").exists()


def test_dg_init_workspace_already_exists_failure(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test(**runner_opts) as runner, runner.isolated_filesystem():
        os.mkdir("dagster-workspace")
        result = runner.invoke("init", "--use-editable-dagster", input="\nhelloworld\n")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


@pytest.mark.parametrize("option", get_args(EditableOption))
@pytest.mark.parametrize("value_source", ["env_var", "arg"])
def test_dg_init_use_editable_dagster(
    option: EditableOption, value_source: str, monkeypatch
) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    if value_source == "env_var":
        monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
        editable_args = [option, "--"]
    else:
        editable_args = [option, str(dagster_git_repo_dir)]

    with ProxyRunner.test(**runner_opts) as runner, runner.isolated_filesystem():
        result = runner.invoke("init", *editable_args, input="\nhelloworld\n")
        assert_runner_result(result)

        assert Path("dagster-workspace").exists()
        pyproject_toml = Path("dagster-workspace/projects/helloworld/pyproject.toml")
        assert pyproject_toml.exists()
        with pyproject_toml.open() as f:
            toml = tomlkit.parse(f.read())
            validate_pyproject_toml_with_editable(toml, option, dagster_git_repo_dir)


@pytest.mark.parametrize("option", get_args(EditableOption))
def test_dg_init_project_editable_dagster_no_env_var_no_value_fails(
    option: EditableOption, monkeypatch
) -> None:
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", "")
    with ProxyRunner.test(**runner_opts) as runner, runner.isolated_filesystem():
        result = runner.invoke("init", option, input="\nhelloworld\n")
        assert_runner_result(result, exit_0=False)
        assert "require the `DAGSTER_GIT_REPO_DIR`" in result.output
