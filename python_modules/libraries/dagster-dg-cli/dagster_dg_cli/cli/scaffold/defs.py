from collections.abc import Mapping
from copy import copy
from pathlib import Path
from typing import Any, Optional, cast

import click
from click.core import ParameterSource
from dagster_dg_core.component import EnvRegistry
from dagster_dg_core.config import (
    get_config_from_cli_context,
    has_config_on_cli_context,
    normalize_cli_config,
    set_config_on_cli_context,
)
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import GLOBAL_OPTIONS, dg_global_options
from dagster_dg_core.utils import (
    DgClickCommand,
    DgClickGroup,
    exit_with_error,
    generate_missing_registry_object_error_message,
    json_schema_property_to_click_option,
    not_none,
    parse_json_option,
)
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared import check
from dagster_shared.error import DagsterUnresolvableSymbolError
from dagster_shared.serdes.objects import EnvRegistryKey, EnvRegistryObjectSnap
from dagster_shared.seven import load_module_object

from dagster_dg_cli.scaffold import (
    ScaffoldFormatOptions,
    scaffold_inline_component,
    scaffold_registry_object,
)

# These commands are not dynamically generated, but perhaps should be.
HARDCODED_COMMANDS = {"component"}


# The `dg scaffold defs` command is special because its subcommands are dynamically generated
# from the available components in the environment. Because the component types
# depend on the component modules we are using, we cannot resolve them until we have know these
# component modules, which can be set via the `--use-component-module` option, e.g.
#
#     dg --use-component-module dagster_components.test ...
#
# To handle this, we define a custom click.Group subclass that loads the commands on demand.
class ScaffoldDefsGroup(DgClickGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commands_defined = False

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        if not self._commands_defined and cmd_name not in HARDCODED_COMMANDS:
            self._define_commands(ctx)

        # First try exact match
        cmd = super().get_command(ctx, cmd_name)
        return cmd or self._get_matching_command(ctx, cmd_name)

    def list_commands(self, ctx: click.Context) -> list[str]:
        if not self._commands_defined:
            self._define_commands(ctx)
        return super().list_commands(ctx)

    def _define_commands(self, cli_context: click.Context) -> None:
        """Dynamically define a command for each registered component type."""
        if not has_config_on_cli_context(cli_context):
            cli_context.invoke(not_none(self.callback), **cli_context.params)
        config = get_config_from_cli_context(cli_context)
        dg_context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), config)

        registry = EnvRegistry.from_dg_context(dg_context)

        # Keys where the actual class name is not shared with any other key will use the class name
        # as a command alias.
        keys_by_name: dict[str, set[EnvRegistryKey]] = {}
        for key in registry.keys():
            keys_by_name.setdefault(key.name, set()).add(key)

        for key, component_type in registry.items():
            self._create_subcommand(
                key, component_type, use_typename_alias=len(keys_by_name[key.name]) == 1
            )

        self._commands_defined = True

    def _create_subcommand(
        self,
        key: EnvRegistryKey,
        obj: EnvRegistryObjectSnap,
        use_typename_alias: bool,
    ) -> None:
        # We need to "reset" the help option names to the default ones because we inherit the parent
        # value of context settings from the parent group, which has been customized.
        aliases = [
            *[alias.to_typename() for alias in obj.aliases],
            *([key.name] if use_typename_alias else []),
        ]

        @self.command(
            cls=ScaffoldDefsSubCommand,
            name=key.to_typename(),
            context_settings={"help_option_names": ["-h", "--help"]},
            aliases=aliases,
            help=obj.description or obj.summary,
        )
        @click.argument("defs_path", type=str)
        @click.pass_context
        @cli_telemetry_wrapper
        def scaffold_command(
            cli_context: click.Context,
            defs_path: str,
            **other_opts: Any,
        ) -> None:
            f"""Scaffold a {key.name} object.

            This command must be run inside a Dagster project directory. The component scaffold will be
            placed in submodule `<project_name>.defs.<INSTANCE_NAME>`.

            Objects can optionally be passed scaffold parameters. There are two ways to do this:

            (1) Passing a single --json-params option with a JSON string of parameters. For example:

                dg scaffold foo.bar my_object --json-params '{{"param1": "value", "param2": "value"}}'`.

            (2) Passing each parameter as an option. For example:

                dg scaffold foo.bar my_object --param1 value1 --param2 value2`

            It is an error to pass both --json-params and key-value pairs as options.
            """
            cli_config = get_config_from_cli_context(cli_context)
            dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

            # json_params will not be present in the key_value_params if no scaffold properties
            # are defined.
            json_scaffolder_params = other_opts.pop("json_params", None)

            # format option is only present if we are dealing with a component. Otherewise we
            # default to python for decorator scaffolding. Default is YAML (set by option) for
            # components.
            scaffolder_format = cast("ScaffoldFormatOptions", other_opts.pop("format", "python"))

            # Remanining options are scaffolder params
            key_value_scaffolder_params = other_opts

            check.invariant(
                scaffolder_format in ["yaml", "python"],
                "format must be either 'yaml' or 'python'",
            )
            _core_scaffold(
                dg_context,
                cli_context,
                key,
                defs_path,
                key_value_scaffolder_params,
                scaffolder_format,
                json_scaffolder_params,
            )

        if obj.is_component:
            scaffold_command.params.append(
                click.Option(
                    ["--format"],
                    type=click.Choice(["yaml", "python"], case_sensitive=False),
                    default="yaml",
                    help="Format of the component configuration (yaml or python)",
                )
            )

        # If there are defined scaffold properties, add them to the command. Also only add
        # `--json-params` if there are defined scaffold properties.
        if obj.scaffolder_schema and obj.scaffolder_schema.get("properties"):
            scaffold_command.params.append(
                click.Option(
                    ["--json-params"],
                    type=str,
                    default=None,
                    help="JSON string of scaffolder parameters. Mutually exclusive with passing individual parameters as options.",
                    callback=parse_json_option,
                )
            )
            for name, field_info in obj.scaffolder_schema["properties"].items():
                # All fields are currently optional because they can also be passed under
                # `--json-params`
                option = json_schema_property_to_click_option(name, field_info, required=False)
                scaffold_command.params.append(option)

    def _get_matching_command(self, ctx: click.Context, input_cmd: str) -> click.Command:
        commands = self.list_commands(ctx)
        cmd_query = input_cmd.lower()
        matches = sorted([name for name in commands if cmd_query in name.lower()])

        # if input is not a substring match for any registered command, try to interpret it as a
        # Python reference, load the corresponding registry object, and generate a command on the
        # fly
        if len(matches) == 0:
            snap = self._try_load_input_as_registry_object(input_cmd)
            if snap:
                self._create_subcommand(snap.key, snap, use_typename_alias=False)
                return check.not_none(super().get_command(ctx, snap.key.to_typename()))
            else:
                exit_with_error(generate_missing_registry_object_error_message(input_cmd))

        if len(matches) == 1:
            click.echo(f"No exact match found for '{input_cmd}'. Did you mean this one?")
            click.echo(f"    {matches[0]}")
            selection = click.prompt("Choose (y/n)", type=str, default="y")
            if selection == "y":
                index = 1
            elif selection == "n":
                click.echo("Exiting.")
                ctx.exit(0)
            else:
                exit_with_error(f"Invalid selection: {selection}. Please choose 'y' or 'n'.")
        else:
            # Present a menu of options for the user to choose from
            click.echo(f"No exact match found for '{input_cmd}'. Did you mean one of these?")
            for i, match in enumerate(matches, 1):
                click.echo(f"({i}) {match}")
            click.echo("(n) quit")

            # Get user selection
            selection = click.prompt("Select an option (number)", type=str, default="1")
            if selection == "n":
                click.echo("Exiting.")
                ctx.exit(0)

            invalid_selection_msg = f"Invalid selection: {selection}. Please choose a number between 1 and {len(matches)}."
            if not selection.isdigit():
                exit_with_error(invalid_selection_msg)
            index = int(selection)
            if index < 1 or index > len(matches):
                exit_with_error(invalid_selection_msg)

        selected_cmd = matches[index - 1]
        click.echo(f"Using defs scaffolder: {selected_cmd}")
        return check.not_none(super().get_command(ctx, selected_cmd))

    def _try_load_input_as_registry_object(self, input_str: str) -> Optional[EnvRegistryObjectSnap]:
        from dagster.components.core.snapshot import get_package_entry_snap

        if not EnvRegistryKey.is_valid_typename(input_str):
            return None
        key = EnvRegistryKey.from_typename(input_str)
        try:
            obj = load_module_object(key.namespace, key.name)
            return get_package_entry_snap(key, obj)
        except DagsterUnresolvableSymbolError:
            return None


