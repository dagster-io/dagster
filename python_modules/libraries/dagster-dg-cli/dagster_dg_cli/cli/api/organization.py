"""Organization API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_organization_settings, format_saml_result
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


@click.command(name="upload", cls=DgClickCommand)
@click.argument("metadata_file_path", type=click.Path(exists=True))
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.saml", cls="SamlOperationResult")
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def upload_saml_metadata_command(
    ctx: click.Context,
    metadata_file_path: str,
    output_json: bool,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Upload identity provider SAML metadata to enable SSO."""
    import requests

    if not api_token:
        raise click.UsageError(
            "A Dagster Cloud API token must be specified.\n\n"
            "You may specify a token by:\n"
            "- Providing the --api-token parameter\n"
            "- Setting the DAGSTER_CLOUD_API_TOKEN environment variable"
        )

    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )

    with handle_api_errors(ctx, output_json):
        with open(metadata_file_path, "rb") as f:
            response = requests.post(
                url=f"{config.organization_url}/upload_idp_metadata",
                headers={
                    "Dagster-Cloud-Api-Token": api_token,
                    "Dagster-Cloud-Organization": organization,
                },
                files={"metadata.xml": f},
            )

        response.raise_for_status()

        if response.text != "SUCCESS":
            raise click.ClickException(
                "Upload failed; unexpected response. Verify that the correct organization is specified.\n"
                f" {response.text}"
            )

        from dagster_dg_cli.api_layer.schemas.saml import SamlOperationResult

        result = SamlOperationResult(
            message="The identity provider metadata was successfully uploaded."
        )
        click.echo(format_saml_result(result, as_json=output_json))


@click.command(name="remove", cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.saml", cls="SamlOperationResult")
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def remove_saml_metadata_command(
    ctx: click.Context,
    output_json: bool,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Remove identity provider SAML metadata to disable SSO."""
    import requests

    if not api_token:
        raise click.UsageError(
            "A Dagster Cloud API token must be specified.\n\n"
            "You may specify a token by:\n"
            "- Providing the --api-token parameter\n"
            "- Setting the DAGSTER_CLOUD_API_TOKEN environment variable"
        )

    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )

    with handle_api_errors(ctx, output_json):
        response = requests.post(
            url=f"{config.organization_url}/remove_idp_metadata",
            headers={
                "Dagster-Cloud-Api-Token": api_token,
                "Dagster-Cloud-Organization": organization,
            },
        )

        response.raise_for_status()

        from dagster_dg_cli.api_layer.schemas.saml import SamlOperationResult

        result = SamlOperationResult(
            message="The identity provider metadata was successfully removed."
        )
        click.echo(format_saml_result(result, as_json=output_json))


@click.group(
    name="saml",
    cls=DgClickGroup,
    commands={
        "upload": upload_saml_metadata_command,
        "remove": remove_saml_metadata_command,
    },
)
def saml_group():
    """Manage SAML SSO configuration."""


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
        "saml": saml_group,
    },
)
def organization_group():
    """Manage organization in Dagster Plus."""
