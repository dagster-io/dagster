from typer import Typer

from dagster_cloud_cli.commands.integration.atlan import app as atlan_app

app = Typer(help="Customize your integrations in Dagster Cloud.")
app.add_typer(atlan_app, name="atlan", no_args_is_help=True)
