import subprocess
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
from dagster_dg.utils import (
    DgClickCommand,
    exit_with_error,
    format_multiline_str,
    get_shortest_path_repr,
    get_venv_activation_cmd,
    is_uv_installed,
    pushd,
)
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
@click.option(
    "--uv-sync/--no-uv-sync",
    is_flag=True,
    default=None,
    help="""
        Preemptively answer the "Run uv sync?" prompt presented after project initialization.
    """.strip(),
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
    uv_sync: Optional[bool],
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

    if uv_sync is True and not is_uv_installed():
        exit_with_error("""
            uv is not installed. Please install uv to use the `--uv-sync` option.
            See https://docs.astral.sh/uv/getting-started/installation/.
        """)
    elif uv_sync is False and python_environment == "uv_managed":
        exit_with_error(
            "The `--uv-sync` option cannot be set to False when using the `--python-environment uv_managed` option."
        )
    elif python_environment == "uv_managed" and not is_uv_installed():
        exit_with_error("""
            uv is not installed. Please install uv to use the `--python-environment uv_managed` option.
            See https://docs.astral.sh/uv/getting-started/installation/.
        """)

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

    if workspace:
        click.echo("You can create additional projects later by running 'dg scaffold project'.")

    venv_path = project_path / ".venv"
    if _should_run_uv_sync(python_environment, venv_path, uv_sync):
        click.echo("Running `uv sync`...")
        with pushd(project_path):
            subprocess.run(["uv", "sync"], check=True)

        click.echo("\nuv.lock and virtual environment created.")
        display_venv_path = get_shortest_path_repr(venv_path)
        click.echo(
            f"""
            Run `{get_venv_activation_cmd(display_venv_path)}` to activate your project's virtual environment.
            """.strip()
        )


def _should_run_uv_sync(
    python_environment: DgProjectPythonEnvironmentFlag,
    venv_path: Path,
    uv_sync_flag: Optional[bool],
) -> bool:
    # This already will have occurred during the scaffolding step
    if python_environment == "uv_managed" or uv_sync_flag is False:
        return False
    # This can force running `uv sync` even if a venv already exists
    elif uv_sync_flag is True:
        return True
    elif venv_path.exists():
        _print_package_install_warning_message()
        return False
    elif is_uv_installed():  # uv_sync_flag is unset (None)
        response = click.prompt(
            format_multiline_str("""
            Run uv sync? This will create the virtual environment you need to activate in
            order to work on this project. (y/n)
        """),
            default="y",
        ).lower()
        if response not in ("y", "n"):
            exit_with_error(f"Invalid response '{response}'. Please enter 'y' or 'n'.")
        if response == "n":
            _print_package_install_warning_message()
        return response == "y"
    else:
        return False


def _print_package_install_warning_message() -> None:
    pip_install_cmd = "pip install --editable ."
    uv_install_cmd = "uv sync"
    click.secho(
        format_multiline_str(
            f"""
            The environment used for your project must include an installation of your project
            package. Please run `{uv_install_cmd}` (for uv) or `{pip_install_cmd}` (for pip) before
            running `dg` commands against your project.
        """,
        ),
        fg="yellow",
    )
