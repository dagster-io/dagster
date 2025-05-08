from pathlib import Path
from typing import Any, Optional

import click
from dagster_shared.serdes.objects import PluginObjectKey
from pydantic import BaseModel, TypeAdapter

from dagster.components.component_scaffolding import scaffold_object
from dagster.components.core.package_entry import load_package_object
from dagster.components.scaffold.scaffold import ScaffolderUnavailableReason, get_scaffolder


@click.group(name="scaffold")
def scaffold_cli() -> None:
    """Commands for scaffolding Dagster components and related entities."""


@scaffold_cli.command(name="object")
@click.argument("typename", type=str)
@click.argument("path", type=Path)
@click.option(
    "--json-params", type=str, default=None, help="JSON string containing scaffold parameters"
)
@click.option(
    "--scaffold-format",
    type=click.Choice(["yaml", "python"], case_sensitive=False),
    help="Format of the component configuration (yaml or python)",
)
@click.option("--project-root", type=Path)
def scaffold_object_command(
    typename: str,
    path: Path,
    json_params: Optional[str],
    scaffold_format: str,
    project_root: Optional[Path],
) -> None:
    key = PluginObjectKey.from_typename(typename)
    obj = load_package_object(key)

    json_params_dict = (
        parse_json_params_string(obj, json_params) if json_params is not None else None
    )

    scaffold_object(
        path,
        obj,
        typename,
        json_params_dict,
        scaffold_format,
        project_root,
    )


def parse_json_params_string(obj: object, json_params: Optional[str]) -> dict[str, Any]:
    if not json_params:
        return {}
    scaffolder = get_scaffolder(obj)
    if isinstance(scaffolder, ScaffolderUnavailableReason):
        raise Exception(f"Object {obj} does not have a scaffolder. Reason: {scaffolder.message}.")
    scaffold_params = TypeAdapter(scaffolder.get_scaffold_params()).validate_json(json_params)
    assert isinstance(scaffold_params, BaseModel)
    return scaffold_params.model_dump()
