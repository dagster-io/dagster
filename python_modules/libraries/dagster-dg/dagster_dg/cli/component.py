import sys
from pathlib import Path
from typing import Any, Mapping, Optional

import click
from click.core import ParameterSource

from dagster_dg.component import RemoteComponentType
from dagster_dg.context import (
    CodeLocationDirectoryContext,
    DgContext,
    is_inside_code_location_directory,
)
from dagster_dg.generate import generate_component_instance
from dagster_dg.utils import (
    DgClickCommand,
    DgClickGroup,
    json_schema_property_to_click_option,
    parse_json_option,
)


@click.group(name="component", cls=DgClickGroup)
def component_group():
    """Commands for operating on components."""


# ########################
# ##### GENERATE
# ########################


# The `dg component generate` command is special because its subcommands are dynamically generated
# from the registered component types in the code location. Because the registered component types
# depend on the built-in component library we are using, we cannot resolve them until we have the
# built-in component library, which can be set via a global option, e.g.:
#
#     dg --builtin-component-lib dagster_components.test ...
#
# To handle this, we define a custom click.Group subclass that loads the commands on demand.
class ComponentGenerateGroup(DgClickGroup):
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
            command = _create_component_generate_subcommand(key, component_type)
            self.add_command(command)


@component_group.group(name="generate", cls=ComponentGenerateGroup)
def component_generate_group() -> None:
    """Generate a scaffold of a Dagster component."""


def _create_component_generate_subcommand(
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

            dg component generate foo.bar my_component --json-params '{{"param1": "value", "param2": "value"}}'`.

        (2) Passing each parameter as an option. For example:

            dg component generate foo.bar my_component --param1 value1 --param2 value2`

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


# ########################
# ##### LIST
# ########################


@component_group.command(name="list", cls=DgClickCommand)
@click.pass_context
def component_list_command(cli_context: click.Context) -> None:
    """List Dagster component instances defined in the current code location."""
    dg_context = DgContext.from_cli_context(cli_context)
    if not is_inside_code_location_directory(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location directory.", fg="red"
            )
        )
        sys.exit(1)

    context = CodeLocationDirectoryContext.from_path(Path.cwd(), dg_context)
    for component_name in context.get_component_instance_names():
        click.echo(component_name)
