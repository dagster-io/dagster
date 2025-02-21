import json
from pathlib import Path

import click

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.component import all_components_schema_from_dg_context
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickCommand, DgClickGroup
from dagster_dg.utils.editor import (
    install_or_update_yaml_schema_extension,
    recommend_yaml_extension,
)

_DEFAULT_SCHEMA_FOLDER_NAME = ".vscode"


@click.group(name="utils", cls=DgClickGroup)
def utils_group():
    """Assorted utility commands."""


@utils_group.command(name="configure-editor", cls=DgClickCommand)
@dg_global_options
@click.argument("editor", type=click.Choice(["vscode", "cursor"]))
@click.pass_context
def configure_editor_command(
    context: click.Context,
    editor: str,
    **global_options: object,
) -> None:
    """Generates and installs a VS Code or Cursor extension which provides JSON schemas for Components types specified by YamlComponentsLoader objects."""
    executable_name = "code" if editor == "vscode" else "cursor"

    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    recommend_yaml_extension(executable_name)

    schema_folder = dg_context.root_path / _DEFAULT_SCHEMA_FOLDER_NAME
    schema_folder.mkdir(exist_ok=True)

    schema_path = schema_folder / "schema.json"
    schema_path.write_text(json.dumps(all_components_schema_from_dg_context(dg_context), indent=2))

    install_or_update_yaml_schema_extension(executable_name, dg_context.root_path, schema_path)
