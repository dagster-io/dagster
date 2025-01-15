import os
import sys
from pathlib import Path
from typing import Optional

import click

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.scaffold import scaffold_code_location
from dagster_dg.utils import DgClickCommand, DgClickGroup


@click.group(name="code-location", cls=DgClickGroup)
def code_location_group():
    """Commands for operating code location directories."""


# ########################
# ##### SCAFFOLD
# ########################


@code_location_group.command(name="scaffold", cls=DgClickCommand)
@click.argument("name", type=str)
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
@click.option(
    "--skip-venv",
    is_flag=True,
    default=False,
    help="Do not create a virtual environment for the code location.",
)
@dg_global_options
@click.pass_context
def code_location_scaffold_command(
    context: click.Context,
    name: str,
    use_editable_dagster: Optional[str],
    skip_venv: bool,
    **global_options: object,
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
            click.echo(click.style(f"A code location named {name} already exists.", fg="red"))
            sys.exit(1)
        code_location_path = dg_context.code_location_root_path / name
    else:
        code_location_path = Path.cwd() / name

    if use_editable_dagster == "TRUE":
        if not os.environ.get("DAGSTER_GIT_REPO_DIR"):
            click.echo(
                click.style(
                    "The `--use-editable-dagster` flag requires the `DAGSTER_GIT_REPO_DIR` environment variable to be set.",
                    fg="red",
                )
            )
            sys.exit(1)
        editable_dagster_root = os.environ["DAGSTER_GIT_REPO_DIR"]
    elif use_editable_dagster:  # a string value was passed
        editable_dagster_root = use_editable_dagster
    else:
        editable_dagster_root = None

    scaffold_code_location(
        code_location_path, dg_context, editable_dagster_root, skip_venv=skip_venv
    )


# ########################
# ##### LIST
# ########################


@code_location_group.command(name="list", cls=DgClickCommand)
@dg_global_options
@click.pass_context
def code_location_list_command(context: click.Context, **global_options: object) -> None:
    """List code locations in the current deployment."""
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)
    if not dg_context.is_deployment:
        click.echo(
            click.style("This command must be run inside a Dagster deployment directory.", fg="red")
        )
        sys.exit(1)

    for code_location in dg_context.get_code_location_names():
        click.echo(code_location)
