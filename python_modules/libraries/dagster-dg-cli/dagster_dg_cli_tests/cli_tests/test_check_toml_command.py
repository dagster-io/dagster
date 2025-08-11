import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import pytest
from dagster_test.dg_utils.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
    modify_dg_toml_config_as_dict,
)


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a minimal dg project structure for testing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create src structure
    src_dir = project_dir / "src" / "test_project"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").touch()

    # Create defs directory
    defs_dir = src_dir / "defs"
    defs_dir.mkdir()
    (defs_dir / "__init__.py").touch()

    return project_dir


def gen_expected_output(
    in_project: bool,
    in_workspace: bool,
    project_errors: Optional[str] = None,
    workspace_errors: Optional[str] = None,
) -> str:
    lines = ["Checking TOML configuration files..."]

    if in_project:
        lines.append("")
        lines.append(
            f"Found project configuration file: {Path.cwd()}/pyproject.toml",
        )
        if project_errors:
            lines.append(
                f"Project configuration file errors:\n\n{textwrap.dedent(project_errors).strip()}"
            )
        else:
            lines.append("Project configuration file is valid.")
        lines.append("")

    if in_workspace:
        lines.append("")
        config_path = (Path.cwd().parent / "dg.toml") if in_project else Path.cwd() / "dg.toml"
        lines.append(f"Found workspace configuration file: {config_path}")
        if workspace_errors:
            lines.append(
                f"Workspace configuration file errors:\n\n{textwrap.dedent(workspace_errors).strip()}"
            )
        else:
            lines.append("Workspace configuration file is valid.")
        lines.append("")

    if not project_errors and not workspace_errors:
        lines.append("All TOML configuration files are valid.")
    else:
        lines.append("One or more TOML configuration files contain errors.")

    return "\n".join(lines)


@contextmanager
def _get_filesystem_context(
    in_project: bool, in_workspace: bool, runner: ProxyRunner
) -> Iterator[None]:
    if in_project:
        fs_context = isolated_example_project_foo_bar(runner, in_workspace=in_workspace)
    elif in_workspace:
        fs_context = isolated_example_workspace(runner)
    else:
        fs_context = runner.isolated_filesystem()
    with fs_context:
        yield


@pytest.mark.parametrize("in_project", [True, False])
@pytest.mark.parametrize("in_workspace", [True, False])
def test_check_toml_valid(in_project: bool, in_workspace: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        _get_filesystem_context(in_project, in_workspace, runner),
    ):
        result = runner.invoke("check", "toml")
        assert_runner_result(result)
        expected_output = gen_expected_output(in_project=in_project, in_workspace=in_workspace)
        assert result.output.strip() == expected_output.strip()


@pytest.mark.parametrize("in_workspace", [True, False])
def test_check_toml_with_project_config_errors(in_workspace: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        _get_filesystem_context(in_project=True, in_workspace=in_workspace, runner=runner),
    ):
        with modify_dg_toml_config_as_dict(Path("pyproject.toml")) as toml:
            toml["project"]["root_module"] = 123
            toml["invalid_key"] = True

        expected_output = gen_expected_output(
            in_project=True,
            in_workspace=in_workspace,
            project_errors="""
                Invalid value for `tool.dg.project.root_module`:
                    Expected: str
                    Received: 123
                Unrecognized field at `tool.dg`:
                    invalid_key
            """,
        )
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=False)
        assert result.output.strip() == expected_output.strip()


@pytest.mark.parametrize("in_project", [True, False])
def test_check_toml_with_workspace_config_errors(in_project: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        _get_filesystem_context(in_project=in_project, in_workspace=True, runner=runner),
    ):
        config_path = Path.cwd().parent / "dg.toml" if in_project else Path.cwd() / "dg.toml"
        with modify_dg_toml_config_as_dict(config_path) as toml:
            toml["workspace"]["projects"] = [1]
            toml["invalid_key"] = True

        expected_output = gen_expected_output(
            in_project=in_project,
            in_workspace=True,
            workspace_errors="""
                Invalid value for `workspace.projects[0]`:
                    Expected: dict
                    Received: 1
                Unrecognized field at `<root>`:
                    invalid_key
            """,
        )
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=False)
        assert result.output.strip() == expected_output.strip()


def test_check_toml_with_root_and_workspace_config_errors() -> None:
    with (
        ProxyRunner.test() as runner,
        _get_filesystem_context(in_project=True, in_workspace=True, runner=runner),
    ):
        with modify_dg_toml_config_as_dict(Path("pyproject.toml")) as toml:
            toml["project"]["root_module"] = 123
            toml["invalid_key"] = True

        with modify_dg_toml_config_as_dict(Path("../dg.toml")) as toml:
            toml["workspace"]["projects"].append(1)
            toml["invalid_key"] = True

        expected_output = gen_expected_output(
            in_project=True,
            in_workspace=True,
            project_errors="""
                Invalid value for `tool.dg.project.root_module`:
                    Expected: str
                    Received: 123
                Unrecognized field at `tool.dg`:
                    invalid_key
            """,
            workspace_errors="""
                Invalid value for `workspace.projects[1]`:
                    Expected: dict
                    Received: 1
                Unrecognized field at `<root>`:
                    invalid_key
            """,
        )
        result = runner.invoke("check", "toml")
        assert_runner_result(result, exit_0=False)
        assert result.output.strip() == expected_output.strip()
