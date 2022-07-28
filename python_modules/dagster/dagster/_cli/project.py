from genericpath import isdir
import os

import click

from dagster._annotations import experimental
from dagster._generate import generate_project, generate_new_project
from dagster._utils import file_relative_path


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

    TODO
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


@project_cli.command(
    name="from-example",
    help=("Create a new Dagster project using one of the official Dagster examples."),
)
@click.option(  # should this be an argument instead? `dagster project my_app` vs `dagster project --name my_app`
    "--example",
    required=True,
    type=click.STRING,
    help="Name of the example to bootstrap with",
)
@experimental
def from_example_command(example: str):
    # TODO
    pass


@project_cli.command(
    name="scaffold-deployment",
    help="Scaffold files needed for deployment",
)
@experimental
def scaffold_deployment_command(path: str):
    return


@project_cli.command(
    name="scaffold-repository",
    help="Scaffold a new Dagster repository in an existing Dagster project",
)
@experimental
def scaffold_repository_command(path: str):
    return
