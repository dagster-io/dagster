import os

import click

from dagster._annotations import experimental
from dagster._generate import generate_project, generate_repository


@click.group(name="project")
def project_cli():
    """
    Commands for scaffolding new Dagster projects.
    """


@project_cli.command(
    name="scaffold-repository",
    help="Create a new Dagster repository using the default template",
)
@click.option(
    "--name",
    required=True,
    type=click.STRING,
    help="Name of the new Dagster repository",
)
@experimental
def scaffold_repository_command(name: str):
    """
    Create a new Dagster project using the default template.
    """
    dir_abspath = os.path.abspath(name)
    if os.path.isdir(dir_abspath) and os.path.exists(dir_abspath):
        raise FileExistsError(
            f"""
            The directory {dir_abspath} already exists. Please delete the contents of this path
            or choose another repository location.
            """
        )

    generate_repository(name)
    click.echo(_styled_success_statement(name, dir_abspath))


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
    dir_abspath = os.path.abspath(name)
    if os.path.isdir(dir_abspath) and os.path.exists(dir_abspath):
        raise FileExistsError(
            f"""
            The directory {dir_abspath} already exists. Please delete the contents of this path
            or choose another project location.
            """
        )

    generate_project(name)
    click.echo(_styled_success_statement(name, dir_abspath))


def _styled_success_statement(name: str, path: str):
    return (
        click.style("Success!", fg="green")
        + " Created "
        + click.style(name, fg="blue")
        + " at "
        + click.style(path, fg="blue")
        + "."
    )
