import asyncio
import itertools
import json
import tempfile
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional

import click
from dagster_dg_core.component import EnvRegistry, all_components_schema_from_dg_context
from dagster_dg_core.config import (
    DgRawBuildConfig,
    merge_build_configs,
    merge_container_context_configs,
    normalize_cli_config,
)
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import (
    DgClickCommand,
    DgClickGroup,
    exit_with_error,
    generate_missing_registry_object_error_message,
)
from dagster_dg_core.utils.editor import (
    install_or_update_yaml_schema_extension,
    recommend_yaml_extension,
)
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared import check
from dagster_shared.record import record, replace
from dagster_shared.serdes.objects import EnvRegistryKey
from packaging.version import Version
from rich.live import Live
from rich.text import Text

from dagster_dg_cli.utils.ui import DAGGY_SPINNER_FRAMES, format_duration
from dagster_dg_cli.utils.yaml_template_generator import (
    generate_defs_yaml_example_values,
    generate_defs_yaml_schema,
)

if TYPE_CHECKING:
    from dagster.components.component.state_backed_component import StateBackedComponent
    from dagster.components.core.component_tree import ComponentTree

DEFAULT_SCHEMA_FOLDER_NAME = ".dg"


@click.group(name="utils", cls=DgClickGroup)
def utils_group():
    """Assorted utility commands."""


def _generate_component_schema(dg_context: DgContext, output_path: Optional[Path] = None) -> Path:
    schema_path = output_path
    if not schema_path:
        schema_folder = dg_context.root_path / DEFAULT_SCHEMA_FOLDER_NAME
        schema_folder.mkdir(exist_ok=True)

        schema_path = schema_folder / "schema.json"

    schema_path.write_text(json.dumps(all_components_schema_from_dg_context(dg_context), indent=2))
    return schema_path


@utils_group.command(name="generate-component-schema", cls=DgClickCommand)
@dg_global_options
@cli_telemetry_wrapper
@click.option("--output-path", type=click.Path(exists=False, file_okay=True, dir_okay=False))
def generate_component_schema(
    output_path: Optional[str],
    **global_options: object,
) -> None:
    """Generates a JSON schema for the component types installed in the current project."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    _generate_component_schema(dg_context, Path(output_path) if output_path else None)


@utils_group.command(name="configure-editor", cls=DgClickCommand)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
@click.argument("editor", type=click.Choice(["vscode", "cursor"]))
def configure_editor_command(
    editor: str,
    target_path: Path,
    **global_options: object,
) -> None:
    """Generates and installs a VS Code or Cursor extension which provides JSON schemas for Components types specified by YamlComponentsLoader objects."""
    executable_name = "code" if editor == "vscode" else "cursor"

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(target_path, cli_config)

    recommend_yaml_extension(executable_name)
    schema_path = _generate_component_schema(dg_context)
    install_or_update_yaml_schema_extension(executable_name, dg_context.root_path, schema_path)


# ########################
# ##### INSPECT COMPONENT TYPE
# ########################


@utils_group.command(name="inspect-component", cls=DgClickCommand)
@click.argument("component_type", type=str)
@click.option("--description", is_flag=True, default=False)
@click.option("--scaffold-params-schema", is_flag=True, default=False)
@click.option("--defs-yaml-json-schema", is_flag=True, default=False)
@click.option(
    "--defs-yaml-schema",
    is_flag=True,
    default=False,
    help="Generate LLM-optimized YAML template with inline documentation and type hints. "
    "Unlike JSON schemas designed for validation, this YAML format includes human-readable "
    "annotations and structured documentation that LLMs can better parse and understand. "
    "Includes Required/Optional annotations, plain English type descriptions, field "
    "descriptions inline with properties, and serves as both documentation and code "
    "generation scaffold optimized for AI consumption.",
)
@click.option(
    "--defs-yaml-example-values",
    is_flag=True,
    default=False,
    help="Generate YAML example values optimized for LLM understanding and code generation",
)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def inspect_component_type_command(
    component_type: str,
    description: bool,
    scaffold_params_schema: bool,
    defs_yaml_json_schema: bool,
    defs_yaml_schema: bool,
    defs_yaml_example_values: bool,
    target_path: Path,
    **global_options: object,
) -> None:
    """Get detailed information on a registered Dagster component type."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.from_file_discovery_and_command_line_config(target_path, cli_config)
    registry = EnvRegistry.from_dg_context(dg_context)
    component_key = EnvRegistryKey.from_typename(component_type)
    if not registry.has(component_key):
        exit_with_error(generate_missing_registry_object_error_message(component_type))
    elif (
        sum(
            [
                description,
                scaffold_params_schema,
                defs_yaml_json_schema,
                defs_yaml_schema,
                defs_yaml_example_values,
            ]
        )
        > 1
    ):
        exit_with_error(
            "Only one of --description, --scaffold-params-schema, --defs-yaml-json-schema, --defs-yaml-schema, and --defs-yaml-example-values can be specified."
        )

    entry_snap = registry.get(component_key)
    if description:
        if entry_snap.description:
            click.echo(entry_snap.description)
        else:
            click.echo("No description available.")
    elif scaffold_params_schema:
        if entry_snap.scaffolder_schema:
            click.echo(_serialize_json_schema(entry_snap.scaffolder_schema))
        else:
            click.echo("No scaffold params schema defined.")
    elif defs_yaml_json_schema:
        json_schema = _generate_defs_yaml_json_schema(component_type, entry_snap)
        click.echo(_serialize_json_schema(json_schema))
    elif defs_yaml_schema:
        schema_template = _generate_defs_yaml_schema(component_type, entry_snap)
        click.echo(schema_template)
    elif defs_yaml_example_values:
        example_values = _generate_defs_yaml_example_values(component_type, entry_snap)
        click.echo(example_values)
    # print all available metadata
    else:
        click.echo(component_type)
        if entry_snap.description:
            click.echo("\nDescription:\n")
            click.echo(entry_snap.description)
        if entry_snap.scaffolder_schema:
            click.echo("\nScaffold params schema:\n")
            click.echo(_serialize_json_schema(entry_snap.scaffolder_schema))
        if entry_snap.component_schema:
            click.echo("\nComponent schema:\n")
            click.echo(_serialize_json_schema(entry_snap.component_schema))


