import click
from dagster_dg_cli.cli import create_dg_cli


@click.command("noop")
def noop_command():
    pass


cli = create_dg_cli()

cli.add_command(noop_command)
cli()
