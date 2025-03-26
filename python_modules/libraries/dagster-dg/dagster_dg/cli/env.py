from collections.abc import Sequence
from pathlib import Path

import click
import yaml
from dagster_shared.yaml_utils import parse_yaml_with_source_positions
from rich.console import Console
from rich.table import Table
from yaml.scanner import ScannerError

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.component import get_specified_env_var_deps, get_used_env_vars
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.env import ProjectEnvVars
from dagster_dg.utils import DgClickCommand, DgClickGroup
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


@click.group(name="env", cls=DgClickGroup)
def env_group():
    """Commands for managing environment variables."""


# ########################
# ##### ENVIRONMENT
# ########################


@env_group.command(name="list", cls=DgClickCommand)
@dg_global_options
@cli_telemetry_wrapper
def list_env_command(**global_options: object) -> None:
    """List environment variables from the .env file of the current project."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    env = ProjectEnvVars.from_ctx(dg_context)
    if not env.values:
        click.echo("No environment variables are defined for this project.")
        return

    table = Table(border_style="dim")
    table.add_column("Env Var")
    table.add_column("Value")
    for key, value in env.values.items():
        table.add_row(key, value)
    console = Console()
    console.print(table)


# ########################
# ##### FIX COMPONENT YAML REQUIREMENTS
# ########################


@env_group.command(name="fix-component-requirements", cls=DgClickCommand)
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@dg_global_options
def fix_component_requirements(paths: Sequence[str], **global_options: object) -> None:
    """Automatically add environment variable requirements to component yaml files."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    resolved_paths = [Path(path).absolute() for path in paths]

    updated_files = set()

    for component_dir in dg_context.defs_path.iterdir():
        if resolved_paths and not any(
            path == component_dir or path in component_dir.parents for path in resolved_paths
        ):
            continue

        component_path = component_dir / "component.yaml"

        if component_path.exists():
            text = component_path.read_text()
            try:
                component_doc_tree = parse_yaml_with_source_positions(
                    text, filename=str(component_path)
                )
            except ScannerError:
                continue

            specified_env_var_deps = get_specified_env_var_deps(component_doc_tree.value)
            used_env_vars = get_used_env_vars(component_doc_tree.value)

            if used_env_vars - specified_env_var_deps:
                component_doc_updated = component_doc_tree.value
                if "requires" not in component_doc_updated:
                    component_doc_updated["requires"] = {}
                if "env" not in component_doc_updated["requires"]:
                    component_doc_updated["requires"]["env"] = []

                component_doc_updated["requires"]["env"].extend(
                    used_env_vars - specified_env_var_deps
                )

                component_path.write_text(yaml.dump(component_doc_updated, sort_keys=False))
                click.echo(f"Updated {component_path}")
                updated_files.add(component_path)

    if updated_files:
        click.echo(f"Updated {len(updated_files)} component yaml files.")
    else:
        click.echo("No component yaml files were updated.")
