import subprocess
from collections.abc import Sequence
from typing import Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("dagster-dg-cli")


def _subprocess(command: Sequence[str], cwd: Optional[str] = None) -> str:
    """Execute a subprocess command and return decoded output.

    Wrapper around subprocess.check_output that captures both stdout and stderr,
    providing better error context for MCP tool calls by exposing the full command
    output when errors occur.

    Args:
        command: Sequence of command arguments to execute (e.g., ['dg', 'list', 'components']).
        cwd: Working directory path where the command should be executed.

    Returns:
        Decoded UTF-8 string output from the executed command.

    Raises:
        Exception: If the subprocess fails, raises an exception with the command's error output.
    """
    try:
        return subprocess.check_output(
            command,
            cwd=cwd,
            stderr=subprocess.STDOUT,
        ).decode("utf-8")
    except subprocess.CalledProcessError as e:
        raise Exception(e.output)


@mcp.tool()
async def list_available_components(project_path: str) -> str:
    """List all available Dagster components that can be scaffolded in the project.

    This tool provides a comprehensive list of all component types available for scaffolding
    in the specified Dagster project. Components are reusable building blocks that can be
    used to create assets, jobs, schedules, and other Dagster definitions. Use this tool
    when you need to discover what components are available before scaffolding new definitions.

    The output includes component names, types, and brief descriptions to help you choose
    the appropriate component for your use case.

    Args:
        project_path: Absolute filesystem path to the root directory of your Dagster project
                     (the directory containing pyproject.toml with [tool.dg] or dg.toml).

    Returns:
        JSON-formatted string containing the list of available components with their metadata,
        including component names, types, and descriptions.
    """
    return _subprocess(
        [
            "dg",
            "list",
            "components",
            "--json",
        ],
        cwd=project_path,
    )


@mcp.tool()
async def scaffold_dagster_component_help(
    project_path: str,
    component_type: str,
) -> str:
    """Get detailed help and parameter requirements for scaffolding a specific component type.

    This tool provides comprehensive documentation about the parameters, options, and usage
    patterns for a specific component type. Use this before scaffolding a component to
    understand what arguments are required and what configuration options are available.

    The help output includes parameter descriptions, default values, validation rules,
    and example usage patterns specific to the component type.

    Args:
        project_path: Absolute filesystem path to the root directory of your Dagster project
                     (the directory containing pyproject.toml with [tool.dg] or dg.toml).
        component_type: Fully qualified component type identifier (e.g.,
                       'dagster_sling.SlingReplicationCollectionComponent',
                       'dagster_dbt.DbtProjectComponent'). Use list_available_components
                       to discover available component types.

    Returns:
        Detailed help text describing the component's parameters, usage patterns,
        and configuration options. This includes required and optional parameters,
        their types, default values, and example configurations.
    """
    return _subprocess(
        [
            "dg",
            "scaffold",
            "defs",
            component_type,
            "--help",
        ],
        cwd=project_path,
    )


@mcp.tool()
async def scaffold_dagster_component(
    project_path: str, component_type: str, component_name: str, component_arguments: list[str]
) -> str:
    """Scaffold a new Dagster component with the specified configuration.

    This tool creates a new component directory structure with a defs.yaml file that can be
    customized with component-specific configuration. The scaffolding process sets up the
    basic file structure and configuration template needed for the component to function.

    After scaffolding, you'll typically need to:
    1. Edit the generated defs.yaml file with your specific configuration
    2. Run check_dagster_defs_yaml to validate the YAML syntax
    3. Run check_dagster_definitions to ensure the component loads correctly

    Args:
        project_path: Absolute filesystem path to the root directory of your Dagster project
                     (the directory containing pyproject.toml with [tool.dg] or dg.toml).
        component_type: Fully qualified component type identifier (e.g.,
                       'dagster_sling.SlingReplicationCollectionComponent').
                       Use list_available_components to find available types.
        component_name: Name for the new component instance. This will be used as the
                       directory name and component identifier. Should be a valid
                       Python identifier (letters, numbers, underscores only).
        component_arguments: List of command-line arguments to pass to the scaffold command.
                           Use scaffold_dagster_component_help to determine what arguments
                           are available for the specific component type.
                           Example: ['--connection-name', 'my_db', '--table-pattern', 'users_*']

    Returns:
        Output from the scaffold command, including the path to the created component
        directory and any additional setup instructions or warnings.
    """
    return _subprocess(
        [
            "dg",
            "scaffold",
            "defs",
            component_type,
            component_name,
            *component_arguments,
        ],
        cwd=project_path,
    )


