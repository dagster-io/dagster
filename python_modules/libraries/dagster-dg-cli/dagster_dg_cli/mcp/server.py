import subprocess
from collections.abc import Sequence

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("dagster-dg-cli")


def _subprocess(command: Sequence[str], cwd: str) -> str:
    """Call to `subprocess.check_output` with exception output exposed.

    This is used to provide additional context to the `mcp.tool`.

    Args:
        command: Sequence of command arguments.
        cwd: Current working directory.

    Returns:
        Decoded command output.
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
    """List all Dagster components for the project.

    Components can be scaffolded to create new Dagster definitions. Call this when you need to add
    new Dagster definitions and want to get a list of components to use to do so.

    Args:
        project_path: The full path to your Dagster project.

    Returns:
        The list of components available for the given Dagster project.
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
    """Determine the sub-parameters required for the `component_type` scaffold command.

    Args:
        project_path: The full path to your Dagster project.
        component_type: The full identifier of the component to be scaffolded (e.g. dagster_sling.SlingReplicationCollectionComponent)

    Returns:
        The help for scaffolding a specific component_type.
    """
    return _subprocess(
        [
            "dg",
            "--verbose",
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
    """Scaffold a new Dagster component in the project.

    This produces a defs.yaml file which can be populated with the appropriate fields for the component.

    Args:
        project_path: The full path to your Dagster project.
        component_type: The full identifier of the component to be scaffolded (e.g. dagster_sling.SlingReplicationCollectionComponent)
        component_name: The name of the component to provide for the newly scaffolded component.
        component_arguments: List of arguments to be passed to the component scaffold sub-command, run the "help" tool to determine arguments.

    Returns:
        The output from running the `dg scaffold` command.
    """
    return _subprocess(
        [
            "dg",
            "--verbose",
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
    """Inspect a component type to get info on the YAML schema and other metadata.

    Call this before editing a component YAML file to ensure you understand the schema and other constraints.

    Args:
        project_path: The full path to your Dagster project.
        component_type: The type of component to be scaffolded.

    Returns:
        The output from running the command to inspect the specified component type.
    """
    return _subprocess(
        [
            "dg",
            "--verbose",
            "utils",
            "inspect-component",
            component_type,
        ],
        cwd=project_path,
    )


@mcp.tool()
async def check_dagster_defs_yaml(project_path: str) -> str:
    """Runs a check to ensure that defs.yaml files in the project are valid.

    Call this after every change to defs YAML to ensure they are syntactically correct.

    Args:
        project_path: The full path to your Dagster project.

    Returns:
        Verification that the YAML is formatted properly.
    """
    return _subprocess(
        [
            "dg",
            "--verbose",
            "check",
            "yaml",
        ],
        cwd=project_path,
    )


@mcp.tool()
async def check_dagster_definitions(project_path: str) -> str:
    """Runs a check to ensure the Dagster definitions are valid.

    Call this after every change to defs YAML to ensure they load successfully.

    Args:
        project_path: The full path to your Dagster project.

    Returns:
        Verification that the YAML is formatted properly.
    """
    return _subprocess(
        [
            "dg",
            "--verbose",
            "check",
            "defs",
        ],
        cwd=project_path,
    )


@mcp.tool()
async def list_dagster_definitions(project_path: str) -> str:
    """Retrieve metadata around the definitions in this Dagster project.

    Call this after every change to component YAML to ensure they load successfully.

    Args:
        project_path: The full path to your Dagster project.

    Returns:
        A list of definitions in this Dagster project.
    """
    return _subprocess(
        [
            "dg",
            "--verbose",
            "list",
            "defs",
            "--json",
        ],
        cwd=project_path,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
