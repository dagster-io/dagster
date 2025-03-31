import contextlib
import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, NamedTuple, Optional

import click
import packaging.version
import yaml
from dagster_shared.serdes.objects import LibraryObjectKey

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.component import RemoteLibraryObjectRegistry, all_components_schema_from_dg_context
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import (
    DgClickCommand,
    DgClickGroup,
    exit_with_error,
    generate_missing_component_type_error_message,
)
from dagster_dg.utils.editor import (
    install_or_update_yaml_schema_extension,
    recommend_yaml_extension,
)
from dagster_dg.utils.telemetry import cli_telemetry_wrapper

_DEFAULT_SCHEMA_FOLDER_NAME = ".vscode"


@click.group(name="utils", cls=DgClickGroup)
def utils_group():
    """Assorted utility commands."""


@utils_group.command(name="configure-editor", cls=DgClickCommand)
@dg_global_options
@cli_telemetry_wrapper
@click.argument("editor", type=click.Choice(["vscode", "cursor"]))
def configure_editor_command(
    editor: str,
    **global_options: object,
) -> None:
    """Generates and installs a VS Code or Cursor extension which provides JSON schemas for Components types specified by YamlComponentsLoader objects."""
    executable_name = "code" if editor == "vscode" else "cursor"

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    recommend_yaml_extension(executable_name)

    schema_folder = dg_context.root_path / _DEFAULT_SCHEMA_FOLDER_NAME
    schema_folder.mkdir(exist_ok=True)

    schema_path = schema_folder / "schema.json"
    schema_path.write_text(json.dumps(all_components_schema_from_dg_context(dg_context), indent=2))

    install_or_update_yaml_schema_extension(executable_name, dg_context.root_path, schema_path)


# ########################
# ##### INSPECT COMPONENT TYPE
# ########################


@utils_group.command(name="inspect-component-type", cls=DgClickCommand)
@click.argument("component_type", type=str)
@click.option("--description", is_flag=True, default=False)
@click.option("--scaffold-params-schema", is_flag=True, default=False)
@click.option("--component-schema", is_flag=True, default=False)
@dg_global_options
@cli_telemetry_wrapper
def inspect_component_type_command(
    component_type: str,
    description: bool,
    scaffold_params_schema: bool,
    component_schema: bool,
    **global_options: object,
) -> None:
    """Get detailed information on a registered Dagster component type."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_defined_registry_environment(Path.cwd(), cli_config)
    registry = RemoteLibraryObjectRegistry.from_dg_context(dg_context)
    component_key = LibraryObjectKey.from_typename(component_type)
    if not registry.has(component_key):
        exit_with_error(generate_missing_component_type_error_message(component_type))
    elif sum([description, scaffold_params_schema, component_schema]) > 1:
        exit_with_error(
            "Only one of --description, --scaffold-params-schema, and --component-schema can be specified."
        )

    component_type_snap = registry.get_component_type(component_key)

    if description:
        if component_type_snap.description:
            click.echo(component_type_snap.description)
        else:
            click.echo("No description available.")
    elif scaffold_params_schema:
        if component_type_snap.scaffolder_schema:
            click.echo(_serialize_json_schema(component_type_snap.scaffolder_schema))
        else:
            click.echo("No scaffold params schema defined.")
    elif component_schema:
        if component_type_snap.schema:
            click.echo(_serialize_json_schema(component_type_snap.schema))
        else:
            click.echo("No component schema defined.")

    # print all available metadata
    else:
        click.echo(component_type)
        if component_type_snap.description:
            click.echo("\nDescription:\n")
            click.echo(component_type_snap.description)
        if component_type_snap.scaffolder_schema:
            click.echo("\nScaffold params schema:\n")
            click.echo(_serialize_json_schema(component_type_snap.scaffolder_schema))
        if component_type_snap.schema:
            click.echo("\nComponent schema:\n")
            click.echo(_serialize_json_schema(component_type_snap.schema))


def _serialize_json_schema(schema: Mapping[str, Any]) -> str:
    return json.dumps(schema, indent=4)


def _workspace_entry_for_project(dg_context: DgContext) -> dict[str, dict[str, str]]:
    entry = {
        "working_directory": str(dg_context.root_path),
        "module_name": str(dg_context.code_location_target_module_name),
        "location_name": dg_context.code_location_name,
    }
    if dg_context.use_dg_managed_environment:
        entry["executable_path"] = str(dg_context.project_python_executable)
    return {"python_module": entry}


def _semver_less_than(version: str, other: str) -> bool:
    try:
        parsed_version = packaging.version.parse(version)
        parsed_other = packaging.version.parse(other)
        return parsed_version < parsed_other
    except packaging.version.InvalidVersion:
        return False


MIN_ENV_VAR_INJECTION_VERSION = "1.10.8"


@contextmanager
def create_temp_workspace_file(dg_context: DgContext) -> Iterator[str]:
    with NamedTemporaryFile(mode="w+", delete=True) as temp_workspace_file:
        entries = []
        if dg_context.is_project:
            entries.append(_workspace_entry_for_project(dg_context))
        elif dg_context.is_workspace:
            for spec in dg_context.project_specs:
                project_root = dg_context.root_path / spec.path
                project_context: DgContext = dg_context.with_root_path(project_root)

                if (
                    project_context.use_dg_managed_environment
                    and (project_context.root_path / ".env").exists()
                    and _semver_less_than(
                        project_context.get_module_version("dagster"), MIN_ENV_VAR_INJECTION_VERSION
                    )
                ):
                    click.echo(
                        f"Warning: Dagster version {project_context.get_module_version('dagster')} is less than the minimum required version for .env file environment "
                        f"variable injection ({MIN_ENV_VAR_INJECTION_VERSION}). Environment variables will not be injected for location {project_context.code_location_name}."
                    )
                entries.append(_workspace_entry_for_project(project_context))
        yaml.dump({"load_from": entries}, temp_workspace_file)
        temp_workspace_file.flush()
        yield temp_workspace_file.name


class DagsterCliCmd(NamedTuple):
    cmd_location: str
    cmd: list[str]
    workspace_file: Optional[str]


@contextlib.contextmanager
def create_dagster_cli_cmd(
    dg_context: DgContext, forward_options: list[str], run_cmds: list[str]
) -> Iterator[DagsterCliCmd]:
    cmd = [*run_cmds, *forward_options]
    if dg_context.is_project:
        cmd_location = dg_context.get_executable("dagster")
        with create_temp_workspace_file(dg_context) as temp_workspace_file:
            yield DagsterCliCmd(
                cmd_location=str(cmd_location), cmd=cmd, workspace_file=temp_workspace_file
            )
        # yield CommandArgs(cmd_location=str(cmd_location), cmd=cmd, workspace_file=None)
    elif dg_context.is_workspace:
        with create_temp_workspace_file(dg_context) as temp_workspace_file:
            yield DagsterCliCmd(
                cmd=cmd,
                cmd_location="ephemeral",
                workspace_file=temp_workspace_file,
            )
    else:
        exit_with_error("This command must be run inside a code location or deployment directory.")
