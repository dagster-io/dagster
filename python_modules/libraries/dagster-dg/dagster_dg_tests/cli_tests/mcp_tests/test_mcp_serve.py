from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()


import pytest
from dagster_dg.utils import ensure_dagster_dg_tests_import
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_is_valid_mcp_server():
    server_params = StdioServerParameters(command="dg", args=["mcp", "serve"], env=None)

    async with stdio_client(server_params) as stdio_transport:
        stdio, write = stdio_transport
        async with ClientSession(stdio, write) as session:
            await session.initialize()

            response = await session.list_tools()
            tools = response.tools
            assert "scaffold_dagster_component" in [tool.name for tool in tools]
