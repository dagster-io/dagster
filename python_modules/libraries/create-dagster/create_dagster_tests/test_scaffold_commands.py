import os
import subprocess
from pathlib import Path
from typing import Literal, Optional, get_args

import dagster_shared.check as check
import pytest
import tomlkit
from dagster_dg.shared_options import DEFAULT_EDITABLE_DAGSTER_PROJECTS_ENV_VAR
from dagster_dg.utils import (
    create_toml_node,
    discover_git_root,
    ensure_dagster_dg_tests_import,
    get_toml_node,
    has_toml_node,
    modify_toml_as_dict,
    pushd,
)
from typing_extensions import TypeAlias

ensure_dagster_dg_tests_import()

from dagster_dg.utils import ensure_dagster_dg_tests_import
from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    clear_module_from_cache,
    isolated_example_workspace,
)

# ########################
# ##### WORKSPACE
# ########################


@pytest.mark.parametrize(
    "cli_args",
    [
        tuple(),
        ("helloworld",),
        (".",),
    ],
    ids=[
        "no_args",
        "with_name",
        "with_cwd",
    ],
)
def test_scaffold_workspace_command_success(monkeypatch, cli_args: tuple[str, ...]) -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        if "." in cli_args:
            os.mkdir("helloworld")
            os.chdir("helloworld")
            expected_name = "helloworld"
        elif "helloworld" in cli_args:
            expected_name = "helloworld"
        else:
            expected_name = "dagster-workspace"

        result = runner.invoke_create_dagster("workspace", *cli_args)
        assert_runner_result(result)

        if "." in cli_args:
            os.chdir("..")

        assert Path(expected_name).exists()
        assert Path(f"{expected_name}/dg.toml").exists()
        assert Path(f"{expected_name}/projects").exists()


