import os
from pathlib import Path
from typing import Optional

import click
from dagster_shared.scaffold import scaffold_subtree

from dagster.version import __version__ as dagster_version

PROJECT_NAME_PLACEHOLDER = "PROJECT_NAME_PLACEHOLDER"


def generate_repository(path: str):
    REPO_NAME_PLACEHOLDER = "REPO_NAME_PLACEHOLDER"

    click.echo(f"Creating a Dagster repository at {path}.")

    #
    generate_project(
        path=path,
        excludes=None,
        name_placeholder=REPO_NAME_PLACEHOLDER,
        templates_path=os.path.join(os.path.dirname(__file__), "templates", REPO_NAME_PLACEHOLDER),
    )

    click.echo(f"Generated files for Dagster repository in {path}.")


def generate_project(
    path: str,
    excludes: Optional[list[str]] = None,
    name_placeholder: str = PROJECT_NAME_PLACEHOLDER,
    templates_path: str = PROJECT_NAME_PLACEHOLDER,
):
    """Renders templates for Dagster project."""
    click.echo(f"Creating a Dagster project at {path}.")

    project_template_path = os.path.join(os.path.dirname(__file__), "templates", templates_path)

    return scaffold_subtree(
        path=Path(path),
        project_template_path=Path(project_template_path),
        excludes=excludes,
        name_placeholder=name_placeholder,
        templates_path=templates_path,
        dagster_version=dagster_version,
    )

    click.echo(f"Generated files for Dagster project in {path}.")
