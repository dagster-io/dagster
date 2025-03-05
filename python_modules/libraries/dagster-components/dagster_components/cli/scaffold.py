from pathlib import Path
from typing import Optional

import click

from dagster_components.core.component import load_component_type
from dagster_components.core.component_key import ComponentKey
from dagster_components.scaffold import scaffold_object_instance


@click.group(name="scaffold")
def scaffold_cli() -> None:
    """Commands for scaffolding Dagster components and related entities."""


@scaffold_cli.command(name="object")
@click.argument("object_type", type=str)
@click.argument("path", type=Path)
@click.option("--json-params", type=str, default=None)
def scaffold_object_command(
    object_type: str,
    path: Path,
    json_params: Optional[str],
) -> None:
    key = ComponentKey.from_typename(object_type)
    component_type_cls = load_component_type(key)

    scaffold_object_instance(path, component_type_cls, object_type, json_params)
