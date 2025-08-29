"""Client factory for DG API commands."""

from typing import Protocol

import click
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient, IGraphQLClient

# Test constants
TEST_ORGANIZATION = "test-org"
TEST_DEPLOYMENT = "test-deployment"


class GraphQLClientFactory(Protocol):
    """Protocol for GraphQL client factories used in testing."""

    def __call__(self, config: DagsterPlusCliConfig) -> IGraphQLClient: ...


class DgApiTestContext:
    """Test context for DG API commands."""

    def __init__(self, client_factory: GraphQLClientFactory):
        self.client_factory = client_factory
        self.organization = TEST_ORGANIZATION
        self.deployment = TEST_DEPLOYMENT


def create_dg_api_graphql_client(
    ctx: click.Context, config: DagsterPlusCliConfig
) -> IGraphQLClient:
    """Create GraphQL client for DG API commands.

    This is the single entry point for GraphQL client creation in DG API commands.
    It checks for test context injection and falls back to creating a real client.

    Args:
        ctx: Click context from the CLI command
        config: Config to use for creating the client

    Returns:
        IGraphQLClient instance
    """
    # Check if we have a test context with custom factory
    if ctx.obj and isinstance(ctx.obj, DgApiTestContext) and ctx.obj.client_factory:
        return ctx.obj.client_factory(config)

    # For normal operation, validate authentication before creating client
    if not config.user_token:
        raise click.UsageError(
            "A Dagster Cloud API token must be specified.\n\n"
            "You may specify a token by:\n"
            "- Providing the --api-token parameter\n"
            "- Setting the DAGSTER_CLOUD_API_TOKEN environment variable"
        )

    # Normal operation: create real client from config
    return DagsterPlusGraphQLClient.from_config(config)
