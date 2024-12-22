import sys
from pathlib import Path
from typing import Any, List, Mapping, Optional

import click
from click.core import ParameterSource

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.component import RemoteComponentType
from dagster_dg.config import (
    DgConfig,
    get_config_from_cli_context,
    has_config_on_cli_context,
    set_config_on_cli_context,
)
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
    not_none,
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

    def list_commands(self, cli_context: click.Context) -> List[str]:
        if not self._commands_defined:
            self._define_commands(cli_context)
        return super().list_commands(cli_context)

    def _define_commands(self, cli_context: click.Context) -> None:
        """Dynamically define a command for each registered component type."""
        if not has_config_on_cli_context(cli_context):
            cli_context.invoke(not_none(self.callback), **cli_context.params)
        config = get_config_from_cli_context(cli_context)
        dg_context = DgContext.from_config(config)

        if not is_inside_code_location_directory(Path.cwd()):
            click.echo(
                click.style(
                    "This command must be run inside a Dagster code location directory.", fg="red"
                )
            )
            sys.exit(1)

        context = CodeLocationDirectoryContext.from_path(Path.cwd(), dg_context)
        for key, component_type in context.iter_component_types():
            command = _create_component_generate_subcommand(key, component_type)
            self.add_command(command)


class ComponentGenerateSubCommand(DgClickCommand):
    def format_usage(self, context: click.Context, formatter: click.HelpFormatter) -> None:
        if not isinstance(self, click.Command):
            raise ValueError("This mixin is only intended for use with click.Command instances.")
        arg_pieces = self.collect_usage_pieces(context)
        command_parts = context.command_path.split(" ")
        command_parts.insert(-1, "[GLOBAL OPTIONS]")
        return formatter.write_usage(" ".join(command_parts), " ".join(arg_pieces))

    def format_options(self, context: click.Context, formatter: click.HelpFormatter) -> None:
        # This will not produce any global options since there are none defined on component
        # generate subcommands.
        super().format_options(context, formatter)

        # Get the global options off the parent group.
        parent_context = not_none(context.parent)
        parent_command = not_none(context.parent).command
        if not isinstance(parent_command, DgClickGroup):
            raise ValueError("Parent command must be a DgClickGroup.")
        _, global_opts = parent_command.get_partitioned_opts(context)

        with formatter.section("Global options"):
            records = [not_none(p.get_help_record(parent_context)) for p in global_opts]
            formatter.write_dl(records)


# We have to override the usual Click processing of `--help` here. The issue is
# that click will process this option before processing anything else, but because we are
# dynamically generating subcommands based on the content of other options, the output of --help
# actually depends on these other options. So we opt out of Click's short-circuiting
# behavior of `--help` by setting `help_option_names=[]`, ensuring that we can process the other
# options first and generate the correct subcommands. We then add a custom `--help` option that
# gets invoked inside the callback.
@component_group.group(
    name="generate",
    cls=ComponentGenerateGroup,
    invoke_without_command=True,
    context_settings={"help_option_names": []},
)
@click.option("-h", "--help", "help_", is_flag=True, help="Show this message and exit.")
@dg_global_options
@click.pass_context
def component_generate_group(context: click.Context, help_: bool, **global_options: object) -> None:
    """Generate a scaffold of a Dagster component."""
    # Click attempts to resolve subcommands BEFORE it invokes this callback.
    # Therefore we need to manually invoke this callback during subcommand generation to make sure
    # it runs first. It will be invoked again later by Click. We make it idempotent to deal with
    # that.
    if not has_config_on_cli_context(context):
        set_config_on_cli_context(context, DgConfig.from_cli_global_options(global_options))
    if help_:
        click.echo(context.get_help())
        context.exit(0)


def _create_component_generate_subcommand(
    component_key: str, component_type: RemoteComponentType
) -> DgClickCommand:
    # We need to "reset" the help option names to the default ones because we inherit the parent
    # value of context settings from the parent group, which has been customized.
    @click.command(
        name=component_key,
        cls=ComponentGenerateSubCommand,
        context_settings={"help_option_names": ["-h", "--help"]},
    )
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
        config = get_config_from_cli_context(cli_context)
        dg_context = DgContext.from_config(config)
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
@dg_global_options
def component_list_command(**global_options: object) -> None:
    """List Dagster component instances defined in the current code location."""
    dg_context = DgContext.from_cli_global_options(global_options)
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
