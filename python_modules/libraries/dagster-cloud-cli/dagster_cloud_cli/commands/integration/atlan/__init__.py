import sys
from typing import Annotated

import validators
from typer import Argument, Typer

from dagster_cloud_cli import gql, ui
from dagster_cloud_cli.config_utils import dagster_cloud_options

app = Typer(help="Customize your Atlan integration.")


@app.command(name="set-settings")
@dagster_cloud_options(allow_empty=True, requires_url=True)
def set_atlan_settings_command(
    atlan_token: Annotated[
        str,
        Argument(
            help="The token to use to access the Atlan API.",
        ),
    ],
    atlan_domain: Annotated[
        str,
        Argument(
            help="The domain of your Atlan tenant. Eg. your-organization.atlan.com.",
        ),
    ],
    api_token: str,
    url: str,
):
    """Upload your Atlan settings to enable the Dagster<>Atlan integration in Dagster Cloud."""
    if not validators.domain(atlan_domain):
        ui.print(
            "Invalid domain. "
            "Please provide the domain of your Altan tenant using the following format: your-organization.atlan.com."
        )
        sys.exit(1)

    try:
        with gql.graphql_client_from_url(url, api_token) as client:
            organization, _ = gql.set_atlan_integration_settings(
                client, token=atlan_token, domain=atlan_domain
            )
        ui.print(f"Atlan settings successfully set for organization: {organization}")

    except Exception as e:
        ui.print(f"Failed to set Atlan settings. Exception: {e}")
        sys.exit(1)


@app.command(name="delete-settings")
@dagster_cloud_options(allow_empty=True, requires_url=True)
def delete_atlan_settings_command(
    api_token: str,
    url: str,
):
    """Delete your Atlan settings to disable the Dagster<>Atlan integration in Dagster Cloud."""
    try:
        with gql.graphql_client_from_url(url, api_token) as client:
            organization, _ = gql.delete_atlan_integration_settings(client)
        ui.print(f"Atlan settings successfully deleted for organization: {organization}")
    except Exception as e:
        ui.print(f"Failed to delete Atlan settings. Exception: {e}")
        sys.exit(1)


@app.command(name="get-settings")
@dagster_cloud_options(allow_empty=True, requires_url=True)
def get_atlan_settings_command(
    api_token: str,
    url: str,
):
    """Get your current Atlan settings from Dagster Cloud."""
    with gql.graphql_client_from_url(url, api_token) as client:
        settings = gql.get_atlan_integration_settings(client)
        ui.print(f"Token: {settings['token']}")
        ui.print(f"Domain: {settings['domain']}")


@app.command(name="preflight-check")
@dagster_cloud_options(allow_empty=True, requires_url=True)
def preflight_check_command(
    api_token: str,
    url: str,
):
    """Run a preflight check on your Atlan integration settings."""
    with gql.graphql_client_from_url(url, api_token) as client:
        result = gql.atlan_integration_preflight_check(client)
        if result["success"]:
            ui.print("Preflight check passed successfully!")
        else:
            ui.print("Preflight check failed:")
            ui.print(f"  Error code: {result['error_code']}")
            ui.print(f"  Error message: {result['error_message']}")
