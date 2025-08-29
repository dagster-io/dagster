"""Client factory for DG API commands."""

from typing import Protocol

import click
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient


class GraphQLClientFactory(Protocol):
    """Protocol for GraphQL client factories used in testing."""

    def __call__(self, config: DagsterPlusCliConfig) -> DagsterPlusGraphQLClient: ...


class DgApiTestContext:
    """Test context for DG API commands."""

    def __init__(self, client_factory: GraphQLClientFactory):
        self.client_factory = client_factory


def create_dg_api_graphql_client(
    ctx: click.Context, config: DagsterPlusCliConfig
) -> DagsterPlusGraphQLClient:
    """Create GraphQL client for DG API commands.

    This is the single entry point for GraphQL client creation in DG API commands.
    It checks for test context injection and falls back to creating a real client.

    Args:
        ctx: Click context from the CLI command
        config: Optional config to use, falls back to global config if not provided

    Returns:
        DagsterPlusGraphQLClient instance
    """
    # Check if we have a test context with custom factory
    if ctx.obj and isinstance(ctx.obj, DgApiTestContext) and ctx.obj.client_factory:
        return ctx.obj.client_factory(config)

    # Normal operation: create real client from config
    return DagsterPlusGraphQLClient.from_config(config)
