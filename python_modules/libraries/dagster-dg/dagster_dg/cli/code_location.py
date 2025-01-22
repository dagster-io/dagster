import os
from pathlib import Path
from typing import Annotated

import click
import typer
from typer_di import Depends, TyperDI

from dagster_dg.cli.global_options import typer_dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.scaffold import scaffold_code_location
from dagster_dg.utils import exit_with_error

code_location_group = TyperDI(
    name="code-location", help="Commands for operating on code location directories."
)


# ########################
# ##### SCAFFOLD
# ########################


@code_location_group.command(name="scaffold")
def code_location_scaffold_command(
    context: click.Context,
    name: str,
    use_editable_dagster: Annotated[
        bool,
        typer.Option(
            help=(
                "Install Dagster package dependencies from a local Dagster clone. Accepts a path to local Dagster clone root or"
                " may be set as a flag (no value is passed). If set as a flag,"
                " the location of the local Dagster clone will be read from the `DAGSTER_GIT_REPO_DIR` environment variable."
            ),
        ),
    ] = False,
    skip_venv: Annotated[
        bool,
        typer.Option(
            help="Do not create a virtual environment for the code location.",
        ),
    ] = False,
    global_options: dict[str, object] = Depends(typer_dg_global_options),
) -> None:
    """Scaffold a Dagster code location file structure and a uv-managed virtual environment scoped
    to the code location.

    This command can be run inside or outside of a deployment directory. If run inside a deployment,
    the code location will be created within the deployment directory's code location directory.

    The code location file structure defines a Python package with some pre-existing internal
    structure:

    \b
    ├── <name>
    │   ├── __init__.py
    │   ├── components
    │   ├── definitions.py
    │   └── lib
    │       └── __init__.py
    ├── <name>_tests
    │   └── __init__.py
    └── pyproject.toml

    The `<name>.components` directory holds components (which can be created with `dg scaffold
    component`).  The `<name>.lib` directory holds custom component types scoped to the code
    location (which can be created with `dg component-type scaffold`).
    """  # noqa: D301
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)
    if dg_context.is_deployment:
        if dg_context.has_code_location(name):
            exit_with_error(f"A code location named {name} already exists.")
        code_location_path = dg_context.code_location_root_path / name
    else:
        code_location_path = Path.cwd() / name

    if use_editable_dagster:
        if not os.environ.get("DAGSTER_GIT_REPO_DIR"):
            exit_with_error(
                "The `--use-editable-dagster` flag requires the `DAGSTER_GIT_REPO_DIR` environment variable to be set."
            )
        editable_dagster_root = os.environ["DAGSTER_GIT_REPO_DIR"]
    else:
        editable_dagster_root = None

    scaffold_code_location(
        code_location_path, dg_context, editable_dagster_root, skip_venv=skip_venv
    )


# ########################
# ##### LIST
# ########################


@code_location_group.command(name="list")
def code_location_list_command(
    context: typer.Context,
    global_options: dict[str, object] = Depends(typer_dg_global_options),
) -> None:
    """List code locations in the current deployment."""
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)
    if not dg_context.is_deployment:
        exit_with_error("This command must be run inside a Dagster deployment directory.")

    for code_location in dg_context.get_code_location_names():
        click.echo(code_location)