@mcp.tool()
async def inspect_component_type(project_path: str, component_type: str) -> str:
    """Inspect a component type to understand its YAML schema, configuration options, and metadata.

    This tool provides detailed information about a component type's structure, including:
    - The description of the component type.
    - The jsonschema that yaml files that use this type must abide by.

    Use this tool before editing a component's defs.yaml file to understand what
    configuration options are available and how to structure the YAML correctly.

    Args:
        project_path: Absolute filesystem path to the root directory of your Dagster project
                     (the directory containing pyproject.toml with [tool.dg] or dg.toml).
        component_type: Fully qualified component type identifier to inspect (e.g.,
                       'dagster_sling.SlingReplicationCollectionComponent',
                       'dagster_dbt.DbtProjectComponent'). Use list_available_components
                       to discover available component types.

    Returns:
        Detailed inspection output including the component's YAML schema definition,
        configuration parameters with their types and constraints, and metadata about
        the component's behavior and requirements.
    """
    return _subprocess(
        [
            "dg",
            "utils",
            "inspect-component",
            component_type,
        ],
        cwd=project_path,
    )


@mcp.tool()
async def check_dagster_defs_yaml(project_path: str) -> str:
    """Validate the syntax and structure of all defs.yaml files in the project.

    This tool performs comprehensive validation of YAML syntax, schema compliance,
    and structural correctness for all component definition files in the project.
    It checks for:
    - Valid YAML syntax (proper indentation, quotes, etc.)
    - Schema compliance (required fields, correct data types)
    - Reference integrity (valid component type names)

    Run this tool after making any changes to defs.yaml files to catch syntax
    errors and configuration issues before attempting to load the definitions.

    Args:
        project_path: Absolute filesystem path to the root directory of your Dagster project
                     (the directory containing pyproject.toml with [tool.dg] or dg.toml).

    Returns:
        Validation results indicating whether all defs.yaml files are syntactically
        correct and properly structured. If errors are found, detailed error messages
        with file paths and line numbers are provided to help with debugging.
    """
    return _subprocess(
        [
            "dg",
            "check",
            "yaml",
        ],
        cwd=project_path,
    )


@mcp.tool()
async def check_dagster_definitions(project_path: str) -> str:
    """Validate that all Dagster definitions can be successfully loaded and instantiated.

    This tool performs a comprehensive validation of the entire project's definitions by
    attempting to load all components and build their definitions.

    This is a deeper validation than check_dagster_defs_yaml - while that tool only
    checks YAML syntax and schema, this tool actually loads and runs the Python code and
    verifies that all components can be instantiated with the provided configuration.

    Args:
        project_path: Absolute filesystem path to the root directory of your Dagster project
                     (the directory containing pyproject.toml with [tool.dg] or dg.toml).

    Returns:
        Validation results indicating whether all definitions can be successfully loaded.
        If loading fails, detailed error messages with component names, error types,
        and troubleshooting guidance are provided.
    """
    return _subprocess(
        [
            "dg",
            "check",
            "defs",
        ],
        cwd=project_path,
    )


@mcp.tool()
async def list_dagster_definitions(project_path: str) -> str:
    """Retrieve comprehensive metadata about all definitions in the Dagster project.

    This tool provides detailed information about all successfully loaded definitions
    in the project.

    Use this tool to get an overview of all definitions and where they were defined.

    Args:
        project_path: Absolute filesystem path to the root directory of your Dagster project
                     (the directory containing pyproject.toml with [tool.dg] or dg.toml).

    Returns:
        JSON-formatted metadata about all definitions in the project, including
        their names, types, dependencies, and configuration details. The structure
        provides a comprehensive view of the project's data pipeline architecture.
    """
    return _subprocess(
        [
            "dg",
            "list",
            "defs",
            "--json",
        ],
        cwd=project_path,
    )


@mcp.tool()
async def list_available_integrations(project_path: str) -> str:
    """Retrieve an index of all available Dagster integrations in the marketplace.

    This provides information on integrations in the marketplace that are available for
    installation. It is a helpful resource for determine which tools are available, and provides
    context for determining which integration may be relevant when scaffolding components.

    Args:
        project_path: Absolute filesystem path to the root directory of your Dagster project
                     (the directory containing pyproject.toml with [tool.dg] or dg.toml).

    Returns:
        JSON-formatted metadata about all integrations available for installation, including
        their name, description, and pypi installation url. This resource is useful for determining
        which integrations to use when scaffolding pipelines.
    """
    return _subprocess(
        [
            "dg",
            "utils",
            "integrations",
            "--json",
        ],
        cwd=project_path,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
