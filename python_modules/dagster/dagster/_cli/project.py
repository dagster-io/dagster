import os
import sys
from typing import NamedTuple, Optional, Sequence

import click
import requests

from dagster._generate import (
    download_example_from_github,
    generate_code_location,
    generate_project,
    generate_repository,
)
from dagster._generate.download import AVAILABLE_EXAMPLES
from dagster.version import __version__ as dagster_version


@click.group(name="project")
def project_cli():
    """Commands for bootstrapping new Dagster projects and code locations."""


# Keywords to flag in package names. When a project name contains one of these keywords, we check
# if a conflicting PyPI package exists.
FLAGGED_PACKAGE_KEYWORDS = ["dagster", "dbt"]

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


class PackageConflictCheckResult(NamedTuple):
    request_error_msg: Optional[str]
    conflict_exists: bool = False


def check_if_pypi_package_conflict_exists(project_name: str) -> PackageConflictCheckResult:
    """Checks if the project name contains any flagged keywords. If so, raises a warning if a PyPI
    package with the same name exists. This is to prevent import errors from occurring due to a
    project name that conflicts with an imported package.

    Raises an error regardless of hyphen or underscore (i.e. dagster_dbt vs dagster-dbt). Both
    are invalid and cause import errors.
    """
    if any(keyword in project_name for keyword in FLAGGED_PACKAGE_KEYWORDS):
        try:
            res = requests.get(f"https://pypi.org/pypi/{project_name}")
            if res.status_code == 200:
                return PackageConflictCheckResult(request_error_msg=None, conflict_exists=True)
        except Exception as e:
            return PackageConflictCheckResult(request_error_msg=str(e))

    return PackageConflictCheckResult(request_error_msg=None, conflict_exists=False)


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
            "WARNING: This command is deprecated. Use `dagster project scaffold-code-location`"
            " instead.",
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


def _check_and_error_on_package_conflicts(project_name: str) -> None:
    package_check_result = check_if_pypi_package_conflict_exists(project_name)
    if package_check_result.request_error_msg:
        click.echo(
            click.style(
                "An error occurred while checking for package conflicts:"
                f" {package_check_result.request_error_msg}. \n\nConflicting package names will"
                " cause import errors in your project if the existing PyPI package is included"
                " as a dependency in your scaffolded project. If desired, this check can be"
                " skipped by adding the `--ignore-package-conflict` flag.",
                fg="red",
            )
        )
        sys.exit(1)

    if package_check_result.conflict_exists:
        click.echo(
            click.style(
                f"The project '{project_name}' conflicts with an existing PyPI package."
                " Conflicting package names will cause import errors in your project if the"
                " existing PyPI package is included as a dependency in your scaffolded"
                " project. Please choose another name, or add the `--ignore-package-conflict`"
                " flag to bypass this check.",
                fg="yellow",
            )
        )
        sys.exit(1)


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
@click.option(
    "--ignore-package-conflict",
    is_flag=True,
    default=False,
    help="Controls whether the project name can conflict with an existing PyPI package.",
)
def scaffold_command(name: str, ignore_package_conflict: bool):
    dir_abspath = os.path.abspath(name)
    if os.path.isdir(dir_abspath) and os.path.exists(dir_abspath):
        click.echo(
            click.style(f"The directory {dir_abspath} already exists. ", fg="red")
            + "\nPlease delete the contents of this path or choose another location."
        )
        sys.exit(1)

    if not ignore_package_conflict:
        _check_and_error_on_package_conflicts(name)

    generate_project(dir_abspath)
    click.echo(_styled_success_statement(name, dir_abspath))


@project_cli.command(
    name="from-example",
    short_help=from_example_command_help_text,
    help=from_example_command_help_text,
)
@click.option(
    "--name",
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
@click.option(
    "--version",
    type=click.STRING,
    help="Which version of the example to download, defaults to same version as installed dagster.",
    default=dagster_version,
    show_default=True,
)
def from_example_command(name: Optional[str], example: str, version: str):
    name = name or example
    dir_abspath = os.path.abspath(name) + "/"
    if os.path.isdir(dir_abspath) and os.path.exists(dir_abspath):
        click.echo(
            click.style(f"The directory {dir_abspath} already exists. ", fg="red")
            + "\nPlease delete the contents of this path or choose another location."
        )
        sys.exit(1)
    else:
        os.mkdir(dir_abspath)

    download_example_from_github(dir_abspath, example, version)

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
