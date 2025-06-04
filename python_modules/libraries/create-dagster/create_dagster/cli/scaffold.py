import subprocess
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import (
    DgProjectPythonEnvironment,
    DgProjectPythonEnvironmentFlag,
    DgRawWorkspaceConfig,
    DgWorkspaceScaffoldProjectOptions,
    discover_workspace_root,
    normalize_cli_config,
)
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_editable_dagster_options, dg_global_options
from dagster_dg_core.utils import (
    DgClickCommand,
    exit_with_error,
    format_multiline_str,
    get_shortest_path_repr,
    get_venv_activation_cmd,
    is_uv_installed,
    pushd,
)
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from typing_extensions import get_args

from create_dagster.scaffold import scaffold_project, scaffold_workspace


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
            A `uv` installation was detected. Run `uv sync`? This will create a uv.lock file and the
            virtual environment you need to activate in order to work on this project. If you wish
            to use a non-uv package manager, choose "n". (y/n)
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


# ########################
# ##### PROJECT
# ########################


@click.command(
    name="project",
    cls=DgClickCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.argument("path", type=Path)
@click.option(
    "--python-environment",
    default="active",
    type=click.Choice(get_args(DgProjectPythonEnvironmentFlag)),
    help="Type of Python environment in which to launch subprocesses for this project.",
)
@click.option(
    "--uv-sync/--no-uv-sync",
    is_flag=True,
    default=None,
    help="""
        Preemptively answer the "Run uv sync?" prompt presented after project initialization.
    """.strip(),
)
@dg_editable_dagster_options
@dg_global_options
@cli_telemetry_wrapper
def scaffold_project_command(
    path: Path,
    use_editable_dagster: Optional[str],
    python_environment: DgProjectPythonEnvironmentFlag,
    uv_sync: Optional[bool],
    **global_options: object,
) -> None:
    """Scaffold a new Dagster project at PATH. The name of the project will be the final component of PATH.

    This command can be run inside or outside of a workspace directory. If run inside a workspace,
    the project will be added to the workspace's list of project specs.

    "." may be passed as PATH to create the new project inside the existing working directory.

    Examples:
        create-dagster project PROJECT_NAME
            Scaffold a new project in new directory PROJECT_NAME. Automatically creates directory
            and parent directories.
        create-dagster project .
            Scaffold a new project in the CWD. The project name is taken from the last component of the CWD.

    Created projects will have the following structure:

    ├── src
    │   └── <project_name>
    │       ├── __init__.py
    │       ├── definitions.py
    │       ├── defs
    │       │   └── __init__.py
    │       └── components
    │           └── __init__.py
    ├── tests
    │   └── __init__.py
    └── pyproject.toml

    The `src.<project_name>.defs` directory holds Python objects that can be targeted by the
    `dg scaffold` command or have dg-inspectable metadata. Custom component types in the project
    live in `src.<project_name>.components`. These types can be created with `dg scaffold component`.
    """
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), cli_config)

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

    abs_path = path.resolve()
    if dg_context.is_in_workspace and dg_context.has_project(
        abs_path.relative_to(dg_context.workspace_root_path)
    ):
        exit_with_error(f"The current workspace already specifies a project at {abs_path}.")
    elif str(path) != "." and abs_path.exists():
        exit_with_error(f"A file or directory already exists at {abs_path}.")

    scaffold_project(
        abs_path,
        dg_context,
        use_editable_dagster=use_editable_dagster,
        python_environment=DgProjectPythonEnvironment.from_flag(python_environment),
    )

    venv_path = path / ".venv"
    if _should_run_uv_sync(python_environment, venv_path, uv_sync):
        click.echo("Running `uv sync --group dev`...")
        with pushd(path):
            subprocess.run(["uv", "sync", "--group", "dev"], check=True)

        click.echo("\nuv.lock and virtual environment created.")
        display_venv_path = get_shortest_path_repr(venv_path)
        click.echo(
            f"""
            Run `{get_venv_activation_cmd(display_venv_path)}` to activate your project's virtual environment.
            """.strip()
        )


# ########################
# ##### WORKSPACE
# ########################


@click.command(
    name="workspace",
    cls=DgClickCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.argument("path", type=Path)
@dg_editable_dagster_options
@dg_global_options
@cli_telemetry_wrapper
def scaffold_workspace_command(
    path: Path,
    use_editable_dagster: Optional[str],
    **global_options: object,
):
    """Initialize a new Dagster workspace.

    Examples:
        create-dagster workspace WORKSPACE_NAME
            Scaffold a new workspace in new directory WORKSPACE_NAME. Automatically creates directory
            and parent directories.
        create-dagster workspace .
            Scaffold a new workspace in the CWD. The workspace name is the last component of the CWD.

    The scaffolded workspace folder has the following structure:

    ├── <workspace_name>
    │   ├── projects
    |   |   └── <Dagster projects go here>
    │   └── dg.toml

    """
    workspace_config = DgRawWorkspaceConfig(
        scaffold_project_options=DgWorkspaceScaffoldProjectOptions.get_raw_from_cli(
            use_editable_dagster,
        )
    )

    abs_path = path.resolve()

    existing_workspace_path = discover_workspace_root(path)
    if existing_workspace_path:
        exit_with_error(
            f"Workspace already exists at {existing_workspace_path}.  Run `create-dagster project` to add a new project to that workspace."
        )
    elif str(path) != "." and path.exists():
        exit_with_error(f"Folder already exists at {path}.")

    click.echo(f"Creating a Dagster workspace at {path}.")

    scaffold_workspace(abs_path, workspace_config)
