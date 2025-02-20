from pathlib import Path
from typing import Optional

import click

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.scaffold import scaffold_project, scaffold_workspace
from dagster_dg.utils import DgClickCommand, exit_with_error


@click.command(name="init", cls=DgClickCommand)
@click.option(
    "--use-editable-dagster",
    type=str,
    flag_value="TRUE",
    is_flag=False,
    default=None,
    help=(
        "Install Dagster package dependencies from a local Dagster clone. Accepts a path to local Dagster clone root or"
        " may be set as a flag (no value is passed). If set as a flag,"
        " the location of the local Dagster clone will be read from the `DAGSTER_GIT_REPO_DIR` environment variable."
    ),
)
@dg_global_options
@click.pass_context
def init_command(
    context: click.Context,
    use_editable_dagster: Optional[str],
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

    project_name = click.prompt(
        "Enter the name of your first Dagster project (or press Enter to continue without creating a project)",
        type=str,
    ).strip()

    if not project_name:
        click.echo(
            "Continuing without adding a project. You can create one later by running `dg scaffold project`."
        )
    else:
        workspace_dg_context = DgContext.from_config_file_discovery_and_cli_config(
            workspace_path, cli_config
        )
        if workspace_dg_context.has_project(project_name):
            exit_with_error(f"A project named {project_name} already exists.")

        project_path = workspace_dg_context.get_workspace_project_path(project_name)

        scaffold_project(
            project_path,
            workspace_dg_context,
            use_editable_dagster=use_editable_dagster,
            skip_venv=False,
            populate_cache=True,
        )

        click.echo("You can create additional projects later by running `dg scaffold project`.")
