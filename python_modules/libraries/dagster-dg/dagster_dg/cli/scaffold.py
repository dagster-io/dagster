from collections.abc import Mapping
from copy import copy
from pathlib import Path
from typing import Any, Optional

import click
from click.core import ParameterSource
from typer.rich_utils import rich_format_help

from dagster_dg.cli.shared_options import (
    GLOBAL_OPTIONS,
    dg_editable_dagster_options,
    dg_global_options,
)
from dagster_dg.component import RemoteComponentRegistry, RemoteComponentType
from dagster_dg.component_key import ComponentKey
from dagster_dg.config import (
    DgWorkspaceNewProjectOptions,
    get_config_from_cli_context,
    has_config_on_cli_context,
    normalize_cli_config,
    set_config_on_cli_context,
)
from dagster_dg.context import DgContext
from dagster_dg.scaffold import (
    scaffold_component_instance,
    scaffold_component_type,
    scaffold_project,
    scaffold_workspace,
)
from dagster_dg.utils import (
    DgClickCommand,
    DgClickGroup,
    exit_with_error,
    generate_missing_component_type_error_message,
    json_schema_property_to_click_option,
    not_none,
    parse_json_option,
    snakecase,
)

DEFAULT_WORKSPACE_NAME = "dagster-workspace"


@click.group(name="scaffold", cls=DgClickGroup)
def scaffold_group():
    """Commands for scaffolding Dagster code."""


# ########################
# ##### WORKSPACE
# ########################


@scaffold_group.command(name="workspace", cls=DgClickCommand)
@click.argument("name", type=str, default=DEFAULT_WORKSPACE_NAME)
@dg_editable_dagster_options
@dg_global_options
def workspace_scaffold_command(
    name: str,
    use_editable_dagster: Optional[str],
    use_editable_components_package_only: Optional[str],
    **global_options: object,
):
    """Initialize a new Dagster workspace.

    The scaffolded workspace folder has the following structure:

    \b
    ├── dagster-workspace
    │   ├── projects
    |   |   └── <Dagster projects go here>
    |   ├── libraries
    |   |   └── <Shared packages go here>
    │   └── pyproject.toml

    """  # noqa: D301
    new_project_options = DgWorkspaceNewProjectOptions.get_raw_from_cli(
        use_editable_dagster,
        use_editable_components_package_only,
    )
    scaffold_workspace(name, new_project_options)


# ########################
# ##### PROJECT
# ########################


@scaffold_group.command(name="project", cls=DgClickCommand)
@click.argument("path", type=Path)
@click.option(
    "--skip-venv",
    is_flag=True,
    default=False,
    help="Do not create a virtual environment for the project.",
)
@click.option(
    "--populate-cache/--no-populate-cache",
    is_flag=True,
    default=True,
    help="Whether to automatically populate the component type cache for the project.",
    hidden=True,
)
@dg_editable_dagster_options
@dg_global_options
def scaffold_project_command(
    path: Path,
    skip_venv: bool,
    populate_cache: bool,
    use_editable_dagster: Optional[str],
    use_editable_components_package_only: Optional[str],
    **global_options: object,
) -> None:
    """Scaffold a Dagster project file structure and a uv-managed virtual environment scoped
    to the project.

    This command can be run inside or outside of a workspace directory. If run inside a workspace,
    the project will be created within the workspace directory's project directory.

    The project file structure defines a Python package with some pre-existing internal
    structure:

    \b
    ├── <name>
    │   ├── __init__.py
    │   ├── defs
    │   ├── definitions.py
    │   └── lib
    │       └── __init__.py
    ├── <name>_tests
    │   └── __init__.py
    └── pyproject.toml

    The `<name>.components` directory holds components (which can be created with `dg scaffold
    component`).  The `<name>.lib` directory holds custom component types scoped to the project
    (which can be created with `dg scaffold component-type`).
    """  # noqa: D301
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), cli_config)

    abs_path = path.resolve()
    if dg_context.is_workspace:
        if dg_context.has_project(abs_path.relative_to(dg_context.workspace_root_path)):
            exit_with_error(f"The current workspace already specifies a project at {abs_path}.")
        elif abs_path.exists():
            exit_with_error(f"A file or directory already exists at {abs_path}.")

    scaffold_project(
        abs_path,
        dg_context,
        use_editable_dagster=use_editable_dagster,
        use_editable_components_package_only=use_editable_components_package_only,
        skip_venv=skip_venv,
        populate_cache=populate_cache,
    )


# ########################
# ##### COMPONENT
# ########################