def _serialize_json_schema(schema: Mapping[str, Any]) -> str:
    return json.dumps(schema, indent=4)


def _generate_defs_yaml_schema(component_type_str: str, entry_snap) -> str:
    """Generate LLM-optimized YAML template for a component's defs.yaml file.

    Creates a template with inline documentation and type hints optimized for AI
    understanding and code generation, separate from JSON schemas used for validation.

    Args:
        component_type_str: The component type identifier
        entry_snap: Component registry entry containing schema information

    Returns:
        A YAML template string with inline documentation and LLM-optimized annotations
    """
    # Use the component's existing schema, or empty schema if none available
    component_schema = entry_snap.component_schema or {}

    return generate_defs_yaml_schema(component_type_str, component_schema)


def _generate_defs_yaml_example_values(component_type_str: str, entry_snap) -> str:
    """Generate YAML example values for a component's defs.yaml file.

    Creates example values with sample data that users can copy and modify
    for their component configuration.
    """
    # Use the component's existing schema, or empty schema if none available
    component_schema = entry_snap.component_schema or {}

    return generate_defs_yaml_example_values(component_type_str, component_schema)


def _generate_defs_yaml_json_schema(component_type_str: str, entry_snap) -> dict[str, Any]:
    """Generate JSON schema for a complete defs.yaml file.

    Creates a JSON schema that includes all top-level defs.yaml fields (type, attributes,
    template_vars_module, requirements, post_processing) with the component's attributes
    schema merged into the attributes property.
    """
    from dagster.components.core.defs_module import ComponentFileModel

    # Get the base ComponentFileModel schema
    base_schema = ComponentFileModel.model_json_schema()

    # Get the component's attributes schema if available
    component_schema = entry_snap.component_schema or {}

    # If we have a component schema, use it for the attributes property
    if component_schema:
        base_schema["properties"]["attributes"] = component_schema

        # If the component schema has required fields, make attributes required
        if component_schema.get("required"):
            if "required" not in base_schema:
                base_schema["required"] = ["type"]
            if "attributes" not in base_schema["required"]:
                base_schema["required"].append("attributes")

    return base_schema


def _workspace_entry_for_project(
    dg_context: DgContext, use_executable_path: bool
) -> dict[str, dict[str, str]]:
    if not dg_context.config.project:
        exit_with_error("Unexpected empty project config.")

    key = "python_module"
    module_name = dg_context.code_location_target_module_name

    entry = {
        "working_directory": str(
            dg_context.get_path_for_local_module(dg_context.root_module_name).parent
        ),
        "module_name": module_name,
        "location_name": dg_context.code_location_name,
    }
    if use_executable_path:
        entry["executable_path"] = str(dg_context.project_python_executable)
    return {key: entry}


MIN_ENV_VAR_INJECTION_VERSION = Version("1.10.8")


