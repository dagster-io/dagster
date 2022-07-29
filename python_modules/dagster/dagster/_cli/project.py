import os

import click

from dagster._annotations import experimental
from dagster._generate import generate_project


@click.group(name="project")
def project_cli():
    """
    Commands for scaffolding new Dagster projects.
    """


@project_cli.command(
    name="scaffold",
    help="Create a new Dagster project using the default template",
)
@click.option(
    "--name",
    required=True,
    type=click.STRING,
    help="Name of the new Dagster project",
)
@experimental
def scaffold_command(name: str):
    """
    Create a new Dagster project using the default template.
    """
    project_dir_abspath = os.path.abspath(name)
    if os.path.isdir(project_dir_abspath) and os.path.exists(project_dir_abspath):
        raise FileExistsError(
            f"""
            The directory {project_dir_abspath} already exists. Please delete the contents of this path
            or choose another project location.
            """
        )

    click.echo(f"Creating a new Dagster repository at {project_dir_abspath}...")
    generate_project(name)
    click.echo("Done.")
