import json
import subprocess
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

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
from dagster_dg_core.utils.mcp_client.claude_desktop import get_claude_desktop_config_path
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared import check
from dagster_shared.serdes.objects import EnvRegistryKey
from packaging.version import Version

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
# ##### MCP
# ########################

MCP_CONFIG = {
    "command": "uv",
    "args": ["tool", "run", "--from", "dagster-dg-cli", "dg", "mcp", "serve"],
}


def _inject_into_mcp_config_json(path: Path) -> None:
    contents = json.loads(path.read_text())
    if not contents.get("mcpServers"):
        contents["mcpServers"] = {}
    contents["mcpServers"]["dagster-dg-cli"] = MCP_CONFIG
    path.write_text(json.dumps(contents, indent=2))


@utils_group.command(name="configure-mcp", cls=DgClickCommand, hidden=True)
@dg_global_options
@cli_telemetry_wrapper
@click.argument(
    "mcp_client", type=click.Choice(["claude-desktop", "cursor", "claude-code", "vscode"])
)
def configure_mcp_command(
    mcp_client: str,
    **global_options: object,
) -> None:
    """Generates and installs a VS Code or Cursor extension which provides JSON schemas for Components types specified by YamlComponentsLoader objects."""
    if mcp_client == "claude-desktop":
        _inject_into_mcp_config_json(get_claude_desktop_config_path())
    elif mcp_client == "cursor":
        _inject_into_mcp_config_json(Path.home() / ".cursor" / "mcp.json")
    elif mcp_client == "vscode":
        cli_config = normalize_cli_config(global_options, click.get_current_context())
        dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)
        _inject_into_mcp_config_json(dg_context.root_path / ".vscode" / "mcp.json")
    elif mcp_client == "claude-code":
        subprocess.run(["claude", "mcp", "remove", "dagster-dg-cli"], check=False)
        subprocess.run(
            ["claude", "mcp", "add-json", "dagster-dg-cli", json.dumps(MCP_CONFIG)], check=True
        )


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

    if dg_context.config.project.autoload_defs:
        key = "autoload_defs_module"
        module_name = dg_context.defs_module_name
    else:
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
