import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

import click
import pytest
from dagster_dg_core.utils import discover_git_root, ensure_dagster_dg_tests_import
from dagster_shared.record import as_dict, record

ensure_dagster_dg_tests_import()


@record
class CommandThresholds:
    """Configuration for performance test thresholds (in seconds)."""

    create_project: float
    scaffold_asset: float
    scaffold_resource: float
    scaffold_defs_folder_component: float
    list_defs: float
    list_components: float
    list_component_tree: float
    list_envs: float
    list_registry_modules: float
    check_defs: float
    check_yaml: float


def time_command(
    cmd: list[str], cwd: Optional[Path] = None, timeout: float = 120
) -> tuple[float, str]:
    """Execute a command and return (execution_time, stdout)."""
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
        execution_time = time.time() - start_time
        return execution_time, result.stdout
    except subprocess.CalledProcessError as e:
        execution_time = time.time() - start_time
        raise RuntimeError(
            f"Command {' '.join(cmd)} failed after {execution_time:.2f}s: {e.stdout}"
        ) from e
    except subprocess.TimeoutExpired as e:
        execution_time = time.time() - start_time
        raise RuntimeError(f"Command {' '.join(cmd)} timed out after {execution_time:.2f}s") from e


def _assert_under_threshold(actual_time: float, threshold: float, command_name: str) -> None:
    """Assert that command execution time is under threshold."""
    info_line = f"{command_name}: {actual_time:.2f}s (threshold: {threshold:.2f}s)"
    if actual_time > threshold:
        click.echo(f"x {info_line}")
        pytest.fail("{command_name} exceeded performance threshold")
    else:
        click.echo(f"✓ {info_line}")


