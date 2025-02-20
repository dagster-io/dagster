from pathlib import Path

import click

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.scaffold import scaffold_code_location, scaffold_workspace
from dagster_dg.utils import DgClickCommand


@click.command(name="init", cls=DgClickCommand)
@dg_global_options
@click.pass_context
def init_command(
    context: click.Context,
    **global_options: object,
):
    """Initialize a new Dagster workspace and a first project within that workspace.

    The workspace file structure defines a Python package with some pre-existing internal
    structure:

    \b
    ├── workspace
    │   ├── __init__.py
    │   ├── projects
    |       └── <Dagster projects go here>
    |   ├── libraries
    |       └── <Shared packages go here>
    │   └── pyproject.toml

    """  # noqa: D301
    cli_config = normalize_cli_config(global_options, context)

    #    dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)

    workspace_path = Path.cwd() / "workspace"

    # Check to see if there is already a workspace folder either in this folde
    scaffold_workspace(workspace_path)

    # Check to see if a project already exists
    project_name = click.prompt("Enter the name of your first Dagster project", type=str)

    project_path = workspace_path / "projects" / project_name

    project_dg_context = DgContext.from_config_file_discovery_and_cli_config(
        project_path, cli_config
    )

    scaffold_code_location(
        project_path,
        project_dg_context,
        editable_dagster_root=None,
        skip_venv=False,
        populate_cache=True,
    )