def test_scaffold_workspace_already_exists_failure(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        os.mkdir("dagster-workspace")
        result = runner.invoke_create_dagster(
            "workspace",
            "--use-editable-dagster",
            "dagster-workspace",
        )
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


# ########################
# ##### PROJECT
# ########################

# At this time all of our tests are against an editable install of dagster. The reason
# for this is that this package should always be tested against the corresponding version of
# dagster (i.e. from the same commit), and the only way to achieve this right now is
# using the editable install variant of `dg scaffold project`.
#
# Ideally we would have a way to still use the matching dagster-components without using the
# editable install variant, but this will require somehow configuring uv to ensure that it builds
# and returns the local version of the package.


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
        (("--", "foo-bar"), "y\n", {}),
        # Test declining to create a venv
        (("--", "foo-bar"), "n\n", {}),
    ],
    ids=[
        "dirname_cwd",
        "dirname_cwd_preexisting_venv",
        "dirname_cwd_explicit_uv_sync",
        "dirname_cwd_explicit_no_uv_sync",
        "dirname_cwd_no_uv",
        "dirname_arg",
        "dirname_arg_no_venv",
    ],
)
# def test_scaffold_project_outside_workspace_success(monkeypatch) -> None:
def test_scaffold_project_success(
    monkeypatch, cli_args: tuple[str, ...], input_str: Optional[str], opts: dict[str, object]
) -> None:
    use_preexisting_venv = check.opt_bool_elem(opts, "use_preexisting_venv") or False
    no_uv = check.opt_bool_elem(opts, "no_uv") or False
    # Remove when we are able to test without editable install
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
    if no_uv:
        monkeypatch.setattr("create_dagster.cli.scaffold.is_uv_installed", lambda: False)
    with ProxyRunner.test() as runner, runner.isolated_filesystem(), clear_module_from_cache("bar"):
        if "." in cli_args:  # creating in CWD
            os.mkdir("foo-bar")
            os.chdir("foo-bar")
            if use_preexisting_venv:
                subprocess.run(["uv", "venv"], check=True)

        result = runner.invoke_create_dagster(
            "project", "--use-editable-dagster", *cli_args, input=input_str
        )
        assert_runner_result(result)

        if "." in cli_args:  # creating in CWD
            os.chdir("..")

        assert Path("foo-bar").exists()
        assert Path("foo-bar/src/foo_bar").exists()
        assert Path("foo-bar/src/foo_bar/components").exists()
        assert Path("foo-bar/src/foo_bar/defs").exists()
        assert Path("foo-bar/tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # this indicates user opts to create venv and uv.lock
        if not use_preexisting_venv and (
            (input_str and input_str.endswith("y\n")) or "--uv-sync" in cli_args
        ):
            assert Path("foo-bar/.venv").exists()
            assert Path("foo-bar/uv.lock").exists()
        elif use_preexisting_venv:
            assert Path("foo-bar/.venv").exists()
            assert not Path("foo-bar/uv.lock").exists()
        else:
            assert not Path("foo-bar/.venv").exists()
            assert not Path("foo-bar/uv.lock").exists()


def test_scaffold_project_inside_workspace_success(monkeypatch) -> None:
    # Remove when we are able to test without editable install
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        result = runner.invoke_create_dagster(
            "project",
            "projects/foo-bar",
            "--verbose",
            "--uv-sync",
        )
        assert_runner_result(result)
        assert Path("projects/foo-bar").exists()
        assert Path("projects/foo-bar/src/foo_bar").exists()
        assert Path("projects/foo-bar/src/foo_bar/components").exists()
        assert Path("projects/foo-bar/src/foo_bar/defs").exists()
        assert Path("projects/foo-bar/tests").exists()
        assert Path("projects/foo-bar/pyproject.toml").exists()
        assert Path("projects/foo-bar/.gitignore").exists()

        # Check project TOML content
        toml = tomlkit.parse(Path("projects/foo-bar/pyproject.toml").read_text())
        assert get_toml_node(toml, ("tool", "dg", "project", "root_module"), str) == "foo_bar"

        # Check workspace TOML content
        raw_toml = Path("dg.toml").read_text()
        toml = tomlkit.parse(raw_toml)
        assert get_toml_node(toml, ("workspace", "projects", 0, "path"), str) == "projects/foo-bar"

        # Make sure there is an empty line before the new entry
        assert "\n\n[[workspace.projects]]\n" in raw_toml

        # Check venv not created
        assert Path("projects/foo-bar/.venv").exists()
        assert Path("projects/foo-bar/uv.lock").exists()

        # Restore when we are able to test without editable install
        # with open("projects/bar/pyproject.toml") as f:
        #     toml = tomlkit.parse(f.read())
        #
        #     # No tool.uv.sources added without --use-editable-dagster
        #     assert "uv" not in toml["tool"]

        # Create another project, make sure it's appended correctly to the workspace TOML and exists
        # in a different directory.
        result = runner.invoke_create_dagster(
            "project",
            "other_projects/baz",
            "--verbose",
            "--uv-sync",
        )
        assert_runner_result(result)

        # Check workspace TOML content
        raw_toml = Path("dg.toml").read_text()
        toml = tomlkit.parse(raw_toml)
        assert (
            get_toml_node(toml, ("workspace", "projects", 1, "path"), str) == "other_projects/baz"
        )


def test_scaffold_project_inside_workspace_applies_scaffold_project_options(monkeypatch):
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, use_editable_dagster=False),
    ):
        with modify_toml_as_dict(Path("dg.toml")) as toml_dict:
            create_toml_node(
                toml_dict,
                ("workspace", "scaffold_project_options", "use_editable_dagster"),
                True,
            )

        result = runner.invoke_create_dagster(
            "project",
            "projects/foo-bar",
            "--uv-sync",
        )
        assert_runner_result(result)
        # Check that use_editable_dagster was applied
        toml = tomlkit.parse(Path("projects/foo-bar/pyproject.toml").read_text())
        assert has_toml_node(toml, ("tool", "uv", "sources", "dagster"))


EditableOption: TypeAlias = Literal["--use-editable-dagster"]


@pytest.mark.parametrize("option", get_args(EditableOption))
@pytest.mark.parametrize("value_source", ["env_var", "arg"])
def test_scaffold_project_editable_dagster_success(
    value_source: str, option: EditableOption, monkeypatch
) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    if value_source == "env_var":
        monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
        editable_args = [option, "--"]
    else:
        editable_args = [option, str(dagster_git_repo_dir)]
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, use_editable_dagster=False),
    ):
        result = runner.invoke_create_dagster(
            "project",
            "--uv-sync",
            *editable_args,
            "projects/foo-bar",
        )
        assert_runner_result(result)
        assert Path("projects/foo-bar").exists()
        assert Path("projects/foo-bar/pyproject.toml").exists()
        with open("projects/foo-bar/pyproject.toml") as f:
            toml = tomlkit.parse(f.read())
            validate_pyproject_toml_with_editable(toml, option, dagster_git_repo_dir)


