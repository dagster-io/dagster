import webbrowser

import click
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.utils.plus.gql import FULL_DEPLOYMENTS_QUERY
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient


@click.command(name="login", cls=DgClickCommand)
@cli_telemetry_wrapper
def login_command() -> None:
    """Login to Dagster Plus."""
    # Import login server only when the command is actually used
    from dagster_shared.plus.login_server import start_login_server

    org_url = DagsterPlusCliConfig.get().url if DagsterPlusCliConfig.exists() else None
    server, url = start_login_server(org_url)

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
        url=org_url,
    )
    config.write()
    click.echo(f"Authorized for organization {new_org}\n")

    gql_client = DagsterPlusGraphQLClient.from_config(config)
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
        url=org_url,
    )
    config.write()
