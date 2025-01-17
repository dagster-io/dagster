import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Optional

import click
from click.core import ParameterSource

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.component import RemoteComponentRegistry, RemoteComponentType
from dagster_dg.config import (
    get_config_from_cli_context,
    has_config_on_cli_context,
    normalize_cli_config,
    set_config_on_cli_context,
)
from dagster_dg.context import DgContext
from dagster_dg.scaffold import scaffold_component_instance
from dagster_dg.utils import (
    DgClickCommand,
    DgClickGroup,
    exit_with_error,
    json_schema_property_to_click_option,
    not_none,
    parse_json_option,
)


@click.group(name="component", cls=DgClickGroup)
def component_group():
    """Commands for operating on components."""


# ########################
# ##### SCAFFOLD
# ########################


# The `dg component scaffold` command is special because its subcommands are dynamically generated
# from the registered component types in the code location. Because the registered component types
# depend on the built-in component library we are using, we cannot resolve them until we have the
# built-in component library, which can be set via a global option, e.g.:
#
#     dg --builtin-component-lib dagster_components.test ...
#
# To handle this, we define a custom click.Group subclass that loads the commands on demand.
class ComponentScaffoldGroup(DgClickGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commands_defined = False

    def get_command(self, cli_context: click.Context, cmd_name: str) -> Optional[click.Command]:
        if not self._commands_defined:
            self._define_commands(cli_context)
        return super().get_command(cli_context, cmd_name)

    def list_commands(self, cli_context: click.Context) -> list[str]:
        if not self._commands_defined:
            self._define_commands(cli_context)
        return super().list_commands(cli_context)

    def _define_commands(self, cli_context: click.Context) -> None:
        """Dynamically define a command for each registered component type."""
        if not has_config_on_cli_context(cli_context):
            cli_context.invoke(not_none(self.callback), **cli_context.params)
        config = get_config_from_cli_context(cli_context)
        dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), config)

        if not dg_context.is_code_location:
            exit_with_error("This command must be run inside a Dagster code location directory.")

        registry = RemoteComponentRegistry.from_dg_context(dg_context)
        for key, component_type in registry.items():
            command = _create_component_scaffold_subcommand(key, component_type)
            self.add_command(command)


class ComponentScaffoldSubCommand(DgClickCommand):
    def format_usage(self, context: click.Context, formatter: click.HelpFormatter) -> None:
        if not isinstance(self, click.Command):
            raise ValueError("This mixin is only intended for use with click.Command instances.")
        arg_pieces = self.collect_usage_pieces(context)
        command_parts = context.command_path.split(" ")
        command_parts.insert(-1, "[GLOBAL OPTIONS]")
        return formatter.write_usage(" ".join(command_parts), " ".join(arg_pieces))

    def format_options(self, context: click.Context, formatter: click.HelpFormatter) -> None:
        # This will not produce any global options since there are none defined on component
        # scaffold subcommands.
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
    name="scaffold",
    cls=ComponentScaffoldGroup,
    invoke_without_command=True,
    context_settings={"help_option_names": []},
)
@click.option("-h", "--help", "help_", is_flag=True, help="Show this message and exit.")
@dg_global_options
@click.pass_context
def component_scaffold_group(context: click.Context, help_: bool, **global_options: object) -> None:
    """Scaffold of a Dagster component."""
    # Click attempts to resolve subcommands BEFORE it invokes this callback.
    # Therefore we need to manually invoke this callback during subcommand generation to make sure
    # it runs first. It will be invoked again later by Click. We make it idempotent to deal with
    # that.
    if not has_config_on_cli_context(context):
        cli_config = normalize_cli_config(global_options, context)
        set_config_on_cli_context(context, cli_config)
    if help_:
        click.echo(context.get_help())
        context.exit(0)


def _create_component_scaffold_subcommand(
    component_key: str, component_type: RemoteComponentType
) -> DgClickCommand:
    # We need to "reset" the help option names to the default ones because we inherit the parent
    # value of context settings from the parent group, which has been customized.
    @click.command(
        name=component_key,
        cls=ComponentScaffoldSubCommand,
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
    def scaffold_component_command(
        cli_context: click.Context,
        component_name: str,
        json_params: Mapping[str, Any],
        **key_value_params: Any,
    ) -> None:
        f"""Scaffold of a {component_type.name} component.

        This command must be run inside a Dagster code location directory. The component scaffold will be
        placed in submodule `<code_location_name>.components.<COMPONENT_NAME>`.

        Components can optionally be passed scaffold parameters. There are two ways to do this:

        (1) Passing a single --json-params option with a JSON string of parameters. For example:

            dg component scaffold foo.bar my_component --json-params '{{"param1": "value", "param2": "value"}}'`.

        (2) Passing each parameter as an option. For example:

            dg component scaffold foo.bar my_component --param1 value1 --param2 value2`

        It is an error to pass both --json-params and key-value pairs as options.
        """
        cli_config = get_config_from_cli_context(cli_context)
        dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)
        if not dg_context.is_code_location:
            exit_with_error("This command must be run inside a Dagster code location directory.")

        registry = RemoteComponentRegistry.from_dg_context(dg_context)
        if not registry.has(component_key):
            exit_with_error(f"No component type `{component_key}` could be resolved.")
        elif dg_context.has_component(component_name):
            exit_with_error(f"A component instance named `{component_name}` already exists.")

        # Specified key-value params will be passed to this function with their default value of
        # `None` even if the user did not set them. Filter down to just the ones that were set by
        # the user.
        user_provided_key_value_params = {
            k: v
            for k, v in key_value_params.items()
            if cli_context.get_parameter_source(k) == ParameterSource.COMMANDLINE
        }
        if json_params is not None and user_provided_key_value_params:
            exit_with_error(
                "Detected params passed as both --json-params and individual options. These are mutually exclusive means of passing"
                " component generation parameters. Use only one.",
            )
        elif json_params:
            scaffold_params = json_params
        elif user_provided_key_value_params:
            scaffold_params = user_provided_key_value_params
        else:
            scaffold_params = None

        scaffold_component_instance(
            Path(dg_context.components_path),
            component_name,
            component_key,
            scaffold_params,
            dg_context,
        )

    # If there are defined scaffold params, add them to the command
    schema = component_type.scaffold_params_schema
    if schema:
        for key, field_info in schema["properties"].items():
            # All fields are currently optional because they can also be passed under
            # `--json-params`
            option = json_schema_property_to_click_option(key, field_info, required=False)
            scaffold_component_command.params.append(option)

    return scaffold_component_command


# ########################
# ##### LIST
# ########################


@component_group.command(name="list", cls=DgClickCommand)
@dg_global_options
@click.pass_context
def component_list_command(context: click.Context, **global_options: object) -> None:
    """List Dagster component instances defined in the current code location."""
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)
    if not dg_context.is_code_location:
        exit_with_error("This command must be run inside a Dagster code location directory.")

    for component_name in dg_context.get_component_names():
        click.echo(component_name)


# ########################
# ##### CHECK
# ########################


@component_group.command(name="check", cls=DgClickCommand)
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@dg_global_options
@click.pass_context
def component_check_command(
    context: click.Context,
    paths: Sequence[str],
    **global_options: object,
) -> None:
    """Check component files against their schemas, showing validation errors."""
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)

    try:
        dg_context.external_components_command(["check", "component", *paths])
    except CalledProcessError:
        sys.exit(1)