@contextmanager
def create_temp_workspace_file(dg_context: DgContext) -> Iterator[str]:
    # defer for import performance
    import yaml

    check.invariant(
        dg_context.is_in_workspace or dg_context.is_project,
        "can only create a workspace file within a project or workspace context",
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_workspace_file = Path(temp_dir) / "workspace.yaml"

        entries = []
        if dg_context.is_project:
            entries.append(_workspace_entry_for_project(dg_context, use_executable_path=False))
        else:
            for spec in dg_context.project_specs:
                project_root = dg_context.root_path / spec.path
                project_context: DgContext = dg_context.with_root_path(project_root)

                entries.append(
                    _workspace_entry_for_project(project_context, use_executable_path=True)
                )

        temp_workspace_file.write_text(yaml.dump({"load_from": entries}))
        yield str(temp_workspace_file)


def _dagster_cloud_entry_for_project(
    dg_context: DgContext, workspace_context: Optional[DgContext]
) -> dict[str, Any]:
    merged_build_config: DgRawBuildConfig = merge_build_configs(
        workspace_context.build_config if workspace_context else None, dg_context.build_config
    )

    merged_container_context_config = merge_container_context_configs(
        workspace_context.container_context_config if workspace_context else None,
        dg_context.container_context_config,
    )

    return {
        "location_name": dg_context.code_location_name,
        "code_source": {
            **dg_context.target_args,
        },
        **({"build": merged_build_config} if merged_build_config else {}),
        **(
            {"container_context": merged_container_context_config}
            if merged_container_context_config
            else {}
        ),
    }


def create_temp_dagster_cloud_yaml_file(dg_context: DgContext, statedir: str) -> str:
    # defer for import performance
    import yaml

    check.invariant(
        dg_context.is_in_workspace or dg_context.is_project,
        "can only create a workspace file within a project or workspace context",
    )

    dagster_cloud_yaml_path = Path(statedir) / "dagster_cloud.yaml"
    with open(dagster_cloud_yaml_path, "w+") as temp_dagster_cloud_yaml_file:
        entries = []
        if dg_context.is_project:
            entries.append(_dagster_cloud_entry_for_project(dg_context, None))
        else:
            for spec in dg_context.project_specs:
                project_root = dg_context.root_path / spec.path
                project_context: DgContext = dg_context.with_root_path(project_root)
                entries.append(_dagster_cloud_entry_for_project(project_context, dg_context))
        yaml.dump({"locations": entries}, temp_dagster_cloud_yaml_file)
        temp_dagster_cloud_yaml_file.flush()
        return temp_dagster_cloud_yaml_file.name


@record
class ComponentStateRefreshStatus:
    status: Literal["refreshing", "done", "failed"]
    error: Optional[Exception] = None
    # For updating: start_time tracks when it began
    # For completed: duration tracks final elapsed time
    start_time: float = 0.0
    duration: Optional[float] = None

    @staticmethod
    def default() -> "ComponentStateRefreshStatus":
        return ComponentStateRefreshStatus(status="refreshing", start_time=time.time())

    def display_text(self, key: str, max_key_length: int, spinner_char: str) -> str:
        padded_key = key.ljust(max_key_length)
        if self.status == "refreshing":
            primary_color = "bright_black"
            elapsed = time.time() - self.start_time
            status_char = spinner_char
            duration_str = format_duration(elapsed)
        elif self.status == "done":
            primary_color = "green"
            status_char = "✓"
            duration_str = f"in {format_duration(self.duration)}"
        elif self.status == "failed":
            primary_color = "red"
            status_char = "✗"
            duration_str = f"after {format_duration(self.duration)}"
        else:
            raise ValueError(f"Invalid status: {self.status}")
        return f"[ {padded_key} ] {click.style(status_char, fg=primary_color)} {click.style(self.status, fg=primary_color)} {click.style(duration_str, fg='white', dim=True)}"


def _get_display_header(statuses: dict[str, ComponentStateRefreshStatus]) -> str:
    """Display progress header based on current status counts."""
    success_count = sum(1 for s in statuses.values() if s.status == "done")
    error_count = sum(1 for s in statuses.values() if s.status == "failed")
    total = len(statuses)
    completed = success_count + error_count

    if completed == total:
        if error_count == 0:
            message = f"All {total} components refreshed successfully!"
            return click.style(message, fg="green", bold=True)
        else:
            message = f"Finished refreshing {total} components ({success_count} succeeded, {error_count} failed)"
            return click.style(message, fg="yellow", bold=True)
    else:
        message = f"Refreshing defs state... ({completed}/{total} complete)"
        return click.style(message, bold=True)


def _echo_error_text_and_raise(statuses: dict[str, ComponentStateRefreshStatus]) -> None:
    errors = []
    for key, status in statuses.items():
        if status.status == "failed" and status.error:
            errors.append((key, status.error))

    if errors:
        click.echo("\n" + click.style("Detailed error information:", fg="red", bold=True))
        for key, error in errors:
            click.echo(
                f"  {click.style(key, fg='white', bold=True)}: {click.style(str(error), fg='red')}"
            )

        # Raise the first error (or you could create a composite error)
        raise errors[0][1]


def _get_display_text(statuses: dict[str, ComponentStateRefreshStatus], spinner_char: str) -> str:
    max_key_length = max(len(key) for key in statuses.keys()) if statuses else 0
    task_statuses = [
        status.display_text(key, max_key_length, spinner_char) for key, status in statuses.items()
    ]
    return "\n".join([_get_display_header(statuses)] + task_statuses)


def _complete_component_refresh(
    key: str,
    statuses: dict[str, ComponentStateRefreshStatus],
    success: bool,
    error: Optional[Exception] = None,
) -> None:
    """Complete a component refresh with the final status and duration."""
    prev = statuses[key]
    statuses[key] = replace(
        prev,
        duration=time.time() - prev.start_time,
        status="done" if success else "failed",
        error=error,
    )


async def _refresh_component(
    component: "StateBackedComponent", statuses: dict[str, ComponentStateRefreshStatus]
) -> None:
    key = component.get_defs_state_key()
    start_time = time.time()
    statuses[key] = ComponentStateRefreshStatus(status="refreshing", start_time=start_time)

    try:
        await component.refresh_state()
        _complete_component_refresh(key, statuses, success=True)
    except Exception as e:
        _complete_component_refresh(key, statuses, success=False, error=e)


def _get_components_to_refresh(
    tree: "ComponentTree", defs_state_keys: Optional[set[str]]
) -> list["StateBackedComponent"]:
    from dagster.components.component.state_backed_component import StateBackedComponent

    state_backed_components = tree.get_all_components(of_type=StateBackedComponent)
    defs_state_keys = defs_state_keys or {
        component.get_defs_state_key() for component in state_backed_components
    }

    components = [
        component
        for component in tree.get_all_components(of_type=StateBackedComponent)
        if component.get_defs_state_key() in defs_state_keys
    ]
    missing_defs_keys = defs_state_keys - {
        component.get_defs_state_key() for component in components
    }
    if missing_defs_keys:
        click.echo("Error: The following defs state keys were not found:")
        for key in sorted(missing_defs_keys):
            click.echo(f"  {key}")
        click.echo("Available defs state keys:")
        for key in sorted(
            [component.get_defs_state_key() for component in state_backed_components]
        ):
            click.echo(f"  {key}")
        exit_with_error("One or more specified defs state keys were not found.")

    return components


async def _refresh_component_state_impl(
    tree: "ComponentTree",
    defs_state_keys: Optional[set[str]],
) -> None:
    components = _get_components_to_refresh(tree, defs_state_keys)
    statuses = {
        component.get_defs_state_key(): ComponentStateRefreshStatus.default()
        for component in components
    }

    tasks = [
        asyncio.create_task(_refresh_component(component, statuses)) for component in components
    ]
    with Live(refresh_per_second=10) as live:
        spinner_char = itertools.cycle(DAGGY_SPINNER_FRAMES)
        while not all(task.done() for task in tasks):
            live.update(Text.from_ansi(_get_display_text(statuses, next(spinner_char))))
            await asyncio.sleep(0.1)
        await asyncio.gather(*tasks)
        live.update(Text.from_ansi(_get_display_text(statuses, next(spinner_char))))

    _echo_error_text_and_raise(statuses)


@utils_group.command(name="refresh-component-state", cls=DgClickCommand)
@dg_path_options
@dg_global_options
@click.option(
    "--defs-state-key",
    multiple=True,
    help="Only refresh components with the specified defs state key. Can be specified multiple times.",
)
@cli_telemetry_wrapper
def refresh_component_state(
    target_path: Path,
    defs_state_key: tuple[str, ...],
    **other_opts: object,
) -> None:
    """Refresh the component state for the current project."""
    from dagster._cli.utils import get_possibly_temporary_instance_for_cli
    from dagster.components.core.component_tree import ComponentTree

    cli_config = normalize_cli_config(other_opts, click.get_current_context())
    dg_context = DgContext.for_project_environment(target_path, cli_config)

    with get_possibly_temporary_instance_for_cli("dg utils refresh-component-state"):
        tree = ComponentTree.for_project(dg_context.root_path)
        defs_state_keys = set(defs_state_key) if defs_state_key else None
        asyncio.run(_refresh_component_state_impl(tree, defs_state_keys))
