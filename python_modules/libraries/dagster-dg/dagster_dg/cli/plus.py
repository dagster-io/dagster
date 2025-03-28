import webbrowser

import click
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.login_server import start_login_server

from dagster_dg.utils import DgClickCommand, DgClickGroup
from dagster_dg.utils.plus.gql import FULL_DEPLOYMENTS_QUERY
from dagster_dg.utils.plus.gql_client import DagsterCloudGraphQLClient
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


@click.group(name="plus", cls=DgClickGroup, hidden=True)
def plus_group():
    """Commands for interacting with Dagster Plus."""


@plus_group.command(name="login", cls=DgClickCommand)
@cli_telemetry_wrapper
def login_command() -> None:
    """Login to Dagster Plus."""
    server, url = start_login_server()

    try:
        webbrowser.open(url, new=0, autoraise=True)
        click.echo(
            f"Opening browser...\nIf a window does not open automatically, visit {url} to"
            " finish authorization"
        )
    except webbrowser.Error as e:
        click.echo(f"Error launching web browser: {e}\n\nTo finish authorization, visit {url}\n")

    server.serve_forever()
    new_org = server.get_organization()
    new_api_token = server.get_token()

    config = DagsterPlusCliConfig(
        organization=new_org,
        user_token=new_api_token,
        url=DagsterPlusCliConfig.get().url if DagsterPlusCliConfig.exists() else None,
    )
    config.write()
    click.echo(f"Authorized for organization {new_org}\n")

    gql_client = DagsterCloudGraphQLClient.from_config(config)
    result = gql_client.execute(FULL_DEPLOYMENTS_QUERY)
    deployment_names = [d["deploymentName"] for d in result["fullDeployments"]]

    click.echo("Available deployments: " + ", ".join(deployment_names))

    selected_deployment = None
    while selected_deployment not in deployment_names:
        if selected_deployment is not None:
            click.echo(f"{selected_deployment} is not a valid deployment")
        selected_deployment = click.prompt(
            "Select a default deployment", default=deployment_names[0]
        )

    config = DagsterPlusCliConfig(
        organization=config.organization,
        user_token=config.user_token,
        default_deployment=selected_deployment,
        url=config.url,
    )
    config.write()
