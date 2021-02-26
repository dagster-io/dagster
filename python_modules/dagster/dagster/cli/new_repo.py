import os

import click
from dagster.generate import generate_new_repo
from dagster.utils.backcompat import experimental


@click.command(name="new-repo")
@click.argument("path", type=click.Path())
@experimental
def new_repo_command(path: str):
    """
    Creates a new Dagster repository and generates boilerplate code. ``dagster new-repo`` is an
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
    generate_new_repo(path)
    click.echo("Done.")


new_repo_cli = new_repo_command
