from pathlib import Path

import click
from dagster_dg_core.component import EnvRegistry
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand, exit_with_error, snakecase
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.serdes.objects import EnvRegistryKey

from dagster_dg_cli.scaffold import scaffold_component


def _parse_component_name(dg_context: DgContext, name: str) -> tuple[str, str]:
    """Parse the name into a module name and class name."""
    if "." in name:
        module_name, class_name = name.rsplit(".", 1)
        if not module_name.startswith(dg_context.root_module_name):
            exit_with_error(
                f"Component `{name}` must be nested under the root module `{dg_context.root_module_name}`."
            )
        elif dg_context.has_registry_module_entry_point and not module_name.startswith(
            dg_context.default_registry_root_module_name
        ):
            exit_with_error(
                f"Component `{name}` must be nested under the declared entry point module `{dg_context.default_registry_root_module_name}`."
            )
    else:
        final_module = snakecase(name)
        module_name, class_name = (
            f"{dg_context.default_registry_root_module_name}.{final_module}",
            name,
        )
    return module_name, class_name


@click.command(
    name="component",
    cls=DgClickCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--model/--no-model",
    is_flag=True,
    default=True,
    help="Whether to automatically make the generated class inherit from dagster.components.Model.",
)
@click.argument("name", type=str)
@dg_path_options
@dg_global_options
@click.pass_context
@cli_telemetry_wrapper
def scaffold_component_command(
    context: click.Context, name: str, model: bool, target_path: Path, **global_options: object
) -> None:
    """Scaffold of a custom Dagster component type.

    This command must be run inside a Dagster project directory. The component type scaffold
    will be placed in submodule `<project_name>.lib.<name>`.
    """
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_component_library_environment(target_path, cli_config)
    registry = EnvRegistry.from_dg_context(dg_context)

    module_name, class_name = _parse_component_name(dg_context, name)

    component_key = EnvRegistryKey(name=class_name, namespace=module_name)
    if registry.has(component_key):
        exit_with_error(f"Component type `{component_key.to_typename()}` already exists.")

    path = dg_context.get_path_for_local_module(module_name, require_exists=False).with_suffix(
        ".py"
    )
    if path.exists():
        exit_with_error(f"A module at `{path}` already exists. Please choose a different name.")

    scaffold_component(
        dg_context=dg_context, class_name=class_name, module_name=module_name, model=model
    )