class ScaffoldDefsSubCommand(DgClickCommand):
    # We have to override this because the implementation of `format_help` used elsewhere will only
    # pull parameters directly off the target command. For these component scaffold subcommands  we need
    # to expose the global options, which are defined on the preceding group rather than the command
    # itself.
    def format_help(self, context: click.Context, formatter: click.HelpFormatter):
        """Customizes the help to include hierarchical usage."""
        from typer.rich_utils import rich_format_help

        if not isinstance(self, click.Command):
            raise ValueError("This mixin is only intended for use with click.Command instances.")

        # This is a hack. We pass the help format func a modified version of the command where the global
        # options are attached to the command itself. This will cause them to be included in the
        # help output.
        cmd_copy = copy(self)
        cmd_copy.params = [
            *cmd_copy.params,
            *(GLOBAL_OPTIONS.values()),
        ]
        rich_format_help(obj=cmd_copy, ctx=context, markup_mode="rich")

    def format_usage(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        if not isinstance(self, click.Command):
            raise ValueError("This mixin is only intended for use with click.Command instances.")
        arg_pieces = self.collect_usage_pieces(ctx)
        command_parts = ctx.command_path.split(" ")
        command_parts.insert(-1, "[GLOBAL OPTIONS]")
        return formatter.write_usage(" ".join(command_parts), " ".join(arg_pieces))


# We have to override the usual Click processing of `--help` here. The issue is
# that click will process this option before processing anything else, but because we are
# dynamically generating subcommands based on the content of other options, the output of --help
# actually depends on these other options. So we opt out of Click's short-circuiting
# behavior of `--help` by setting `help_option_names=[]`, ensuring that we can process the other
# options first and generate the correct subcommands. We then add a custom `--help` option that
# gets invoked inside the callback.
@click.group(
    name="defs",
    cls=ScaffoldDefsGroup,
    invoke_without_command=True,
    context_settings={"help_option_names": []},
)
@click.option("-h", "--help", "help_", is_flag=True, help="Show this message and exit.")
@dg_global_options
@click.pass_context
def scaffold_defs_group(context: click.Context, help_: bool, **global_options: object) -> None:
    """Commands for scaffolding Dagster code."""
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


@scaffold_defs_group.command(
    name="inline-component",
    cls=ScaffoldDefsSubCommand,
)
@click.argument("path", type=str)
@click.option(
    "--typename",
    type=str,
    required=True,
)
@click.option(
    "--superclass",
    type=str,
    help="The superclass for the component to scaffold. If unset, `dg.Component` will be used.",
)
@cli_telemetry_wrapper
def scaffold_defs_inline_component(
    path: str,
    typename: str,
    superclass: Optional[str],
) -> None:
    """Scaffold a new Dagster component."""
    # We need to pass the global options to the command, but we don't want to
    # pass them to the subcommand. So we remove them from the context.
    context = click.get_current_context()
    cli_config = get_config_from_cli_context(context)
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    if dg_context.has_object_at_defs_path(path):
        exit_with_error(f"A component instance at `{path}` already exists.")

    scaffold_inline_component(
        Path(path),
        typename,
        superclass,
        dg_context,
    )


def _core_scaffold(
    dg_context: DgContext,
    cli_context: click.Context,
    object_key: EnvRegistryKey,
    defs_path: str,
    key_value_params: Mapping[str, Any],
    scaffold_format: ScaffoldFormatOptions,
    json_params: Optional[Mapping[str, Any]] = None,
) -> None:
    from dagster.components.core.package_entry import is_scaffoldable_object_key
    from pydantic import ValidationError

    if not is_scaffoldable_object_key(object_key):
        exit_with_error(f"Scaffoldable object type `{object_key.to_typename()}` not found.")
    elif dg_context.has_object_at_defs_path(defs_path):
        exit_with_error(f"Path `{(dg_context.defs_path / defs_path).absolute()}` already exists.")

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

    try:
        scaffold_registry_object(
            Path(dg_context.defs_path) / defs_path,
            object_key.to_typename(),
            scaffold_params,
            dg_context,
            scaffold_format,
        )
    except ValidationError as e:
        exit_with_error(
            (
                f"Error validating scaffold parameters for `{object_key.to_typename()}`:\\n\\n"
                f"{e.json(indent=4)}"
            ),
            do_format=False,
        )
