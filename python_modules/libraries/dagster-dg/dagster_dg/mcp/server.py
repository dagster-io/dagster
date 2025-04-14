from mcp.server.fastmcp import FastMCP

mcp = FastMCP("dagster-dg")
import subprocess


@mcp.tool()
async def scaffold_dagster_project(project_path: str, project_name: str) -> str:
    """Create a new Dagster project at the location of `project_path` and the name `project_name`.

    Args:
        project_path: The path to your Dagster project.

    Returns:
        The output of the project scaffold command.
    """
    return subprocess.check_output(
        ["uv", "run", "dg", "scaffold", "project", project_path], stderr=subprocess.STDOUT
    ).decode("utf-8")


@mcp.tool()
async def list_dagster_components(project_path: str) -> str:
    """List all Dagster components for the project.
    Components can be scaffolded to create new Dagster definitions. Call this
    when you need to add new Dagster definitions and want to get a list
    of components to use to do so.

    Args:
        project_path: The path to your Dagster project.

    Returns:
        The list of components available for the given Dagster project.
    """
    return subprocess.check_output(
        [
            "uv",
            "run",
            "dg",
            "list",
            "plugins",
            "--feature",
            "component",
        ],
        cwd=project_path,
        stderr=subprocess.STDOUT,
    ).decode("utf-8")


@mcp.tool()
async def install_component(project_path: str, package_name: str) -> str:
    """Install a component from the marketplace.
    Currently available components include:
        - `dagster-dbt`
        - `dagster-sling`
    Args:
        project_path: The path to your Dagster project.
        package_name: The Python package available on pypi for the component.

    Returns:
        The output of the `uv add` command
    """
    # TODO - get list of available components from the registry
    return subprocess.check_output(
        ["uv", "add", package_name],
        cwd=project_path,
        stderr=subprocess.STDOUT,
    ).decode("utf-8")


@mcp.tool()
async def scaffold_dagster_component(
    project_path: str, component_type: str, component_name: str
) -> str:
    """Scaffold a new Dagster component in the project.
    This produces a component.yaml file which can be populated with the appropriate fields for the component.

    Args:
        project_path: The path to your Dagster project.
        component_type: The type of component to be scaffolded.
        component_name: The name of the component to provide for the newly scaffolded component.

    Returns:
        The output from running the `dg scaffold` command.
    """
    return subprocess.check_output(
        ["uv", "run", "dg", "scaffold", component_type, component_name],
        cwd=project_path,
        stderr=subprocess.STDOUT,
    ).decode("utf-8")


@mcp.tool()
async def inspect_component_type(project_path: str, component_type: str) -> str:
    """Inspect a component type to get info on the YAML schema and other metadata.
    Call this before editing a component YAML file to ensure you understand the schema and other constraints.

    Args:
        project_path: The path to your Dagster project.
        component_type: The type of component to be scaffolded.

    Returns:
        The output from running the command to inspect the specified component type.
    """
    return subprocess.check_output(
        ["uv", "run", "dg", "utils", "inspect-component-type", component_type],
        cwd=project_path,
        stderr=subprocess.STDOUT,
    ).decode("utf-8")


@mcp.tool()
async def check_dagster_component_yaml(project_path: str) -> str:
    """Runs a check to ensure that component.yaml files in the project are valid.
    Call this after every change to component YAML to ensure they are syntactically correct.

    Args:
        project_path: The path to your Dagster project.

    Returns:
        Verification that the YAML is formatted properly.
    """
    return subprocess.check_output(
        ["uv", "run", "dg", "check", "yaml"],
        cwd=project_path,
        stderr=subprocess.STDOUT,
    ).decode("utf-8")


if __name__ == "__main__":
    mcp.run(transport="stdio")