# The `dg scaffold component` command is special because its subcommands are dynamically generated
# from the registered component types in the project. Because the registered component types
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
        cmd = super().get_command(cli_context, cmd_name)
        if cmd is None:
            exit_with_error(generate_missing_component_type_error_message(cmd_name))
        return cmd

    def list_commands(self, cli_context: click.Context) -> list[str]:
        if not self._commands_defined:
            self._define_commands(cli_context)
        return super().list_commands(cli_context)

    def _define_commands(self, cli_context: click.Context) -> None:
        """Dynamically define a command for each registered component type."""
        if not has_config_on_cli_context(cli_context):
            cli_context.invoke(not_none(self.callback), **cli_context.params)
        config = get_config_from_cli_context(cli_context)
        dg_context = DgContext.for_defined_registry_environment(Path.cwd(), config)

        registry = RemoteComponentRegistry.from_dg_context(dg_context)
        for key, component_type in registry.items():
            command = _create_component_scaffold_subcommand(key, component_type)
            self.add_command(command)


class ComponentScaffoldSubCommand(DgClickCommand):
    # We have to override this because the implementation of `format_help` used elsewhere will only
    # pull parameters directly off the target command. For these component scaffold subcommands  we need
    # to expose the global options, which are defined on the preceding group rather than the command
    # itself.
    def format_help(self, context: click.Context, formatter: click.HelpFormatter):
        """Customizes the help to include hierarchical usage."""
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

    def format_usage(self, context: click.Context, formatter: click.HelpFormatter) -> None:
        if not isinstance(self, click.Command):
            raise ValueError("This mixin is only intended for use with click.Command instances.")
        arg_pieces = self.collect_usage_pieces(context)
        command_parts = context.command_path.split(" ")
        command_parts.insert(-1, "[GLOBAL OPTIONS]")
        return formatter.write_usage(" ".join(command_parts), " ".join(arg_pieces))


# We have to override the usual Click processing of `--help` here. The issue is
# that click will process this option before processing anything else, but because we are
# dynamically generating subcommands based on the content of other options, the output of --help
# actually depends on these other options. So we opt out of Click's short-circuiting
# behavior of `--help` by setting `help_option_names=[]`, ensuring that we can process the other
# options first and generate the correct subcommands. We then add a custom `--help` option that
# gets invoked inside the callback.
@scaffold_group.group(
    name="component",
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
    component_key: ComponentKey, component_type: RemoteComponentType
) -> DgClickCommand:
    # We need to "reset" the help option names to the default ones because we inherit the parent
    # value of context settings from the parent group, which has been customized.
    @click.command(
        name=component_key.to_typename(),
        cls=ComponentScaffoldSubCommand,
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    @click.argument("component_instance_name", type=str)
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
        component_instance_name: str,
        json_params: Mapping[str, Any],
        **key_value_params: Any,
    ) -> None:
        f"""Scaffold of a {component_type.name} component.

        This command must be run inside a Dagster project directory. The component scaffold will be
        placed in submodule `<project_name>.components.<COMPONENT_NAME>`.

        Components can optionally be passed scaffold parameters. There are two ways to do this:

        (1) Passing a single --json-params option with a JSON string of parameters. For example:

            dg component scaffold foo.bar my_component --json-params '{{"param1": "value", "param2": "value"}}'`.

        (2) Passing each parameter as an option. For example:

            dg component scaffold foo.bar my_component --param1 value1 --param2 value2`

        It is an error to pass both --json-params and key-value pairs as options.
        """
        cli_config = get_config_from_cli_context(cli_context)
        dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

        registry = RemoteComponentRegistry.from_dg_context(dg_context)
        if not registry.has(component_key):
            exit_with_error(f"Component type `{component_key.to_typename()}` not found.")
        elif dg_context.has_component_instance(component_instance_name):
            exit_with_error(
                f"A component instance named `{component_instance_name}` already exists."
            )

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
            Path(dg_context.defs_path) / component_instance_name,
            component_key.to_typename(),
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
# ##### COMPONENT TYPE
# ########################


@scaffold_group.command(name="component-type", cls=DgClickCommand)
@click.argument("name", type=str)
@dg_global_options
@click.pass_context
def component_type_scaffold_command(
    context: click.Context, name: str, **global_options: object
) -> None:
    """Scaffold of a custom Dagster component type.

    This command must be run inside a Dagster project directory. The component type scaffold
    will be placed in submodule `<project_name>.lib.<name>`.
    """
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_component_library_environment(Path.cwd(), cli_config)
    registry = RemoteComponentRegistry.from_dg_context(dg_context)

    module_name = snakecase(name)
    component_key = ComponentKey(
        name=name, namespace=dg_context.default_component_library_module_name
    )
    if registry.has(component_key):
        exit_with_error(f"Component type`{component_key.to_typename()}` already exists.")

    scaffold_component_type(dg_context, name, module_name)
