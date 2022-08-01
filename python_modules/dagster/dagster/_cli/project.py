import os
import sys

import click

from dagster._annotations import experimental
from dagster._generate import download_example_from_github, generate_project, generate_repository


@click.group(name="project")
def project_cli():
    """
    Commands for bootstrapping new Dagster projects and repositories.
    """


scaffold_repository_command_help_text = (
    "Create a folder structure with a single Dagster repository, in the current directory. "
    "This CLI helps you to scaffold a new Dagster repository within a folder structure that "
    "includes multiple Dagster repositories"
)

scaffold_command_help_text = (
    "Create a folder structure with a single Dagster repository and other files such as "
    "workspace.yaml, in the current directory. This CLI enables you to quickly start building "
    "a new Dagster project with everything set up."
)


@project_cli.command(
    name="scaffold-repository",
    short_help=scaffold_repository_command_help_text,
    help=scaffold_repository_command_help_text,
)
@click.option(
    "--name",
    required=True,
    type=click.STRING,
    help="Name of the new Dagster repository",
)
@experimental
def scaffold_repository_command(name: str):
    dir_abspath = os.path.abspath(name)
    if os.path.isdir(dir_abspath) and os.path.exists(dir_abspath):
        click.echo(
            click.style(f"The directory {dir_abspath} already exists. ", fg="red")
            + "\nPlease delete the contents of this path or choose another location."
        )
        sys.exit(1)

    generate_repository(dir_abspath)
    click.echo(_styled_success_statement(name, dir_abspath))


@project_cli.command(
    name="scaffold",
    short_help=scaffold_command_help_text,
    help=scaffold_command_help_text,
)
@click.option(
    "--name",
    required=True,
    type=click.STRING,
    help="Name of the new Dagster project",
)
@experimental
def scaffold_command(name: str):
    dir_abspath = os.path.abspath(name)
    if os.path.isdir(dir_abspath) and os.path.exists(dir_abspath):
        click.echo(
            click.style(f"The directory {dir_abspath} already exists. ", fg="red")
            + "\nPlease delete the contents of this path or choose another location."
        )
        sys.exit(1)

    generate_project(dir_abspath)
    click.echo(_styled_success_statement(name, dir_abspath))


@project_cli.command(
    name="from-example",
    help="Create a new Dagster project using one of the official Dagster examples.",
)
@click.option(
    "--name",
    required=True,
    type=click.STRING,
    help="Name of the new Dagster project",
)
@click.option(
    "--example",
    required=True,
    type=click.STRING,
    help=(
        "Name of the example to bootstrap with. You can use an example name from the official "
        "examples in Dagster repo: https://github.com/dagster-io/dagster/tree/master/examples"
    ),
)
@experimental
def from_example_command(name: str, example: str):
    dir_abspath = os.path.abspath(name)
    if os.path.isdir(dir_abspath) and os.path.exists(dir_abspath):
        click.echo(
            click.style(f"The directory {dir_abspath} already exists. ", fg="red")
            + "\nPlease delete the contents of this path or choose another location."
        )
        sys.exit(1)

    download_example_from_github(dir_abspath, example)

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
