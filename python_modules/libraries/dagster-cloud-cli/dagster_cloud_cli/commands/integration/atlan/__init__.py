from typing import Annotated

from typer import Argument, Typer

from dagster_cloud_cli import gql
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
            help="The domain of your Atlan tenant. Eg. https://your-organization.atlan.com.",
        ),
    ],
    api_token: str,
    url: str,
):
    """Upload your Atlan settings to enable the Dagster<>Atlan integration in Dagster Cloud."""
    with gql.graphql_client_from_url(url, api_token) as client:
        gql.set_atlan_integration_settings(client, token=atlan_token, domain=atlan_domain)


@app.command(name="delete-settings")
@dagster_cloud_options(allow_empty=True, requires_url=True)
def delete_atlan_settings_command(
    api_token: str,
    organization: str,
    url: str,
):
    """Delete your Atlan settings to enable the Dagster<>Atlan integration in Dagster Cloud."""
    if not url and not organization:
        raise ui.error("Must provide either organization name or URL.")

    if not url:
        url = gql.url_from_config(organization=organization)

    with gql.graphql_client_from_url(url, api_token) as client:
        gql.delete_atlan_integration_settings(client)
