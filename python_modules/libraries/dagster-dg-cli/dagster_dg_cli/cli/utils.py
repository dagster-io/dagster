import asyncio
import json
import tempfile
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional

import click
from dagster._cli.utils import get_possibly_temporary_instance_for_cli
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

from dagster_dg_cli.utils.ui import clear_screen, daggy_spinner_char, format_duration

if TYPE_CHECKING:
    from dagster.components.component.state_backed_component import StateBackedComponent

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
@click.option("--component-schema", is_flag=True, default=False)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def inspect_component_type_command(
    component_type: str,
    description: bool,
    scaffold_params_schema: bool,
    component_schema: bool,
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
    elif sum([description, scaffold_params_schema, component_schema]) > 1:
        exit_with_error(
            "Only one of --description, --scaffold-params-schema, and --component-schema can be specified."
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
    elif component_schema:
        if entry_snap.component_schema:
            click.echo(_serialize_json_schema(entry_snap.component_schema))
        else:
            click.echo("No component schema defined.")
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

    def echo(self, key: str, max_key_length: int) -> None:
        padded_key = key.ljust(max_key_length)
        if self.status == "refreshing":
            primary_color = "bright_black"
            elapsed = time.time() - self.start_time
            status_char = daggy_spinner_char(elapsed)
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
        click.echo(
            f"[ {padded_key} ] {click.style(status_char, fg=primary_color)} {click.style(self.status, fg=primary_color)} {click.style(duration_str, fg='white', dim=True)}"
        )


def _show_progress_header(statuses: dict[str, ComponentStateRefreshStatus]) -> None:
    """Display progress header based on current status counts."""
    success_count = sum(1 for s in statuses.values() if s.status == "done")
    error_count = sum(1 for s in statuses.values() if s.status == "failed")
    total = len(statuses)
    completed = success_count + error_count

    if completed == total:
        if error_count == 0:
            message = f"All {total} components refreshed successfully!"
            click.echo(click.style(message, fg="green", bold=True))
        else:
            message = f"Finished refreshing {total} components ({success_count} succeeded, {error_count} failed)"
            click.echo(click.style(message, fg="yellow", bold=True))
    else:
        message = f"Refreshing defs state... ({completed}/{total} complete)"
        click.echo(click.style(message, bold=True))


def _update_display(
    statuses: dict[str, ComponentStateRefreshStatus], initial: bool = False
) -> None:
    import sys

    clear_screen(len(statuses) + 2, initial)  # +2 for header and empty line
    _show_progress_header(statuses)
    click.echo()  # Empty line for spacing

    max_key_length = max(len(key) for key in statuses.keys()) if statuses else 0
    for key, status in statuses.items():
        status.echo(key, max_key_length)

    sys.stdout.flush()


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
    _update_display(statuses)


async def _refresh_component(
    component: "StateBackedComponent", statuses: dict[str, ComponentStateRefreshStatus]
) -> None:
    key = component.get_state_key()
    start_time = time.time()
    statuses[key] = ComponentStateRefreshStatus(status="refreshing", start_time=start_time)

    try:
        await component.refresh_state()
        _complete_component_refresh(key, statuses, success=True)
    except Exception as e:
        _complete_component_refresh(key, statuses, success=False, error=e)


async def _refresh_components_with_display(
    components: list["StateBackedComponent"],
    statuses: dict[str, ComponentStateRefreshStatus],
) -> None:
    """Refresh all components concurrently with live display updates."""
    # Create refresh tasks
    refresh_tasks = [_refresh_component(component, statuses) for component in components]

    # Create a task for periodic display updates (for spinner animation)
    async def update_display_periodically():
        while any(status.status == "refreshing" for status in statuses.values()):
            _update_display(statuses)
            await asyncio.sleep(0.1)  # Update display every 100ms for smooth animation

    display_task = asyncio.create_task(update_display_periodically())

    try:
        # Wait for all refresh tasks to complete
        await asyncio.gather(*refresh_tasks)

        # Cancel the display update task
        display_task.cancel()
        try:
            await display_task
        except asyncio.CancelledError:
            pass

        # Final display update
        _update_display(statuses)
    except Exception:
        # Make sure we cancel the display task on error
        display_task.cancel()
        try:
            await display_task
        except asyncio.CancelledError:
            pass
        raise


@utils_group.command(name="refresh-component-state", cls=DgClickCommand)
@dg_path_options
@dg_global_options
@click.option(
    "--defs-key",
    multiple=True,
    help="Only refresh components with the specified defs-key. Can be specified multiple times.",
)
@cli_telemetry_wrapper
def refresh_component_state(
    target_path: Path,
    defs_key: tuple[str, ...],
    **other_opts: object,
) -> None:
    """Refresh the component state for the current project."""
    cli_config = normalize_cli_config(other_opts, click.get_current_context())
    dg_context = DgContext.for_project_environment(target_path, cli_config)

    from dagster.components.component.state_backed_component import StateBackedComponent
    from dagster.components.core.component_tree import ComponentTree

    with get_possibly_temporary_instance_for_cli("dg utils refresh-component-state"):
        tree = ComponentTree.for_project(dg_context.root_path)
        all_components = tree.get_all_components(of_type=StateBackedComponent)

        # Filter components by defs-key if specified
        if defs_key:
            defs_key_set = set(defs_key)
            to_refresh = [
                component
                for component in all_components
                if component.get_state_key() in defs_key_set
            ]

            # Check if any specified defs-keys don't exist
            found_keys = {component.get_state_key() for component in to_refresh}
            missing_keys = defs_key_set - found_keys
            if missing_keys:
                available_keys = {component.get_state_key() for component in all_components}
                click.echo("Error: The following defs-keys were not found:")
                for key in sorted(missing_keys):
                    click.echo(f"  {key}")
                click.echo("\nAvailable defs-keys:")
                for key in sorted(available_keys):
                    click.echo(f"  {key}")
                exit_with_error("One or more specified defs-keys were not found.")
        else:
            to_refresh = all_components

        # Initialize statuses and show initial display
        current_time = time.time()
        statuses = {
            component.get_state_key(): ComponentStateRefreshStatus(
                status="refreshing", start_time=current_time
            )
            for component in to_refresh
        }
        _update_display(statuses, initial=True)

        # Run the refresh process with live updates
        asyncio.run(_refresh_components_with_display(to_refresh, statuses))

        # Check for errors and raise them
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
