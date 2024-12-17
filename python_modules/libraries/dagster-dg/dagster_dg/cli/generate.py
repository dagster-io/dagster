import os
import sys
from pathlib import Path
from typing import Optional, Tuple

import click

from dagster_dg.context import (
    CodeLocationDirectoryContext,
    DeploymentDirectoryContext,
    DgContext,
    is_inside_code_location_directory,
    is_inside_deployment_directory,
)
from dagster_dg.generate import (
    generate_code_location,
    generate_component_instance,
    generate_component_type,
    generate_deployment,
)


@click.group(name="generate")
def generate_cli() -> None:
    """Commands for generating Dagster components and related entities."""


@generate_cli.command(name="deployment")
@click.argument("path", type=Path)
def generate_deployment_command(path: Path) -> None:
    """Generate a Dagster deployment file structure.

    The deployment file structure includes a directory for code locations and configuration files
    for deploying to Dagster Plus.
    """
    dir_abspath = os.path.abspath(path)
    if os.path.exists(dir_abspath):
        click.echo(
            click.style(f"A file or directory at {dir_abspath} already exists. ", fg="red")
            + "\nPlease delete the contents of this path or choose another location."
        )
        sys.exit(1)
    generate_deployment(path)


@generate_cli.command(name="code-location")
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
@click.pass_context
def generate_code_location_command(
    cli_context: click.Context, name: str, use_editable_dagster: Optional[str]
) -> None:
    """Generate a Dagster code location file structure and a uv-managed virtual environment scoped
    to the code location.

    This command can be run inside or outside of a deployment directory. If run inside a deployment,
    the code location will be created within the deployment directory's code location directory.

    The code location file structure defines a Python package with some pre-existing internal
    structure:

    ├── <name>
    │   ├── __init__.py
    │   ├── components
    │   ├── definitions.py
    │   └── lib
    │       └── __init__.py
    ├── <name>_tests
    │   └── __init__.py
    └── pyproject.toml

    The `<name>.components` directory holds components (which can be created with `dg generate
    component`).  The `<name>.lib` directory holds custom component types scoped to the code
    location (which can be created with `dg generate component-type`).
    """
    dg_context = DgContext.from_cli_context(cli_context)
    if is_inside_deployment_directory(Path.cwd()):
        context = DeploymentDirectoryContext.from_path(Path.cwd(), dg_context)
        if context.has_code_location(name):
            click.echo(click.style(f"A code location named {name} already exists.", fg="red"))
            sys.exit(1)
        code_location_path = context.code_location_root_path / name
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

    generate_code_location(code_location_path, editable_dagster_root)


@generate_cli.command(name="component-type")
@click.argument("name", type=str)
@click.pass_context
def generate_component_type_command(cli_context: click.Context, name: str) -> None:
    """Generate a scaffold of a custom Dagster component type.

    This command must be run inside a Dagster code location directory. The component type scaffold
    will be generated in submodule `<code_location_name>.lib.<name>`.
    """
    dg_context = DgContext.from_cli_context(cli_context)
    if not is_inside_code_location_directory(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location directory.", fg="red"
            )
        )
        sys.exit(1)
    context = CodeLocationDirectoryContext.from_path(Path.cwd(), dg_context)
    full_component_name = f"{context.name}.{name}"
    if context.has_component_type(full_component_name):
        click.echo(click.style(f"A component type named `{name}` already exists.", fg="red"))
        sys.exit(1)

    generate_component_type(context, name)


@generate_cli.command(name="component")
@click.argument(
    "component_type",
    type=str,
)
@click.argument("component_name", type=str)
@click.option("--json-params", type=str, default=None, help="JSON string of component parameters.")
@click.argument("extra_args", nargs=-1, type=str)
@click.pass_context
def generate_component_command(
    cli_context: click.Context,
    component_type: str,
    component_name: str,
    json_params: Optional[str],
    extra_args: Tuple[str, ...],
) -> None:
    """Generate a scaffold of a Dagster component.

    This command must be run inside a Dagster code location directory. The component scaffold will be
    generated in submodule `<code_location_name>.components.<name>`.

    The COMPONENT_TYPE must be a registered component type in the code location environment.
    You can view all registered component types with `dg list component-types`. The COMPONENT_NAME
    will be used to name the submodule created under <code_location_name>.components.

    Components can optionally be passed generate parameters. There are two ways to do this:

    - Passing --json-params with a JSON string of parameters. For example:

        dg generate component foo.bar my_component --json-params '{"param1": "value", "param2": "value"}'`.

    - Passing key-value pairs as space-separated EXTRA_ARGS after `--`. For example:

        dg generate component foo.bar my_component -- param1=value param2=value

    When key-value pairs are used, the value type will be inferred from the
    underlying component generation schema.

    It is an error to pass both --json-params and EXTRA_ARGS.
    """
    dg_context = DgContext.from_cli_context(cli_context)
    if not is_inside_code_location_directory(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location directory.", fg="red"
            )
        )
        sys.exit(1)

    context = CodeLocationDirectoryContext.from_path(Path.cwd(), dg_context)
    if not context.has_component_type(component_type):
        click.echo(
            click.style(f"No component type `{component_type}` could be resolved.", fg="red")
        )
        sys.exit(1)
    elif context.has_component_instance(component_name):
        click.echo(
            click.style(f"A component instance named `{component_name}` already exists.", fg="red")
        )
        sys.exit(1)

    if json_params is not None and extra_args:
        click.echo(
            click.style(
                "Detected both --json-params and EXTRA_ARGS. These are mutually exclusive means of passing"
                " component generation parameters. Use only one.",
                fg="red",
            )
        )
        sys.exit(1)

    generate_component_instance(
        Path(context.component_instances_root_path),
        component_name,
        component_type,
        json_params,
        extra_args,
        dg_context,
    )
