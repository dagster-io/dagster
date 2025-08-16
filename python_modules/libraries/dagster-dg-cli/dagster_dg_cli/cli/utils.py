import json
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
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared import check
from dagster_shared.serdes.objects import EnvRegistryKey
from packaging.version import Version

from dagster_dg_cli.cli.agent_project_context import agent_project_context_command
from dagster_dg_cli.cli.agent_project_context.schema_utils import generate_yaml_template_from_schema
from dagster_dg_cli.utils.yaml_template_generator import (
    generate_defs_yaml_example_values,
    generate_defs_yaml_schema,
)

DEFAULT_SCHEMA_FOLDER_NAME = ".dg"


@click.group(name="utils", cls=DgClickGroup)
def utils_group():
    """Assorted utility commands."""


utils_group.add_command(agent_project_context_command)


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
@click.option(
    "--template",
    is_flag=True,
    default=False,
    help="Output component schema as LLM-friendly YAML template",
)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def inspect_component_type_command(
    component_type: str,
    description: bool,
    scaffold_params_schema: bool,
    component_schema: bool,
    defs_yaml_json_schema: bool,
    defs_yaml_schema: bool,
    defs_yaml_example_values: bool,
    template: bool,
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
                component_schema,
                defs_yaml_json_schema,
                defs_yaml_schema,
                defs_yaml_example_values,
                template,
            ]
        )
        > 1
    ):
        exit_with_error(
            "Only one of --description, --scaffold-params-schema, --component-schema, --defs-yaml-json-schema, --defs-yaml-schema, --defs-yaml-example-values, and --template can be specified."
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
    elif defs_yaml_json_schema:
        json_schema = _generate_defs_yaml_json_schema(component_type, entry_snap)
        click.echo(_serialize_json_schema(json_schema))
    elif defs_yaml_schema:
        schema_template = _generate_defs_yaml_schema(component_type, entry_snap)
        click.echo(schema_template)
    elif defs_yaml_example_values:
        example_values = _generate_defs_yaml_example_values(component_type, entry_snap)
        click.echo(example_values)
    elif template:
        if entry_snap.component_schema:
            component_name = component_type.split(".")[-1]
            template_output = generate_yaml_template_from_schema(
                entry_snap.component_schema, component_name
            )
            click.echo(template_output)
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