# This tests the _released_ version of create-dagster for performance. Y
@pytest.mark.slow
@pytest.mark.skipif(
    os.getenv("BUILDKITE") is not None, reason="Skip on Buildkite since test env is unreliable"
)
def test_create_dagster_performance(monkeypatch):
    """Performance test for create-dagster workflow.

    This test creates a new project, scaffolds components, and runs check commands,
    timing each operation against configurable thresholds.
    """
    # Setup editable dagster for testing
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    # Configure thresholds - can be customized via environment variables
    thresholds = CommandThresholds(
        create_project=float(os.getenv("CREATE_DAGSTER_PERF_CREATE_PROJECT", "1.0")),
        scaffold_asset=float(os.getenv("CREATE_DAGSTER_PERF_SCAFFOLD_ASSET", "2.0")),
        scaffold_resource=float(os.getenv("CREATE_DAGSTER_PERF_SCAFFOLD_RESOURCE", "2.0")),
        scaffold_defs_folder_component=float(
            os.getenv("CREATE_DAGSTER_PERF_SCAFFOLD_DEFS_FOLDER_COMPONENT", "2.0")
        ),
        list_defs=float(os.getenv("CREATE_DAGSTER_PERF_LIST_DEFS", "2.0")),
        list_components=float(os.getenv("CREATE_DAGSTER_PERF_LIST_COMPONENTS", "2.0")),
        list_component_tree=float(os.getenv("CREATE_DAGSTER_PERF_LIST_COMPONENT_TREE", "2.0")),
        list_envs=float(os.getenv("CREATE_DAGSTER_PERF_LIST_ENVS", "2.0")),
        list_registry_modules=float(os.getenv("CREATE_DAGSTER_PERF_LIST_REGISTRY_MODULES", "2.0")),
        check_yaml=float(os.getenv("CREATE_DAGSTER_PERF_CHECK_YAML", "2.0")),
        check_defs=float(os.getenv("CREATE_DAGSTER_PERF_CHECK_DEFS", "2.0")),
    )

    click.echo(f"\nPerformance test thresholds: {as_dict(thresholds)}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "test-perf-project"

        try:
            # Create project
            click.echo("\n=== Testing create-dagster project ===")
            create_cmd = [
                "create-dagster",
                "project",
                # "--use-editable-dagster",  # uncomment to test with editable
                "--uv-sync",
                str(project_path),
            ]
            create_time, create_output = time_command(create_cmd, cwd=temp_path)
            _assert_under_threshold(
                create_time, thresholds.create_project, "create-dagster project"
            )
            assert project_path.exists(), "Project directory was not created"
            assert (project_path / "pyproject.toml").exists(), "pyproject.toml not found"
            assert (project_path / "src").exists(), "src directory not found"
            assert (project_path / ".venv").exists(), "Virtual environment not created"

            # Scaffold asset
            click.echo("\n=== Testing dg scaffold defs asset ===")
            scaffold_asset_cmd = ["dg", "scaffold", "defs", "asset", "my_test_asset.py"]
            asset_time, asset_output = time_command(
                scaffold_asset_cmd, cwd=project_path, timeout=thresholds.scaffold_asset + 10
            )
            _assert_under_threshold(asset_time, thresholds.scaffold_asset, "dg scaffold defs asset")

            # Scaffold resource
            click.echo("\n=== Testing dg scaffold defs resource ===")
            scaffold_resource_command = [
                "dg",
                "scaffold",
                "defs",
                "resources",
                "my_test_resource.py",
            ]
            resource_time, resource_output = time_command(
                scaffold_resource_command,
                cwd=project_path,
                timeout=thresholds.scaffold_resource + 10,
            )
            _assert_under_threshold(
                resource_time, thresholds.scaffold_resource, "dg scaffold resource"
            )

            # Scaffold defs folder component
            click.echo("\n=== Testing dg scaffold defs DefsFolderComponent ===")
            scaffold_defs_folder_component_cmd = [
                "dg",
                "scaffold",
                "defs",
                "dagster.DefsFolderComponent",
                "my_defs_folder",
            ]
            scaffold_defs_folder_component_time, scaffold_defs_folder_component_output = (
                time_command(
                    scaffold_defs_folder_component_cmd,
                    cwd=project_path,
                    timeout=thresholds.scaffold_defs_folder_component + 10,
                )
            )
            _assert_under_threshold(
                scaffold_defs_folder_component_time,
                thresholds.scaffold_defs_folder_component,
                "dg scaffold defs DefsFolderComponent",
            )

            # List components
            click.echo("\n=== Testing dg list components ===")
            list_components_command = ["dg", "list", "components"]
            list_components_time, list_components_output = time_command(
                list_components_command, cwd=project_path, timeout=thresholds.list_components + 10
            )
            _assert_under_threshold(
                list_components_time, thresholds.list_components, "dg list components"
            )

            # List component tree
            click.echo("\n=== Testing dg list component-tree ===")
            list_component_tree_command = ["dg", "list", "component-tree"]
            list_component_tree_time, list_component_tree_output = time_command(
                list_component_tree_command,
                cwd=project_path,
                timeout=thresholds.list_component_tree + 10,
            )
            _assert_under_threshold(
                list_component_tree_time, thresholds.list_component_tree, "dg list component-tree"
            )

            # List envs
            click.echo("\n=== Testing dg list envs ===")
            list_envs_command = ["dg", "list", "registry-modules"]
            list_envs_time, list_envs_output = time_command(
                list_envs_command,
                cwd=project_path,
                timeout=thresholds.list_envs + 10,
            )
            _assert_under_threshold(list_envs_time, thresholds.list_envs, "dg list envs")

            # List component tree
            click.echo("\n=== Testing dg list registry-modules ===")
            list_registry_modules_command = ["dg", "list", "registry-modules"]
            list_registry_modules_time, list_registry_modules_output = time_command(
                list_registry_modules_command,
                cwd=project_path,
                timeout=thresholds.list_registry_modules + 10,
            )
            _assert_under_threshold(
                list_registry_modules_time,
                thresholds.list_registry_modules,
                "dg list registry-modules",
            )

            # Check yaml
            click.echo("\n=== Testing dg check yaml ===")
            check_yaml_cmd = ["dg", "check", "yaml"]
            check_yaml_time, check_yaml_output = time_command(
                check_yaml_cmd, cwd=project_path, timeout=thresholds.check_yaml + 10
            )
            _assert_under_threshold(check_yaml_time, thresholds.check_yaml, "dg check yaml")

            # Check defs
            click.echo("\n=== Testing dg check defs ===")
            check_defs_cmd = ["dg", "check", "defs"]
            check_defs_time, check_defs_output = time_command(
                check_defs_cmd, cwd=project_path, timeout=thresholds.check_defs + 10
            )
            _assert_under_threshold(check_defs_time, thresholds.check_defs, "dg check defs")

            click.echo("\n✅ All performance tests passed!")
            assert False

        except Exception as e:
            click.echo(f"\n❌ Performance test failed: {e}")
            if project_path.exists():
                click.echo(f"Project artifacts left at: {project_path}")
            raise
