import os
import subprocess
from pathlib import Path
from typing import Optional, get_args

import dagster_shared.check as check
import pytest
import tomlkit
from dagster_dg.utils import discover_git_root, ensure_dagster_dg_tests_import, get_toml_node

ensure_dagster_dg_tests_import()
from dagster_dg_tests.cli_tests.test_scaffold_commands

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import ProxyRunner, assert_runner_result


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
