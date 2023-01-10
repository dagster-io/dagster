import os
import sys
from typing import Sequence

import click

from dagster._generate import (
    download_example_from_github,
    generate_code_location,
    generate_project,
    generate_repository,
)
from dagster._generate.download import AVAILABLE_EXAMPLES


@click.group(name="project")
def project_cli():
    """
    Commands for bootstrapping new Dagster projects and code locations.
    """


scaffold_repository_command_help_text = (
    "(DEPRECATED; Use `dagster project scaffold-code-location` instead) "
    "Create a folder structure with a single Dagster repository, in the current directory. "
    "This CLI helps you to scaffold a new Dagster repository within a folder structure that "
    "includes multiple Dagster repositories"
)

scaffold_code_location_command_help_text = (
    "Create a folder structure with a single Dagster code location, in the current directory. "
    "This CLI helps you to scaffold a new Dagster code location within a folder structure that "
    "includes multiple Dagster code locations."
)

scaffold_command_help_text = (
    "Create a folder structure with a single Dagster code location and other files such as "
    "pyproject.toml. This CLI enables you to quickly start building a new Dagster project with "
    "everything set up."
)

from_example_command_help_text = (
    "Download one of the official Dagster examples to the current directory. "
    "This CLI enables you to quickly bootstrap your project with an officially maintained example."
)

list_examples_command_help_text = "List the examples that available to bootstrap with."


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
def scaffold_repository_command(name: str):
    dir_abspath = os.path.abspath(name)
    if os.path.isdir(dir_abspath) and os.path.exists(dir_abspath):
        click.echo(
            click.style(f"The directory {dir_abspath} already exists. ", fg="red")
            + "\nPlease delete the contents of this path or choose another location."
        )
        sys.exit(1)

    click.echo(
        click.style(
            (
                "WARNING: This command is deprecated. Use `dagster project scaffold-code-location`"
                " instead."
            ),
            fg="yellow",
        )
    )
    generate_repository(dir_abspath)
    click.echo(_styled_success_statement(name, dir_abspath))


@project_cli.command(
    name="scaffold-code-location",
    short_help=scaffold_code_location_command_help_text,
    help=scaffold_code_location_command_help_text,
)
@click.option(
    "--name",
    required=True,
    type=click.STRING,
    help="Name of the new Dagster code location",
)
def scaffold_code_location_command(name: str):
    dir_abspath = os.path.abspath(name)
    if os.path.isdir(dir_abspath) and os.path.exists(dir_abspath):
        click.echo(
            click.style(f"The directory {dir_abspath} already exists. ", fg="red")
            + "\nPlease delete the contents of this path or choose another location."
        )
        sys.exit(1)

    generate_code_location(dir_abspath)
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
    short_help=from_example_command_help_text,
    help=from_example_command_help_text,
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
        "examples in Dagster repo: https://github.com/dagster-io/dagster/tree/master/examples. "
        "You can also find the available examples via `dagster project list-examples`."
    ),
)
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


@project_cli.command(
    name="list-examples",
    short_help=list_examples_command_help_text,
    help=list_examples_command_help_text,
)
def from_example_list_command():
    click.echo("Examples available in `dagster project from-example`:")

    click.echo(_styled_list_examples_prints(AVAILABLE_EXAMPLES))


def _styled_list_examples_prints(examples: Sequence[str]) -> str:
    return "\n".join([f"* {name}" for name in examples])


def _styled_success_statement(name: str, path: str):
    return (
        click.style("Success!", fg="green")
        + " Created "
        + click.style(name, fg="blue")
        + " at "
        + click.style(path, fg="blue")
        + "."
    )
