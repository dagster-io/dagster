from mcp.server.fastmcp import FastMCP

mcp = FastMCP("dagster-dg")
import subprocess


@mcp.tool()
async def list_dagster_plugins(project_path: str) -> str:
    """List all Dagster plugins for the project."""
    return subprocess.check_output(
        ["uv", "run", "dg", "list", "plugins"],
        cwd=project_path,
    ).decode("utf-8")


@mcp.tool()
async def list_dagster_components(project_path: str) -> str:
    """List all Dagster components for the project. Components
    can be scaffolded to create new Dagster definitions. Call this
    when you need to add new Dagster definitions and want to get a list
    of components to use to do so.
    """
    return subprocess.check_output(
        ["uv", "run", "dg", "list", "plugins", "--feature", "component"],
        cwd=project_path,
    ).decode("utf-8")


@mcp.tool()
async def scaffold_dagster_component(
    project_path: str, component_type: str, component_name: str
) -> str:
    """Scaffold a new Dagster component in the project. This produces
    a component.yaml file which can be populated with the appropriate
    fields for the component.
    """
    return subprocess.check_output(
        ["uv", "run", "dg", "scaffold", component_type, component_name],
        cwd=project_path,
    ).decode("utf-8")


@mcp.tool()
async def inspect_component_type(project_path: str, component_type: str) -> str:
    """Inspect a component type to get info on the YAML schema and other metadata.
    Call this before editing a component YAML file to ensure you understand the
    schema and other constraints.
    """
    return subprocess.check_output(
        ["uv", "run", "dg", "utils", "inspect-component-type", component_type],
        cwd=project_path,
    ).decode("utf-8")


@mcp.tool()
async def check_dagster_component_yaml(project_path: str) -> str:
    """Runs a check to ensure that component.yaml files in the project are valid.
    Call this after every change to component YAML to ensure they are
    syntactically correct.
    """
    return subprocess.check_output(
        ["uv", "run", "dg", "check", "yaml"],
        cwd=project_path,
    ).decode("utf-8")


if __name__ == "__main__":
    mcp.run(transport="stdio")
