"""Client factory for DG API commands."""

import click
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient, IGraphQLClient


def create_dg_api_graphql_client(
    ctx: click.Context, config: DagsterPlusCliConfig
) -> IGraphQLClient:
    """Create GraphQL client for DG API commands.

    This is the single entry point for GraphQL client creation in DG API commands.
    It checks for test context injection first, then handles authentication for normal usage.

    Args:
        ctx: Click context from the CLI command
        config: Config to use for creating the client

    Returns:
        IGraphQLClient instance
    """
    from dagster_dg_cli.cli.api.shared import DgApiTestContext

    # Check if we have a test context with custom factory
    if ctx.obj and isinstance(ctx.obj, DgApiTestContext) and ctx.obj.client_factory:
        return ctx.obj.client_factory(config)

    # For normal operation, validate token exists and create client
    if not config.user_token:
        raise click.UsageError(
            "A Dagster Cloud API token must be specified.\n\n"
            "You may specify a token by:\n"
            "- Providing the --api-token parameter\n"
            "- Setting the DAGSTER_CLOUD_API_TOKEN environment variable"
        )

    # Normal operation: create real client from config
    return DagsterPlusGraphQLClient.from_config(config)


def create_dg_api_client(ctx: click.Context) -> IGraphQLClient:
    """Create GraphQL client for DG API commands with automatic config handling.

    This is a convenience function for deployment commands that handles both
    config creation and client creation in a single step.

    Args:
        ctx: Click context from the CLI command

    Returns:
        IGraphQLClient instance
    """
    from dagster_dg_cli.cli.api.shared import get_config_for_api_command

    config = get_config_for_api_command(ctx)
    return create_dg_api_graphql_client(ctx, config)
