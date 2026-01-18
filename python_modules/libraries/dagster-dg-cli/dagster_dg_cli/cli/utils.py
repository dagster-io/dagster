import asyncio
import itertools
import json
import tempfile
import threading
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

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
from dagster_shared.serdes import deserialize_value
from dagster_shared.serdes.objects import EnvRegistryKey
from packaging.version import Version
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from dagster_dg_cli.cli.defs_state import (
    ComponentStateRefreshStatus,
    get_updated_defs_state_info_task_and_statuses,
    raise_component_state_refresh_errors,
)
from dagster_dg_cli.utils.ui import DAGGY_SPINNER_FRAMES, format_duration
from dagster_dg_cli.utils.yaml_template_generator import (
    generate_defs_yaml_example_values,
    generate_defs_yaml_schema,
)

if TYPE_CHECKING:
    from dagster._core.instance.instance import DagsterInstance
    from dagster_shared.serdes.objects.models.defs_state_info import DefsStateManagementType

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
def create_temp_workspace_file(
    dg_context: DgContext, use_active_venv: bool = False
) -> Iterator[str]:
    # defer for import performance
    import sys

    import yaml

    check.invariant(
        dg_context.is_in_workspace or dg_context.is_project,
        "can only create a workspace file within a project or workspace context",
    )

    if use_active_venv:
        click.echo(f"Using active Python environment: {sys.executable}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_workspace_file = Path(temp_dir) / "workspace.yaml"

        entries = []
        if dg_context.is_project:
            entries.append(_workspace_entry_for_project(dg_context, use_executable_path=False))
        else:
            for spec in dg_context.project_specs:
                project_root = dg_context.root_path / spec.path
                project_context: DgContext = dg_context.with_root_path(project_root)

                # when using the active virtual environment, do not attempt to resolve the python executable
                use_executable_path = not use_active_venv

                entries.append(
                    _workspace_entry_for_project(
                        project_context, use_executable_path=use_executable_path
                    )
                )

        temp_workspace_file.write_text(yaml.dump({"load_from": entries}))
        yield str(temp_workspace_file)


def _dagster_cloud_entry_for_project(
    dg_context: DgContext, workspace_context: Optional[DgContext]
) -> dict[str, Any]:
    merged_build_config: DgRawBuildConfig = merge_build_configs(
        workspace_context.build_config if workspace_context else None,
        dg_context.build_config,
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


def _get_display_text_for_status(
    status: ComponentStateRefreshStatus,
    key: str,
    max_key_length: int,
    spinner_char: str,
) -> str:
    padded_key = key.ljust(max_key_length)
    if status.status == "refreshing":
        primary_color = "bright_black"
        elapsed = time.time() - status.start_time
        status_char = spinner_char
        duration_str = format_duration(elapsed)
    elif status.status == "done":
        primary_color = "green"
        status_char = "✓"
        duration_str = f"in {format_duration(status.duration)}"
    elif status.status == "failed":
        primary_color = "red"
        status_char = "✗"
        duration_str = f"after {format_duration(status.duration)}"
    else:
        raise ValueError(f"Invalid status: {status.status}")
    return f"[ {padded_key} ] {click.style(status_char, fg=primary_color)} {click.style(status.status, fg=primary_color)} {click.style(duration_str, fg='white', dim=True)}"


def _get_display_text(statuses: dict[str, ComponentStateRefreshStatus], spinner_char: str) -> str:
    max_key_length = max(len(key) for key in statuses.keys()) if statuses else 0
    task_statuses = [
        _get_display_text_for_status(status, key, max_key_length, spinner_char)
        for key, status in statuses.items()
    ]
    return "\n".join([_get_display_header(statuses)] + task_statuses)


async def _refresh_defs_state_with_live_display(
    project_path: Path,
    instance: "DagsterInstance",
    management_types: set["DefsStateManagementType"],
    defs_state_keys: Optional[set[str]] = None,
) -> None:
    defs_state_storage = check.not_none(instance.defs_state_storage)
    refresh_task, statuses = get_updated_defs_state_info_task_and_statuses(
        project_path, defs_state_storage, management_types, defs_state_keys
    )

    # Thread-safe coordination variables
    display_stop_event = threading.Event()
    display_lock = threading.Lock()

    def display_update_worker():
        """Display update worker that runs in a separate thread."""
        with Live(refresh_per_second=10) as live:
            spinner_char = itertools.cycle(DAGGY_SPINNER_FRAMES)
            while not display_stop_event.is_set():
                with display_lock:
                    live.update(Text.from_ansi(_get_display_text(statuses, next(spinner_char))))
                time.sleep(0.1)
            # Final update before stopping
            with display_lock:
                live.update(Text.from_ansi(_get_display_text(statuses, next(spinner_char))))

    # Start display thread
    display_thread = threading.Thread(target=display_update_worker, daemon=True)
    display_thread.start()

    try:
        # Wait for refresh task to complete
        await refresh_task
    finally:
        # Signal display thread to stop and wait for it
        display_stop_event.set()
        display_thread.join(timeout=1.0)  # Give it 1 second to finish

    raise_component_state_refresh_errors(statuses)


@utils_group.command(name="refresh-defs-state", cls=DgClickCommand)
@dg_path_options
@dg_global_options
@click.option(
    "--defs-state-key",
    multiple=True,
    help="Only refresh state for specified defs state key. Can be specified multiple times.",
)
@click.option(
    "--management-type",
    multiple=True,
    type=click.Choice(["LOCAL_FILESYSTEM", "VERSIONED_STATE_STORAGE"]),
    help="Only refresh components with the specified management type. Can be specified multiple times to include multiple types. Defaults to all management types except for LEGACY_CODE_SERVER_SNAPSHOTS.",
)
@click.option(
    "--instance-ref",
    type=click.STRING,
    required=False,
    hidden=True,
)
@cli_telemetry_wrapper
def refresh_defs_state(
    target_path: Path,
    defs_state_key: tuple[str, ...],
    management_type: tuple[str, ...],
    instance_ref: Optional[str],
    **other_opts: object,
) -> None:
    """Refresh the defs state for the current project."""
    from dagster._cli.utils import get_possibly_temporary_instance_for_cli
    from dagster._core.instance.config import is_dagster_home_set
    from dagster._core.instance.ref import InstanceRef
    from dagster_shared.serdes.objects.models.defs_state_info import DefsStateManagementType

    # Check if DAGSTER_HOME is set before proceeding
    if not instance_ref and not is_dagster_home_set():
        # emit warning
        click.echo(
            click.style(
                "DAGSTER_HOME is not set, which means defs state for VERSIONED_STATE_STORAGE components "
                "cannot be stored in a persistent location. \n"
                "You can resolve this warning by exporting the environment variable. "
                "For example, you can run the following command in your shell or "
                "include it in your shell configuration file:\n"
                '\texport DAGSTER_HOME="~/dagster_home"'
                "\n\n",
                fg="yellow",
            )
        )

    cli_config = normalize_cli_config(other_opts, click.get_current_context())
    dg_context = DgContext.for_project_environment(target_path, cli_config)

    with get_possibly_temporary_instance_for_cli(
        "dg utils refresh-defs-state",
        instance_ref=deserialize_value(instance_ref, InstanceRef) if instance_ref else None,
    ) as instance:
        defs_state_keys = set(defs_state_key) if defs_state_key else None
        management_types = (
            {DefsStateManagementType(mt) for mt in management_type}
            if management_type
            else {
                DefsStateManagementType.LOCAL_FILESYSTEM,
                DefsStateManagementType.VERSIONED_STATE_STORAGE,
            }
        )
        asyncio.run(
            _refresh_defs_state_with_live_display(
                dg_context.root_path, instance, management_types, defs_state_keys
            )
        )


@utils_group.command(
    name="integrations",
    cls=DgClickCommand,
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON.",
)
@cli_telemetry_wrapper
def integrations_docs_command(output_json: bool) -> None:
    """View an index of available Dagster integrations."""
    import requests  # defer for import perf

    response = requests.get("https://dagster-marketplace.vercel.app/api/integrations/index.json")
    response.raise_for_status()

    payload = response.json()
    if output_json:
        click.echo(json.dumps(payload, indent=2))
        return

    console = Console()
    table = Table(border_style="dim", show_lines=True)
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("PyPI")

    for integration in payload:
        # filter out incomplete entries
        if integration.get("name") and integration.get("description") and integration.get("pypi"):
            table.add_row(
                integration["name"],
                integration["description"],
                integration["pypi"],
            )

    console.print(table)
