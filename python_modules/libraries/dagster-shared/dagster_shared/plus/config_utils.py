import functools
import os
from typing import Optional

import click

from dagster_shared.plus.config import DagsterPlusCliConfig

# Constants for CLI arguments and environment variables
DEPLOYMENT_CLI_ARGUMENT = "deployment"
DEPLOYMENT_ENV_VAR_NAME = "DAGSTER_CLOUD_DEPLOYMENT"

ORGANIZATION_CLI_ARGUMENT = "organization"
ORGANIZATION_ENV_VAR_NAME = "DAGSTER_CLOUD_ORGANIZATION"

TOKEN_CLI_ARGUMENT = "api_token"
TOKEN_ENV_VAR_NAME = "DAGSTER_CLOUD_API_TOKEN"


def get_deployment(ctx: Optional[click.Context] = None) -> Optional[str]:
    """Gets the configured deployment to target.
    Highest precedence is a deployment argument, then `DAGSTER_CLOUD_DEPLOYMENT` env var, then config file default.
    """
    if ctx and ctx.params.get(DEPLOYMENT_CLI_ARGUMENT):
        return ctx.params[DEPLOYMENT_CLI_ARGUMENT]

    env_value = os.getenv(DEPLOYMENT_ENV_VAR_NAME)
    if env_value:
        return env_value

    # Fall back to config file
    if DagsterPlusCliConfig.exists():
        try:
            config = DagsterPlusCliConfig.get()
            return config.default_deployment
        except Exception:
            pass

    return None


def get_organization(ctx: Optional[click.Context] = None) -> Optional[str]:
    """Gets the configured organization to target.
    Highest precedence is an organization argument, then `DAGSTER_CLOUD_ORGANIZATION` env var, then config file.
    """
    if ctx and ctx.params.get(ORGANIZATION_CLI_ARGUMENT):
        return ctx.params[ORGANIZATION_CLI_ARGUMENT]

    env_value = os.getenv(ORGANIZATION_ENV_VAR_NAME)
    if env_value:
        return env_value

    # Fall back to config file
    if DagsterPlusCliConfig.exists():
        try:
            config = DagsterPlusCliConfig.get()
            return config.organization
        except Exception:
            pass

    return None


def get_user_token(ctx: Optional[click.Context] = None) -> Optional[str]:
    """Gets the configured user token to use.
    Highest precedence is an api-token argument, then `DAGSTER_CLOUD_API_TOKEN` env var, then config file.
    """
    if ctx and ctx.params.get(TOKEN_CLI_ARGUMENT):
        return ctx.params[TOKEN_CLI_ARGUMENT]

    env_value = os.getenv(TOKEN_ENV_VAR_NAME)
    if env_value:
        return env_value

    # Fall back to config file
    if DagsterPlusCliConfig.exists():
        try:
            config = DagsterPlusCliConfig.get()
            return config.user_token
        except Exception:
            pass

    return None


# Click option definitions for reuse across commands
DEPLOYMENT_OPTION = click.option(
    "--deployment",
    "-d",
    help="Deployment to target.",
    envvar=DEPLOYMENT_ENV_VAR_NAME,
)

ORGANIZATION_OPTION = click.option(
    "--organization",
    "-o",
    help="Organization to target.",
    envvar=ORGANIZATION_ENV_VAR_NAME,
)

TOKEN_OPTION = click.option(
    "--api-token",
    help="Dagster Cloud API token.",
    envvar=TOKEN_ENV_VAR_NAME,
)

VIEW_GRAPHQL_OPTION = click.option(
    "--view-graphql",
    is_flag=True,
    help="Print GraphQL queries and responses to stderr for debugging.",
)


def dg_api_options(
    deployment_scoped: bool = False,
    organization_scoped: bool = False,
):
    """Apply this decorator to Click commands to add organization, deployment, and token options.

    Args:
        deployment_scoped: If True, requires deployment to be specified and validates it
        organization_scoped: If True, only requires organization (deployment is optional)
    """
    if deployment_scoped and organization_scoped:
        raise ValueError("Cannot specify both deployment_scoped and organization_scoped")

    if not deployment_scoped and not organization_scoped:
        raise ValueError("Must specify either deployment_scoped or organization_scoped")

    def decorator(func):
        # Add options in reverse order (Click applies them in reverse)
        func = VIEW_GRAPHQL_OPTION(func)
        func = TOKEN_OPTION(func)
        func = ORGANIZATION_OPTION(func)

        if deployment_scoped:
            func = DEPLOYMENT_OPTION(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ctx = click.get_current_context()

            # Check if we're in test mode with DgApiTestContext
            # Import here to avoid circular imports
            from dagster_dg_cli.cli.api.client import DgApiTestContext

            if ctx.obj and isinstance(ctx.obj, DgApiTestContext):
                organization = ctx.obj.organization
                deployment = ctx.obj.deployment if deployment_scoped else None
                api_token = None
                view_graphql = False  # Default to False in test mode
            else:
                # Get resolved values using precedence chain
                organization = get_organization(ctx)
                deployment = get_deployment(ctx) if deployment_scoped else None
                api_token = get_user_token(ctx)
                view_graphql = kwargs.get("view_graphql", False)

            if not organization:
                raise click.UsageError(
                    "A Dagster Cloud organization must be specified.\n\n"
                    "You may specify an organization by:\n"
                    f"- Providing the --organization parameter\n"
                    f"- Setting the {ORGANIZATION_ENV_VAR_NAME} environment variable"
                )

            if deployment_scoped and not deployment:
                raise click.UsageError(
                    "A Dagster Cloud deployment must be specified for this command.\n\n"
                    "You may specify a deployment by:\n"
                    f"- Providing the --deployment parameter\n"
                    f"- Setting the {DEPLOYMENT_ENV_VAR_NAME} environment variable"
                )

            # Update kwargs with resolved values
            kwargs["organization"] = organization
            kwargs["api_token"] = api_token
            kwargs["view_graphql"] = view_graphql
            if deployment_scoped:
                kwargs["deployment"] = deployment

            return func(*args, **kwargs)

        return wrapper

    return decorator
