import webbrowser

import click
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.login_server import start_login_server

from dagster_dg.utils import DgClickCommand, DgClickGroup


@click.group(name="plus", cls=DgClickGroup, hidden=True)
def plus_group():
    """Commands for interacting with Dagster Plus."""


@plus_group.command(name="login", cls=DgClickCommand)
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

    config = DagsterPlusCliConfig(organization=new_org, user_token=new_api_token)
    config.write()
    click.echo(f"Authorized for organization {new_org}\n")
