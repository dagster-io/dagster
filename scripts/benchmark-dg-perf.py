import argparse
import os
import subprocess
import tempfile
import textwrap
import time
from pathlib import Path

import click
from dagster_dg_core.utils import activate_venv, pushd
from dagster_shared.record import as_dict, record

"""Performance test for create-dagster workflow.

This test creates a new project, scaffolds components, and runs check commands,
timing each operation against configurable thresholds.
"""

parser = argparse.ArgumentParser(
    prog="benchmark-dg-perf",
    description=textwrap.dedent("""
        Simulate a typical create-dagster workflow. Create a project, scaffold some components, run
        some check commands, etc. Each step is timed and compared against a threshold value. Default
        threshold values can be found in the script body. Any threshold can be overridden by setting
        BENCHMARK_DG_PERF_<STEP_NAME>=<THRESHOLD_IN_SECONDS>.

        By default this will use an editable dg install from your local checkout (this is located by
        looking for the DAGSTER_GIT_REPO_DIR environment variable. You can pass --latest-release
        to instead use the latest released `create-dagster` and `dg`.
    """).strip(),
)

parser.add_argument(
    "--latest-release",
    action="store_true",
    default=False,
    help=(
        "Use the latest released versions of `create-dagster` and `dg` instead of the local checkout."
    ),
)


# ########################
# ##### MAIN
# ########################


