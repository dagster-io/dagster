"""Secret API commands following GitHub CLI patterns."""

import json

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

# Lazy import to avoid loading pydantic at CLI startup
from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_secret, format_secrets


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--location",
    help="Filter secrets by code location name",
)
@click.option(
    "--scope",
    type=click.Choice(["deployment", "organization"]),
    help="Filter secrets by scope",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_secrets_command(
    ctx: click.Context,
    location: str,
    scope: str,
    output_json: bool,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List secrets in the organization.

    By default, secret values are not shown for security reasons.
    Use 'dg api secret get NAME --show-value' to view specific values.
    """
    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.secret import DgApiSecretApi

    api = DgApiSecretApi(client)

    try:
        secrets = api.list_secrets(
            location_name=location,
            scope=scope,
        )
        output = format_secrets(secrets, as_json=output_json)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to list secrets: {e}")


@click.command(name="get", cls=DgClickCommand)
@click.argument("secret_name")
@click.option(
    "--location",
    help="Filter by code location name",
)
@click.option(
    "--show-value",
    is_flag=True,
    help="Include secret value in output (use with caution - values will be visible in terminal)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_secret_command(
    ctx: click.Context,
    secret_name: str,
    location: str,
    show_value: bool,
    output_json: bool,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get details for a specific secret.

    By default, the secret value is not shown for security reasons.
    Use --show-value flag to display the actual secret value.

    WARNING: When using --show-value, the secret will be visible in your terminal
    and may be stored in shell history. Use with caution.
    """
    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.secret import DgApiSecretApi

    api = DgApiSecretApi(client)

    try:
        secret = api.get_secret(
            secret_name=secret_name,
            location_name=location,
            include_value=show_value,
        )
        output = format_secret(secret, as_json=output_json, show_value=show_value)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to get secret '{secret_name}': {e}")


@click.group(
    name="secret",
    cls=DgClickGroup,
    commands={
        "list": list_secrets_command,
        "get": get_secret_command,
    },
)
def secret_group():
    """Manage secrets in Dagster Plus.

    Secrets are environment variables that are encrypted and securely stored
    in Dagster Plus. They can be scoped to different deployment levels and
    code locations.

    Security Note: Secret values are hidden by default. Use appropriate flags
    and caution when displaying sensitive values.
    """
