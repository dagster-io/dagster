from textwrap import dedent

from mcp.server.fastmcp import FastMCP

from dagster_dg.cli.check import check_yaml_command
from dagster_dg.cli.list import list_plugins_command
from dagster_dg.cli.utils import inspect_component_type_command
from dagster_dg.mcp.utils import cli_command_to_mcp_tool

mcp = FastMCP("dagster-dg")
import subprocess

cli_command_to_mcp_tool(
    mcp, "list_dagster_plugins", list_plugins_command, ignore_params={"name_only"}
)

cli_command_to_mcp_tool(
    mcp,
    "list_dagster_components",
    list_plugins_command,
    fixed_params={"feature": "component"},
    replace_doc=dedent("""\
        List all Dagster components for the project. Components
        can be scaffolded to create new Dagster definitions. Call this
        when you need to add new Dagster definitions and want to get a list
        of components to use to do so.
    """),
    ignore_params={"name_only"},
)


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


cli_command_to_mcp_tool(
    mcp,
    "inspect_component_type",
    inspect_component_type_command,
    replace_doc=dedent("""\
        Inspect a component type to get info on the YAML schema and other metadata.
        Call this before editing a component YAML file to ensure you understand the
        schema and other constraints.
    """),
    ignore_params={"description", "scaffold_params_schema", "component_schema"},
)


cli_command_to_mcp_tool(
    mcp,
    "check_dagster_component_yaml",
    check_yaml_command,
    replace_doc=dedent("""\
        Runs a check to ensure that component.yaml files in the project are valid.
        Call this after every change to component YAML to ensure they are
        syntactically correct.
    """),
    ignore_params={"watch"},
)

if __name__ == "__main__":
    mcp.run(transport="stdio")