def main(use_latest_release: bool = False) -> None:
    if not os.getenv("DAGSTER_GIT_REPO_DIR"):
        raise RuntimeError(
            "DAGSTER_GIT_REPO_DIR environment variable is not set. "
            "Please set it to the root of your Dagster git repository."
        )

    if use_latest_release:
        click.echo("Running dg performance benchmark using latest released versions...")
    else:
        click.echo(
            f"Running dg performance benchmark using locally checked out dagster at:\n  {os.getenv('DAGSTER_GIT_REPO_DIR')}..."
        )

    # Configure thresholds - can be customized via environment variables
    thresholds = CommandThresholds(
        create_project=float(os.getenv("BENCHMARK_DG_PERF_CREATE_PROJECT", "1.0")),
        scaffold_asset=float(os.getenv("BENCHMARK_DG_PERF_SCAFFOLD_ASSET", "2.0")),
        scaffold_resource=float(os.getenv("BENCHMARK_DG_PERF_SCAFFOLD_RESOURCE", "2.0")),
        scaffold_defs_folder_component=float(
            os.getenv("BENCHMARK_DG_PERF_SCAFFOLD_DEFS_FOLDER_COMPONENT", "2.0")
        ),
        list_defs=float(os.getenv("BENCHMARK_DG_PERF_LIST_DEFS", "2.0")),
        list_components=float(os.getenv("BENCHMARK_DG_PERF_LIST_COMPONENTS", "2.0")),
        list_component_tree=float(os.getenv("BENCHMARK_DG_PERF_LIST_COMPONENT_TREE", "2.0")),
        list_envs=float(os.getenv("BENCHMARK_DG_PERF_LIST_ENVS", "2.0")),
        list_registry_modules=float(os.getenv("BENCHMARK_DG_PERF_LIST_REGISTRY_MODULES", "2.0")),
        check_yaml=float(os.getenv("BENCHMARK_DG_PERF_CHECK_YAML", "2.0")),
        check_defs=float(os.getenv("BENCHMARK_DG_PERF_CHECK_DEFS", "2.0")),
    )

    click.echo("\nPerformance test thresholds:")
    for key, value in as_dict(thresholds).items():
        click.echo(f"  {key}: {value:.2f}s")
    click.echo("")  # Add a blank line for readability

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "test-perf-project"

        # Create project
        create_cmd = [
            *(["uvx", "create-dagster@latest"] if use_latest_release else ["create-dagster"]),
            "project",
            *(["--use-editable-dagster"] if not use_latest_release else []),
            "--uv-sync",
            str(project_path),
        ]
        create_time = _time_command(create_cmd, cwd=temp_path)
        _report_step_result(create_time, thresholds.create_project, "create-dagster project")
        assert project_path.exists(), "Project directory was not created"
        assert (project_path / "pyproject.toml").exists(), "pyproject.toml not found"
        assert (project_path / "src").exists(), "src directory not found"
        assert (project_path / "src" / "test_perf_project").exists(), "src directory not found"
        assert (project_path / ".venv").exists(), "Virtual environment not created"

        with pushd(project_path), activate_venv(".venv"):
            # Scaffold asset
            scaffold_asset_cmd = ["dg", "scaffold", "defs", "asset", "my_test_asset.py"]
            asset_time = _time_command(
                scaffold_asset_cmd, cwd=project_path, timeout=thresholds.scaffold_asset + 10
            )
            _report_step_result(asset_time, thresholds.scaffold_asset, "dg scaffold defs asset")

            # Scaffold resource
            scaffold_resource_command = [
                "dg",
                "scaffold",
                "defs",
                "resources",
                "my_test_resource.py",
            ]
            resource_time = _time_command(
                scaffold_resource_command,
                cwd=project_path,
                timeout=thresholds.scaffold_resource + 10,
            )
            _report_step_result(resource_time, thresholds.scaffold_resource, "dg scaffold resource")

            # Scaffold defs folder component
            scaffold_defs_folder_component_cmd = [
                "dg",
                "scaffold",
                "defs",
                "dagster.DefsFolderComponent",
                "my_defs_folder",
            ]
            scaffold_defs_folder_component_time = _time_command(
                scaffold_defs_folder_component_cmd,
                cwd=project_path,
                timeout=thresholds.scaffold_defs_folder_component + 10,
            )
            _report_step_result(
                scaffold_defs_folder_component_time,
                thresholds.scaffold_defs_folder_component,
                "dg scaffold defs DefsFolderComponent",
            )

            # List components
            list_components_command = ["dg", "list", "components"]
            list_components_time = _time_command(
                list_components_command, cwd=project_path, timeout=thresholds.list_components + 10
            )
            _report_step_result(
                list_components_time, thresholds.list_components, "dg list components"
            )

            # List component tree
            list_component_tree_command = ["dg", "list", "component-tree"]
            list_component_tree_time = _time_command(
                list_component_tree_command,
                cwd=project_path,
                timeout=thresholds.list_component_tree + 10,
            )
            _report_step_result(
                list_component_tree_time, thresholds.list_component_tree, "dg list component-tree"
            )

            # List defs
            list_defs_command = ["dg", "list", "defs"]
            list_defs_time = _time_command(
                list_defs_command, cwd=project_path, timeout=thresholds.list_defs + 10
            )
            _report_step_result(list_defs_time, thresholds.list_defs, "dg list defs")

            # List envs
            list_envs_command = ["dg", "list", "envs"]
            list_envs_time = _time_command(
                list_envs_command,
                cwd=project_path,
                timeout=thresholds.list_envs + 10,
            )
            _report_step_result(list_envs_time, thresholds.list_envs, "dg list envs")

            # List registry modules
            list_registry_modules_command = ["dg", "list", "registry-modules"]
            list_registry_modules_time = _time_command(
                list_registry_modules_command,
                cwd=project_path,
                timeout=thresholds.list_registry_modules + 10,
            )
            _report_step_result(
                list_registry_modules_time,
                thresholds.list_registry_modules,
                "dg list registry-modules",
            )

            # Check yaml
            check_yaml_cmd = ["dg", "check", "yaml"]
            check_yaml_time = _time_command(
                check_yaml_cmd, cwd=project_path, timeout=thresholds.check_yaml + 10
            )
            _report_step_result(check_yaml_time, thresholds.check_yaml, "dg check yaml")

            # Check defs
            check_defs_cmd = ["dg", "check", "defs"]
            check_defs_time = _time_command(
                check_defs_cmd, cwd=project_path, timeout=thresholds.check_defs + 10
            )
            _report_step_result(check_defs_time, thresholds.check_defs, "dg check defs")


# ########################
# ##### HELPERS
# ########################


def _time_command(cmd: list[str], cwd: Path | None = None, timeout: float = 120) -> float:
    """Execute a command and return (execution_time, stdout)."""
    start_time = time.time()
    try:
        subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
        execution_time = time.time() - start_time
        return execution_time
    except subprocess.CalledProcessError as e:
        execution_time = time.time() - start_time
        raise RuntimeError(
            f"Command {' '.join(cmd)} failed after {execution_time:.2f}s" + e.stderr
        ) from e
    except subprocess.TimeoutExpired as e:
        execution_time = time.time() - start_time
        raise RuntimeError(f"Command {' '.join(cmd)} timed out after {execution_time:.2f}s") from e


def _report_step_result(actual_time: float, threshold: float, command_name: str) -> None:
    """Assert that command execution time is under threshold."""
    info_line = f"{command_name}: {actual_time:.2f}s (threshold: {threshold:.2f}s)"
    if actual_time > threshold:
        click.secho(f"x {info_line}", fg="red", bold=True)
    else:
        click.secho(f"✓ {info_line}", fg="green", bold=True)


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


if __name__ == "__main__":
    args = parser.parse_args()
    main(use_latest_release=args.latest_release)
