import os

import click
from dagster.generate import generate_new_project
from dagster.utils.backcompat import experimental


@click.command(name="new-project")
@click.argument("path", type=click.Path())
@experimental
def new_project_command(path: str):
    """
    Creates a new Dagster repository and generates boilerplate code. ``dagster new-project`` is an
    experimental command and it may generate different files in future versions, even between dot
    releases.

    PATH: Location of the new Dagster repository in your filesystem.
    """
    if os.path.exists(path):
        raise FileExistsError(
            f"""
            The path {path} already exists. Please delete the contents of this path or choose
            another repository location.
            """
        )

    click.echo(f"Creating a new Dagster repository in {path}...")
    generate_new_project(path)
    click.echo("Done.")


new_project_cli = new_project_command
