from pathlib import Path
from typing import Final, Optional, get_args

import click

from dagster_dg.cli.shared_options import dg_editable_dagster_options, dg_global_options
from dagster_dg.config import (
    DgProjectPythonEnvironment,
    DgProjectPythonEnvironmentFlag,
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
    "--workspace",
    is_flag=True,
    default=False,
    help="Create a workspace instead of a project at the given path.",
)
@click.option(
    "--project-name",
    type=str,
    help="Name of an initial project folder to create.",
)
@click.option(
    "--python-environment",
    default="active",
    type=click.Choice(get_args(DgProjectPythonEnvironmentFlag)),
    help="Type of Python environment in which to launch subprocesses for the project.",
)
@click.argument(
    "dirname",
    required=False,
)
@cli_telemetry_wrapper
def init_command(
    dirname: Optional[str],
    use_editable_dagster: Optional[str],
    workspace: bool,
    project_name: Optional[str],
    python_environment: DgProjectPythonEnvironmentFlag,
    **global_options: object,
):
    """Initialize a new Dagster project, optionally inside a workspace.

    By default, only a standalone project is created. The project will be created in a new directory specified by DIRNAME. If DIRNAME is not specified, the user will be prompted for it.

    If the --workspace flag is passed, a workspace will be created in DIRNAME and a project created inside the workspace. If DIRNAME is not passed, the user will be prompted for it. The project name can be specified with the --project-name option, or the user will be prompted for it.

    In either case, "." can be passed as DIRNAME to create the new project or workspace inside the existing working directory.

    Examples:
        dg init
            Scaffold a new project in a new directory `<project_name>`. Prompts for `<project_name>`.
        dg init .
            Scaffold a new project in the CWD. The project name is taken from the last component of the CWD.
        dg init PROJECT_NAME
            Scaffold a new project in new directory PROJECT_NAME.
        dg init --workspace
            Scaffold a new workspace in a new directory `<workspace_name>`. Prompts for `<workspace_name>`. Scaffold a new project inside this workspace at projects/<project_name>. Prompts for `<project_name>`.
        dg init --workspace .
            Scaffold a new workspace in the CWD. Scaffold a new project inside this workspace at projects/<project_name>. Prompts for `<project_name>`.
        dg init --workspace WORKSPACE_NAME
            Scaffold a new workspace in a new directory WORKSPACE_NAME. Scaffold a new project inside this workspace at projects/<project_name>. Prompt for the project name.
        dg init --workspace --project-name PROJECT_NAME .
            Scaffold a new workspace in the CWD. Scaffold a new project inside this workspace at projects/PROJECT_NAME.

    Created projects will have the following structure:

    ├── src
    │   └── <project_name>
    │       ├── __init__.py
    │       ├── definitions.py
    │       ├── defs
    │       │   └── __init__.py
    │       └── lib
    │           └── __init__.py
    ├── tests
    │   └── __init__.py
    └── pyproject.toml

    If a workspace is created, it will have the following structure:

    ├── <workspace_name>
    │   ├── projects
    |   |   └── <Dagster projects go here>
    │   └── pyproject.toml

    """
    cli_config = normalize_cli_config(global_options, click.get_current_context())

    workspace_dirname = None

    if workspace:
        workspace_config = DgRawWorkspaceConfig(
            scaffold_project_options=DgWorkspaceScaffoldProjectOptions.get_raw_from_cli(
                use_editable_dagster,
            )
        )
        workspace_dirname = dirname or click.prompt(
            "Enter directory name for new workspace (. to use cwd)", default=".", type=str
        )
        workspace_dirname = scaffold_workspace(workspace_dirname, workspace_config)
        specified_project_name = project_name
        dg_context = DgContext.from_file_discovery_and_command_line_config(
            workspace_dirname, cli_config
        )
        project_container = Path(workspace_dirname, _DEFAULT_INIT_PROJECTS_DIR)
    else:
        if dirname and project_name:
            exit_with_error(
                "Cannot specify both a DIRNAME and --project-name if --workspace is not passed."
            )
        specified_project_name = dirname or project_name
        dg_context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), cli_config)
        project_container = Path.cwd()

    project_name = (
        specified_project_name
        or click.prompt(
            "Enter the name of your Dagster project",
            type=str,
            show_default=False,
        ).strip()
    )
    assert project_name is not None, "click.prompt returned None"
    project_path = project_container if project_name == "." else project_container / project_name

    if project_name != "." and project_path.exists():
        exit_with_error(f"A file or directory already exists at {project_path}.")

    scaffold_project(
        project_path,
        dg_context,
        use_editable_dagster=use_editable_dagster,
        populate_cache=True,
        python_environment=DgProjectPythonEnvironment.from_flag(python_environment),
    )

    click.echo("You can create additional projects later by running 'dg scaffold project'.")
