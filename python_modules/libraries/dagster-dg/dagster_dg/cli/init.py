from pathlib import Path

import click

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.scaffold import scaffold_code_location, scaffold_workspace
from dagster_dg.utils import DgClickCommand, exit_with_error


@click.command(name="init", cls=DgClickCommand)
@dg_global_options
@click.pass_context
def init_command(
    context: click.Context,
    **global_options: object,
):
    """Initialize a new Dagster workspace and a first project within that workspace.

    The scaffolded workspace folder has the following structure:

    \b
    ├── workspace
    │   ├── projects
    |   |   └── <Dagster projects go here>
    |   ├── libraries
    |   |   └── <Shared packages go here>
    │   └── pyproject.toml

    """  # noqa: D301
    cli_config = normalize_cli_config(global_options, context)

    workspace_path = Path.cwd() / "workspace"

    # Check if workspace folder already exists
    if workspace_path.exists():
        exit_with_error(
            f"Workspace directory already exists at {workspace_path}. Run `dg scaffold project` to add a new project to the workspace."
        )

    scaffold_workspace(workspace_path)
    workspace_dg_context = DgContext.from_config_file_discovery_and_cli_config(
        workspace_path, cli_config
    )
    project_name = click.prompt("Enter the name of your first Dagster project", type=str)

    if workspace_dg_context.has_project(project_name):
        exit_with_error(f"A project named {project_name} already exists.")

    project_path = workspace_dg_context.get_workspace_project_path(project_name)

    scaffold_code_location(
        project_path,
        workspace_dg_context,
        editable_dagster_root=None,
        skip_venv=False,
        populate_cache=True,
    )
