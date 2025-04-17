from pathlib import Path
from typing import TYPE_CHECKING, cast

from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()


import pytest
from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from contextlib import asynccontextmanager

from dagster_dg.utils import ensure_dagster_dg_tests_import
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from dagster_dg_tests.utils import ProxyRunner, isolated_example_project_foo_bar

if TYPE_CHECKING:
    from mcp.types import TextContent


@asynccontextmanager
async def mcp_server():
    server_params = StdioServerParameters(command="dg", args=["mcp", "serve"], env=None)

    async with stdio_client(server_params) as stdio_transport:
        stdio, write = stdio_transport
        async with ClientSession(stdio, write) as session:
            await session.initialize()
            yield session


@pytest.mark.asyncio
async def test_is_valid_mcp_server():
    async with mcp_server() as session:
        response = await session.list_tools()
        tools = response.tools
        assert "scaffold_dagster_component" in [tool.name for tool in tools]


# TODO: I would like to write a testing abstraction that lets us consolidate the mcp tests with the CLI tests,
# since the inputs are nearly identical in each case. For now, we just have basic coverage w/ duplicate tests.
@pytest.mark.asyncio
async def test_list_dagster_plugins():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        async with mcp_server() as session:
            response = await session.call_tool("list_dagster_plugins", {"project_path": "."})
            assert not response.isError
            assert len(response.content) == 1
            text_content = cast("TextContent", response.content[0])
            assert "dagster.schedule" in text_content.text


@pytest.mark.asyncio
async def test_list_dagster_components():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        async with mcp_server() as session:
            response = await session.call_tool("list_dagster_components", {"project_path": "."})
            assert not response.isError
            assert len(response.content) == 1
            text_content = cast("TextContent", response.content[0])
            assert "dagster.components.DefinitionsComponent" in text_content.text
            assert "dagster.schedule" not in text_content.text


@pytest.mark.asyncio
async def test_scaffold_dagster_component_and_check_yaml():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        async with mcp_server() as session:
            response = await session.call_tool(
                "scaffold_dagster_component",
                {
                    "project_path": ".",
                    "component_type": "dagster.components.DefinitionsComponent",
                    "component_name": "my_defs",
                },
            )
            assert not response.isError

            assert (
                Path.cwd() / "src" / "foo_bar/" / "defs" / "my_defs" / "component.yaml"
            ).exists()

            response = await session.call_tool(
                "check_dagster_component_yaml",
                {
                    "project_path": ".",
                },
            )
            assert response.isError

            assert (
                Path.cwd() / "src" / "foo_bar/" / "defs" / "my_defs" / "component.yaml"
            ).write_text(
                "type: dagster.components.DefinitionsComponent\n\nattributes:\n  path: test.py"
            )

            response = await session.call_tool(
                "check_dagster_component_yaml",
                {
                    "project_path": ".",
                },
            )
            assert not response.isError, response.content
