import subprocess
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import discover_workspace_root, normalize_cli_config
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

from create_dagster.scaffold import scaffold_project, scaffold_workspace
from create_dagster.version_check import check_create_dagster_up_to_date


def _project_package_install_warning_message() -> str:
    pip_install_cmd = "pip install --editable ."
    uv_install_cmd = "uv sync"
    return format_multiline_str(
        f"""
            The environment used for your project must include an installation of your project
            package. Please run `{uv_install_cmd}` (for uv) or `{pip_install_cmd}` (for pip) before
            running `dg` commands against your project.
        """
    )


def _print_package_install_warning_message(install_msg_warning) -> None:
    click.secho(
        install_msg_warning,
        fg="yellow",
    )


def _workspace_environment_install_warning_message() -> str:
    pip_install_cmd = "pip install --editable ./deployments/local"
    uv_install_cmd = "uv sync --directory ./deployments/local"
    return format_multiline_str(
        f"""
        The Python environment used for your workspace must include an installation of the `dg`
        CLI. Please run `{uv_install_cmd}` (for uv) or `{pip_install_cmd}` (for pip) before
        running `dg` commands locally against your workspace.
        """
    )


def _get_project_uv_sync_prompt_msg() -> str:
    return format_multiline_str("""
    A `uv` installation was detected. Run `uv sync`? This will create a uv.lock file and
    the virtual environment you need to activate in order to work on this project.
    If you wish to use a non-uv package manager, choose "n". (y/n)
    """)


def _get_workspace_environment_uv_sync_prompt_msg(local_environment_path: Path) -> str:
    return format_multiline_str(f"""
    A `uv` installation was detected. Run `uv sync --directory {local_environment_path}`?
    This will create a uv.lock file and the virtual environment you need to activate in order to
    use `dg` locally with this workspace. If you wish to use a non-uv package manager,
    choose "n". (y/n)
    """)


def _should_run_uv_sync(
    venv_path: Path,
    uv_sync_flag: Optional[bool],
    uv_sync_prompt_msg: str,
    install_warning_msg: str,
) -> bool:
    if uv_sync_flag is not None:
        return uv_sync_flag
    elif venv_path.exists():
        _print_package_install_warning_message(install_warning_msg)
        return False
    elif is_uv_installed():  # uv_sync_flag is unset (None)
        response = click.prompt(
            uv_sync_prompt_msg,
            default="y",
        ).lower()
        if response not in ("y", "n"):
            exit_with_error(f"Invalid response '{response}'. Please enter 'y' or 'n'.")
        if response == "n":
            _print_package_install_warning_message(install_warning_msg)
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
    use_editable_dagster: bool,
    uv_sync: Optional[bool],
    **global_options: object,
) -> None:
    """Scaffold a new Dagster project at PATH. The name of the project will be the final component of PATH.

    This command can be run inside or outside of a workspace directory. If run inside a workspace,
    the project will be added to the workspace's list of project specs.

    "." may be passed as PATH to create the new project inside the existing working directory.

    Created projects will have the following structure::

        ├── src
        │   └── PROJECT_NAME
        │       ├── __init__.py
        │       ├── definitions.py
        │       ├── defs
        │       │   └── __init__.py
        │       └── components
        │           └── __init__.py
        ├── tests
        │   └── __init__.py
        └── pyproject.toml

    The `src.PROJECT_NAME.defs` directory holds Python objects that can be targeted by the
    `dg scaffold` command or have dg-inspectable metadata. Custom component types in the project
    live in `src.PROJECT_NAME.components`. These types can be created with `dg scaffold component`.

    Examples::

        create-dagster project PROJECT_NAME
            Scaffold a new project in new directory PROJECT_NAME. Automatically creates directory
            and parent directories.
        create-dagster project .
            Scaffold a new project in the CWD. The project name is taken from the last component of the CWD.
    """
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), cli_config)
    check_create_dagster_up_to_date(dg_context)

    if uv_sync is True and not is_uv_installed():
        exit_with_error("""
            uv is not installed. Please install uv to use the `--uv-sync` option.
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
    )

    venv_path = path / ".venv"

    if _should_run_uv_sync(
        venv_path,
        uv_sync,
        uv_sync_prompt_msg=_get_project_uv_sync_prompt_msg(),
        install_warning_msg=_project_package_install_warning_message(),
    ):
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
def scaffold_workspace_command(
    path: Path,
    use_editable_dagster: bool,
    uv_sync: Optional[bool],
    **global_options: object,
):
    """Initialize a new Dagster workspace.

    The scaffolded workspace folder has the following structure::

        ├── projects
        │   └── Dagster projects go here
        ├── deployments
        │   └── local
        │       ├── pyproject.toml
        │       └── uv.lock
        └── dg.toml

    Examples::

        create-dagster workspace WORKSPACE_NAME
            Scaffold a new workspace in new directory WORKSPACE_NAME. Automatically creates directory
            and parent directories.
        create-dagster workspace .
            Scaffold a new workspace in the CWD. The workspace name is the last component of the CWD.

    """
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), cli_config)
    check_create_dagster_up_to_date(dg_context)

    abs_path = path.resolve()

    existing_workspace_path = discover_workspace_root(path)
    if existing_workspace_path:
        exit_with_error(
            f"Workspace already exists at {existing_workspace_path}.  Run `create-dagster project` to add a new project to that workspace."
        )
    elif str(path) != "." and path.exists():
        exit_with_error(f"Folder already exists at {path}.")

    scaffold_workspace(
        abs_path,
        use_editable_dagster=use_editable_dagster,
    )

    local_environment_path = abs_path / "deployments" / "local"
    local_venv_path = local_environment_path / ".venv"

    click.echo(
        f"Scaffolded files for Dagster workspace at {abs_path}.\nA local environment to run `dg` commands against this workspace was created at {local_environment_path}."
    )

    shortest_local_environment_path = get_shortest_path_repr(local_environment_path)

    if _should_run_uv_sync(
        local_venv_path,
        uv_sync,
        uv_sync_prompt_msg=_get_workspace_environment_uv_sync_prompt_msg(
            shortest_local_environment_path
        ),
        install_warning_msg=_workspace_environment_install_warning_message(),
    ):
        click.echo(f"Running `uv sync --directory {shortest_local_environment_path}`...")
        with pushd(path):
            subprocess.run(
                ["uv", "sync"],
                check=True,
                cwd=local_environment_path,
            )

        click.echo("\nuv.lock and virtual environment created.")
        display_venv_path = get_shortest_path_repr(local_venv_path)
        click.echo(
            f"""
            Run `{get_venv_activation_cmd(display_venv_path)}` to activate your workspace's local virtual environment.
            """.strip()
        )
