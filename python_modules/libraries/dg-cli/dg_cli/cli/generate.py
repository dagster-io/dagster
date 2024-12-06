import os
import sys
from pathlib import Path
from typing import Optional, Tuple

import click

from dg_cli.context import (
    CodeLocationProjectContext,
    DeploymentProjectContext,
    is_inside_code_location_project,
    is_inside_deployment_project,
)
from dg_cli.generate import (
    generate_code_location,
    generate_component_instance,
    generate_component_type,
    generate_deployment,
)


@click.group(name="generate")
def generate_cli() -> None:
    """Commands for generating Dagster components and related entities."""


@generate_cli.command(name="deployment")
@click.argument("path", type=str)
def generate_deployment_command(path: str) -> None:
    """Generate a Dagster deployment instance."""
    dir_abspath = os.path.abspath(path)
    if os.path.exists(dir_abspath):
        click.echo(
            click.style(f"A file or directory at {dir_abspath} already exists. ", fg="red")
            + "\nPlease delete the contents of this path or choose another location."
        )
        sys.exit(1)
    generate_deployment(path)


@generate_cli.command(name="code-location")
@click.argument("name", type=str)
@click.option("--use-editable-dagster", is_flag=True, default=False)
def generate_code_location_command(name: str, use_editable_dagster: bool) -> None:
    """Generate a Dagster code location inside a component."""
    if is_inside_deployment_project(Path.cwd()):
        context = DeploymentProjectContext.from_path(Path.cwd())
        if context.has_code_location(name):
            click.echo(click.style(f"A code location named {name} already exists.", fg="red"))
            sys.exit(1)
        code_location_path = os.path.join(context.code_location_root_path, name)
    else:
        code_location_path = os.path.join(Path.cwd(), name)

    if use_editable_dagster:
        if "DAGSTER_GIT_REPO_DIR" not in os.environ:
            click.echo(
                click.style(
                    "The `--use-editable-dagster` flag requires the `DAGSTER_GIT_REPO_DIR` environment variable to be set.",
                    fg="red",
                )
            )
            sys.exit(1)
        editable_dagster_root = os.environ["DAGSTER_GIT_REPO_DIR"]
    else:
        editable_dagster_root = None

    generate_code_location(code_location_path, editable_dagster_root)


@generate_cli.command(name="component-type")
@click.argument("name", type=str)
def generate_component_type_command(name: str) -> None:
    """Generate a Dagster component instance."""
    if not is_inside_code_location_project(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location project.", fg="red"
            )
        )
        sys.exit(1)
    context = CodeLocationProjectContext.from_path(Path.cwd())
    full_component_name = f"{context.name}.{name}"
    if context.has_component_type(full_component_name):
        click.echo(click.style(f"A component type named `{name}` already exists.", fg="red"))
        sys.exit(1)

    generate_component_type(context.component_types_root_path, name)


@generate_cli.command(name="component")
@click.argument("component_type", type=str)
@click.argument("component_name", type=str)
@click.option("--json-params", type=str, default=None)
@click.argument("extra_args", nargs=-1, type=str)
def generate_component_command(
    component_type: str,
    component_name: str,
    json_params: Optional[str],
    extra_args: Tuple[str, ...],
) -> None:
    if not is_inside_code_location_project(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location project.", fg="red"
            )
        )
        sys.exit(1)

    context = CodeLocationProjectContext.from_path(Path.cwd())
    if not context.has_component_type(component_type):
        click.echo(
            click.style(f"No component type `{component_type}` could be resolved.", fg="red")
        )
        sys.exit(1)
    elif context.has_component_instance(component_name):
        click.echo(
            click.style(f"A component instance named `{component_name}` already exists.", fg="red")
        )
        sys.exit(1)

    generate_component_instance(
        context.component_instances_root_path,
        component_name,
        component_type,
        json_params,
        extra_args,
    )
