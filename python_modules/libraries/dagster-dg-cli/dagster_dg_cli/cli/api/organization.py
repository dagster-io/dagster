"""Organization API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_organization_settings
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema


@click.command(name="get", cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(
    module="dagster_dg_cli.api_layer.schemas.organization", cls="OrganizationSettings"
)
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_settings_command(
    ctx: click.Context,
    output_json: bool,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get settings for the organization."""
    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.organization import DgApiOrganizationApi

    api = DgApiOrganizationApi(client)

    with handle_api_errors(ctx, output_json):
        settings = api.get_organization_settings()
        output = format_organization_settings(settings, as_json=output_json)
        click.echo(output)


@click.command(name="set", cls=DgClickCommand)
@click.argument("file_path", required=True, type=click.Path(exists=True))
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(
    module="dagster_dg_cli.api_layer.schemas.organization", cls="OrganizationSettings"
)
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def set_settings_command(
    ctx: click.Context,
    file_path: str,
    output_json: bool,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Set organization settings from a YAML file."""
    import yaml

    with open(file_path) as f:
        settings_dict = yaml.safe_load(f)

    if not isinstance(settings_dict, dict):
        raise click.ClickException(
            f"Expected a YAML mapping in {file_path}, got {type(settings_dict).__name__}"
        )

    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.organization import DgApiOrganizationApi

    api = DgApiOrganizationApi(client)

    with handle_api_errors(ctx, output_json):
        from dagster_dg_cli.api_layer.schemas.organization import OrganizationSettings

        settings = api.update_organization_settings(OrganizationSettings(settings=settings_dict))
        output = format_organization_settings(settings, as_json=output_json)
        click.echo(output)


@click.group(
    name="settings",
    cls=DgClickGroup,
    commands={
        "get": get_settings_command,
        "set": set_settings_command,
    },
)
def settings_group():
    """Manage organization settings."""


@click.group(
    name="organization",
    cls=DgClickGroup,
    commands={
        "settings": settings_group,
    },
)
def organization_group():
    """Manage organization in Dagster Plus."""
