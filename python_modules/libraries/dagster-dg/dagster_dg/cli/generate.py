import os
import sys
from pathlib import Path
from typing import Any, Mapping, Optional

import click
from click.core import ParameterSource

from dagster_dg.component import RemoteComponentType
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
from dagster_dg.utils import (
    DgClickCommand,
    DgClickGroup,
    json_schema_property_to_click_option,
    parse_json_option,
)


@click.group(name="generate", cls=DgClickGroup)
def generate_cli() -> None:
    """Commands for generating Dagster components and related entities."""


@generate_cli.command(name="deployment", cls=DgClickCommand)
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


@generate_cli.command(name="code-location", cls=DgClickCommand)
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
@click.pass_context
def generate_code_location_command(
    cli_context: click.Context, name: str, use_editable_dagster: Optional[str], skip_venv: bool
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

    generate_code_location(code_location_path, dg_context, editable_dagster_root, skip_venv)


@generate_cli.command(name="component-type", cls=DgClickCommand)
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


# The `dg generate component` command is special because its subcommands are dynamically generated
# from the registered component types in the code location. Because the registered component types
# depend on the built-in component library we are using, we cannot resolve them until we have the
# built-in component library, which can be set via a global option, e.g.:
#
#     dg --builtin-component-lib dagster_components.test ...
#
# To handle this, we define a custom click.Group subclass that loads the commands on demand.
class GenerateComponentGroup(DgClickGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commands_defined = False

    def get_command(self, cli_context: click.Context, cmd_name: str) -> Optional[click.Command]:
        if not self._commands_defined:
            self._define_commands(cli_context)
        return super().get_command(cli_context, cmd_name)

    def list_commands(self, cli_context):
        if not self._commands_defined:
            self._define_commands(cli_context)
        return super().list_commands(cli_context)

    def _define_commands(self, cli_context: click.Context) -> None:
        """Dynamically define a command for each registered component type."""
        app_context = DgContext.from_cli_context(cli_context)

        if not is_inside_code_location_directory(Path.cwd()):
            click.echo(
                click.style(
                    "This command must be run inside a Dagster code location directory.", fg="red"
                )
            )
            sys.exit(1)

        context = CodeLocationDirectoryContext.from_path(Path.cwd(), app_context)
        for key, component_type in context.iter_component_types():
            command = _create_generate_component_subcommand(key, component_type)
            self.add_command(command)


@generate_cli.group(name="component", cls=GenerateComponentGroup)
def generate_component_group() -> None:
    """Generate a scaffold of a Dagster component."""


def _create_generate_component_subcommand(
    component_key: str, component_type: RemoteComponentType
) -> DgClickCommand:
    @click.command(name=component_key, cls=DgClickCommand)
    @click.argument("component_name", type=str)
    @click.option(
        "--json-params",
        type=str,
        default=None,
        help="JSON string of component parameters.",
        callback=parse_json_option,
    )
    @click.pass_context
    def generate_component_command(
        cli_context: click.Context,
        component_name: str,
        json_params: Mapping[str, Any],
        **key_value_params: Any,
    ) -> None:
        f"""Generate a scaffold of a {component_type.name} component.

        This command must be run inside a Dagster code location directory. The component scaffold will be
        generated in submodule `<code_location_name>.components.<COMPONENT_NAME>`.

        Components can optionally be passed generate parameters. There are two ways to do this:

        (1) Passing a single --json-params option with a JSON string of parameters. For example:

            dg generate component foo.bar my_component --json-params '{{"param1": "value", "param2": "value"}}'`.

        (2) Passing each parameter as an option. For example:

            dg generate component foo.bar my_component --param1 value1 --param2 value2`

        It is an error to pass both --json-params and key-value pairs as options.
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
        if not context.has_component_type(component_key):
            click.echo(
                click.style(f"No component type `{component_key}` could be resolved.", fg="red")
            )
            sys.exit(1)
        elif context.has_component_instance(component_name):
            click.echo(
                click.style(
                    f"A component instance named `{component_name}` already exists.", fg="red"
                )
            )
            sys.exit(1)

        # Specified key-value params will be passed to this function with their default value of
        # `None` even if the user did not set them. Filter down to just the ones that were set by
        # the user.
        user_provided_key_value_params = {
            k: v
            for k, v in key_value_params.items()
            if cli_context.get_parameter_source(k) == ParameterSource.COMMANDLINE
        }
        if json_params is not None and user_provided_key_value_params:
            click.echo(
                click.style(
                    "Detected params passed as both --json-params and individual options. These are mutually exclusive means of passing"
                    " component generation parameters. Use only one.",
                    fg="red",
                )
            )
            sys.exit(1)
        elif json_params:
            generate_params = json_params
        elif user_provided_key_value_params:
            generate_params = user_provided_key_value_params
        else:
            generate_params = None

        generate_component_instance(
            Path(context.component_instances_root_path),
            component_name,
            component_key,
            generate_params,
            dg_context,
        )

    # If there are defined generate params, add them to the command
    schema = component_type.generate_params_schema
    if schema:
        for key, field_info in schema["properties"].items():
            # All fields are currently optional because they can also be passed under
            # `--json-params`
            option = json_schema_property_to_click_option(key, field_info, required=False)
            generate_component_command.params.append(option)

    return generate_component_command