def validate_pyproject_toml_with_editable(
    toml: tomlkit.TOMLDocument,
    option: EditableOption,
    repo_root: Path,
) -> None:
    if option == "--use-editable-dagster":
        assert get_toml_node(toml, ("tool", "uv", "sources", "dagster"), dict) == {
            "path": str(repo_root / "python_modules" / "dagster"),
            "editable": True,
        }
        assert get_toml_node(toml, ("tool", "uv", "sources", "dagster-pipes"), dict) == {
            "path": str(repo_root / "python_modules" / "dagster-pipes"),
            "editable": True,
        }
        assert get_toml_node(toml, ("tool", "uv", "sources", "dagster-shared"), dict) == {
            "path": str(repo_root / "python_modules" / "libraries" / "dagster-shared"),
            "editable": True,
        }
        assert get_toml_node(toml, ("tool", "uv", "sources", "dagster-webserver"), dict) == {
            "path": str(repo_root / "python_modules" / "dagster-webserver"),
            "editable": True,
        }
        # Check for presence of one random package with no component to ensure we are
        # preemptively adding all packages
        assert get_toml_node(toml, ("tool", "uv", "sources", "dagstermill"), dict) == {
            "path": str(repo_root / "python_modules" / "libraries" / "dagstermill"),
            "editable": True,
        }
    else:
        assert not has_toml_node(toml, ("tool", "uv", "sources", "dagster"))
        assert not has_toml_node(toml, ("tool", "uv", "sources", "dagster-pipes"))
        assert not has_toml_node(toml, ("tool", "uv", "sources", "dagster-shared"))
        assert not has_toml_node(toml, ("tool", "uv", "sources", "dagster-webserver"))
        assert not has_toml_node(toml, ("tool", "uv", "sources", "dagstermill"))


def test_scaffold_project_use_editable_dagster_env_var_succeeds(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
    monkeypatch.setenv(DEFAULT_EDITABLE_DAGSTER_PROJECTS_ENV_VAR, "1")
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        # We need to use subprocess rather than runner here because the environment variable affects
        # CLI defaults set at process startup.
        subprocess.check_output(["create-dagster", "project", "--uv-sync", "foo-bar"], text=True)
        with open("foo-bar/pyproject.toml") as f:
            toml = tomlkit.parse(f.read())
            validate_pyproject_toml_with_editable(
                toml, "--use-editable-dagster", dagster_git_repo_dir
            )


def test_scaffold_project_python_environment_uv_managed_success(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke_create_dagster(
            "project",
            "foo-bar",
            "--python-environment",
            "uv_managed",
            "--use-editable-dagster",
        )
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/src/foo_bar").exists()
        assert Path("foo-bar/src/foo_bar/components").exists()
        assert Path("foo-bar/src/foo_bar/defs").exists()
        assert Path("foo-bar/tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv not created
        assert Path("foo-bar/.venv").exists()
        assert Path("foo-bar/uv.lock").exists()


@pytest.mark.parametrize("option", get_args(EditableOption))
def test_scaffold_project_editable_dagster_no_env_var_no_value_fails(
    option: EditableOption, monkeypatch
) -> None:
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", "")
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, use_editable_dagster=False),
    ):
        result = runner.invoke_create_dagster("project", option, "--", "bar")
        assert_runner_result(result, exit_0=False)
        assert "requires the `DAGSTER_GIT_REPO_DIR`" in result.output


def test_scaffold_project_already_exists_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        result = runner.invoke_create_dagster("project", "bar", "--uv-sync")
        assert_runner_result(result)
        result = runner.invoke_create_dagster("project", "bar", "--uv-sync")
        assert_runner_result(result, exit_0=False)
        assert "already specifies a project at" in result.output


def test_scaffold_project_non_editable_dagster_dagster_components_executable_exists() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke_create_dagster(
            "project", "bar", "--python-environment", "uv_managed"
        )
        assert_runner_result(result)
        with pushd("bar"):
            result = runner.invoke("list", "plugin-modules", "--verbose")
            assert_runner_result(result)
