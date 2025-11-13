import os
from pathlib import Path

import pytest
import yaml
from dagster_dg_cli.cli.utils import create_temp_workspace_file
from dagster_dg_core.context import DgContext
from dagster_dg_core.utils import activate_venv, discover_git_root, environ, is_windows, pushd
from dagster_test.dg_utils.utils import (
    ProxyRunner,
    assert_runner_result,
    install_editable_dg_dev_packages_to_venv,
    isolated_example_workspace,
)


def parse_workspace_yaml(workspace_file_path: str) -> dict:
    """Parse a workspace.yaml file and return its contents."""
    return yaml.safe_load(Path(workspace_file_path).read_text())


def get_workspace_entries(workspace_data: dict) -> list[dict]:
    """Extract load_from entries from parsed workspace data."""
    return workspace_data.get("load_from", [])


def has_executable_path(entry: dict) -> bool:
    """Check if a workspace entry has executable_path in its python_module section."""
    python_module = entry.get("python_module", {})
    return "executable_path" in python_module


def get_executable_path(entry: dict) -> str | None:
    """Get the executable_path from a workspace entry, or None if not present."""
    python_module = entry.get("python_module", {})
    return python_module.get("executable_path")


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_workspace_yaml_includes_executable_path_by_default():
    """Test that workspace.yaml includes executable_path when use_active_venv=False (default)."""
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, create_venv=True) as workspace_path,
        environ({"DAGSTER_GIT_REPO_DIR": dagster_git_repo_dir}),
    ):
        venv_path = workspace_path / ".venv"
        install_editable_dg_dev_packages_to_venv(venv_path)

        with activate_venv(venv_path), pushd(workspace_path):
            # Create a project
            result = runner.invoke_create_dagster(
                "project", "--use-editable-dagster", "projects/test-project", "--uv-sync"
            )
            assert_runner_result(result)

            # Generate workspace file WITHOUT use_active_venv flag
            dg_context = DgContext.for_workspace_or_project_environment(workspace_path, {})
            with create_temp_workspace_file(dg_context, use_active_venv=False) as workspace_file:
                workspace_data = parse_workspace_yaml(workspace_file)
                entries = get_workspace_entries(workspace_data)

                # Verify we have at least one entry
                assert len(entries) > 0, "Expected at least one workspace entry"

                # Verify all entries have executable_path
                for entry in entries:
                    assert has_executable_path(entry), f"Expected executable_path in entry: {entry}"
                    exec_path = get_executable_path(entry)
                    assert exec_path is not None
                    assert Path(exec_path).exists(), f"Executable path does not exist: {exec_path}"


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_workspace_yaml_excludes_executable_path_with_use_active_venv():
    """Test that workspace.yaml omits executable_path when use_active_venv=True."""
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, create_venv=True) as workspace_path,
        environ({"DAGSTER_GIT_REPO_DIR": dagster_git_repo_dir}),
    ):
        venv_path = workspace_path / ".venv"
        install_editable_dg_dev_packages_to_venv(venv_path)

        with activate_venv(venv_path), pushd(workspace_path):
            # Create a project
            result = runner.invoke_create_dagster(
                "project", "--use-editable-dagster", "projects/test-project", "--uv-sync"
            )
            assert_runner_result(result)

            # Generate workspace file WITH use_active_venv flag
            dg_context = DgContext.for_workspace_or_project_environment(workspace_path, {})
            with create_temp_workspace_file(dg_context, use_active_venv=True) as workspace_file:
                workspace_data = parse_workspace_yaml(workspace_file)
                entries = get_workspace_entries(workspace_data)

                # Verify we have at least one entry
                assert len(entries) > 0, "Expected at least one workspace entry"

                # Verify NO entries have executable_path
                for entry in entries:
                    assert not has_executable_path(entry), (
                        f"Did not expect executable_path in entry: {entry}"
                    )


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_workspace_yaml_multiple_projects_without_use_active_venv():
    """Test that multiple projects all get executable_path when use_active_venv=False."""
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, create_venv=True) as workspace_path,
        environ({"DAGSTER_GIT_REPO_DIR": dagster_git_repo_dir}),
    ):
        venv_path = workspace_path / ".venv"
        install_editable_dg_dev_packages_to_venv(venv_path)

        with activate_venv(venv_path), pushd(workspace_path):
            # Create multiple projects
            result = runner.invoke_create_dagster(
                "project", "--use-editable-dagster", "projects/project-1", "--uv-sync"
            )
            assert_runner_result(result)

            result = runner.invoke_create_dagster(
                "project", "--use-editable-dagster", "projects/project-2", "--uv-sync"
            )
            assert_runner_result(result)

            # Generate workspace file WITHOUT use_active_venv
            dg_context = DgContext.for_workspace_or_project_environment(workspace_path, {})
            with create_temp_workspace_file(dg_context, use_active_venv=False) as workspace_file:
                workspace_data = parse_workspace_yaml(workspace_file)
                entries = get_workspace_entries(workspace_data)

                # Verify we have two entries
                assert len(entries) == 2, f"Expected 2 workspace entries, got {len(entries)}"

                # Verify all entries have executable_path
                for entry in entries:
                    assert has_executable_path(entry), f"Expected executable_path in entry: {entry}"


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_workspace_yaml_multiple_projects_with_use_active_venv():
    """Test that multiple projects omit executable_path when use_active_venv=True."""
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, create_venv=True) as workspace_path,
        environ({"DAGSTER_GIT_REPO_DIR": dagster_git_repo_dir}),
    ):
        venv_path = workspace_path / ".venv"
        install_editable_dg_dev_packages_to_venv(venv_path)

        with activate_venv(venv_path), pushd(workspace_path):
            # Create multiple projects
            result = runner.invoke_create_dagster(
                "project", "--use-editable-dagster", "projects/project-1", "--uv-sync"
            )
            assert_runner_result(result)

            result = runner.invoke_create_dagster(
                "project", "--use-editable-dagster", "projects/project-2", "--uv-sync"
            )
            assert_runner_result(result)

            # Generate workspace file WITH use_active_venv
            dg_context = DgContext.for_workspace_or_project_environment(workspace_path, {})
            with create_temp_workspace_file(dg_context, use_active_venv=True) as workspace_file:
                workspace_data = parse_workspace_yaml(workspace_file)
                entries = get_workspace_entries(workspace_data)

                # Verify we have two entries
                assert len(entries) == 2, f"Expected 2 workspace entries, got {len(entries)}"

                # Verify NO entries have executable_path
                for entry in entries:
                    assert not has_executable_path(entry), (
                        f"Did not expect executable_path in entry: {entry}"
                    )


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_workspace_yaml_preserves_other_fields():
    """Test that use_active_venv only affects executable_path, not other fields."""
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, create_venv=True) as workspace_path,
        environ({"DAGSTER_GIT_REPO_DIR": dagster_git_repo_dir}),
    ):
        venv_path = workspace_path / ".venv"
        install_editable_dg_dev_packages_to_venv(venv_path)

        with activate_venv(venv_path), pushd(workspace_path):
            # Create a project
            result = runner.invoke_create_dagster(
                "project", "--use-editable-dagster", "projects/test-project", "--uv-sync"
            )
            assert_runner_result(result)

            # Generate workspace file WITH use_active_venv
            dg_context = DgContext.for_workspace_or_project_environment(workspace_path, {})
            with create_temp_workspace_file(dg_context, use_active_venv=True) as workspace_file:
                workspace_data = parse_workspace_yaml(workspace_file)
                entries = get_workspace_entries(workspace_data)

                assert len(entries) > 0
                entry = entries[0]
                python_module = entry.get("python_module", {})

                # Verify essential fields are present
                assert "working_directory" in python_module
                assert "module_name" in python_module
                assert "location_name" in python_module

                # Verify executable_path is NOT present
                assert "executable_path" not in python_module


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_virtual_env_environment_variable_set_with_activate_venv():
    """Test that activate_venv context manager correctly sets VIRTUAL_ENV."""
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, create_venv=True) as workspace_path,
        environ({"DAGSTER_GIT_REPO_DIR": dagster_git_repo_dir}),
    ):
        venv_path = workspace_path / ".venv"

        # Before activation, VIRTUAL_ENV might not be set
        original_virtual_env = os.environ.get("VIRTUAL_ENV")

        with activate_venv(venv_path):
            # Inside context, VIRTUAL_ENV should be set
            current_virtual_env = os.environ.get("VIRTUAL_ENV")
            assert current_virtual_env is not None
            assert Path(current_virtual_env) == venv_path.absolute()

        # After context, VIRTUAL_ENV should be restored
        restored_virtual_env = os.environ.get("VIRTUAL_ENV")
        assert restored_virtual_env == original_virtual_env
