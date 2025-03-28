from pathlib import Path
from typing import Final, Optional

import click

from dagster_dg.cli.shared_options import dg_editable_dagster_options, dg_global_options
from dagster_dg.config import (
    DgProjectPythonEnvironment,
    DgRawWorkspaceConfig,
    DgWorkspaceScaffoldProjectOptions,
    normalize_cli_config,
)
from dagster_dg.context import DgContext
from dagster_dg.scaffold import scaffold_project, scaffold_workspace
from dagster_dg.utils import DgClickCommand, exit_with_error
from dagster_dg.utils.telemetry import cli_telemetry_wrapper

# Workspace
_DEFAULT_INIT_PROJECTS_DIR: Final = "projects"


@click.command(name="init", cls=DgClickCommand)
@dg_editable_dagster_options
@dg_global_options
@click.option(
    "--workspace-name",
    type=str,
    help="Name of the workspace folder to create.",
)
@click.option(
    "--project-name",
    type=str,
    help="Name of an initial project folder to create. Setting to an empty string will skip project scaffolding.",
)
@click.option(
    "--project-python-environment",
    default="persistent_uv",
    type=click.Choice(["persistent_uv", "active"]),
    help="Type of Python environment in which to launch subprocesses for the project.",
)
@cli_telemetry_wrapper
def init_command(
    use_editable_dagster: Optional[str],
    workspace_name: Optional[str],
    project_name: Optional[str],
    project_python_environment: DgProjectPythonEnvironment,
    **global_options: object,
):
    """Initialize a new Dagster workspace and a first project within that workspace.

    The scaffolded workspace folder has the following structure:

    \b
    ├── dagster-workspace
    │   ├── projects
    |   |   └── <Dagster projects go here>
    |   ├── libraries
    |   |   └── <Shared packages go here>
    │   └── pyproject.toml

    """  # noqa: D301
    cli_config = normalize_cli_config(global_options, click.get_current_context())

    workspace_path = None

    if workspace_name:
        workspace_config = DgRawWorkspaceConfig(
            scaffold_project_options=DgWorkspaceScaffoldProjectOptions.get_raw_from_cli(
                use_editable_dagster,
            )
        )

        workspace_path = scaffold_workspace(workspace_name, workspace_config)

    if project_name is None:
        project_name = click.prompt(
            "Enter the name of your Dagster project",
            type=str,
            show_default=False,
        ).strip()
        assert project_name is not None, "click.prompt returned None"
    else:
        project_name = project_name.strip()

    if workspace_path:
        dg_context = DgContext.from_file_discovery_and_command_line_config(
            workspace_path, cli_config
        )
        project_path = Path(workspace_path, _DEFAULT_INIT_PROJECTS_DIR, project_name)

    else:
        dg_context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), cli_config)

        project_path = Path(Path.cwd(), project_name)

    if project_path.exists():
        exit_with_error(f"A file or directory already exists at {project_path}.")

    scaffold_project(
        project_path,
        dg_context,
        use_editable_dagster=use_editable_dagster,
        skip_venv=False,
        populate_cache=True,
        python_environment=project_python_environment,
    )

    click.echo("You can create additional projects later by running `dg scaffold project`.")
