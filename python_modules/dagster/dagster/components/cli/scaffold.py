from pathlib import Path
from typing import Optional

import click
from dagster_shared.serdes.objects import LibraryObjectKey
from pydantic import TypeAdapter

from dagster.components.component_scaffolding import scaffold_object
from dagster.components.core.library_object import load_library_object
from dagster.components.scaffold.scaffold import ScaffolderUnavailableReason, get_scaffolder


@click.group(name="scaffold")
def scaffold_cli() -> None:
    """Commands for scaffolding Dagster components and related entities."""


@scaffold_cli.command(name="object")
@click.argument("typename", type=str)
@click.argument("path", type=Path)
@click.option("--json-params", type=str, default=None)
@click.option(
    "--scaffold-format",
    type=click.Choice(["yaml", "python"], case_sensitive=False),
    help="Format of the component configuration (yaml or python)",
)
def scaffold_object_command(
    typename: str,
    path: Path,
    json_params: Optional[str],
    scaffold_format: str,
) -> None:
    key = LibraryObjectKey.from_typename(typename)
    obj = load_library_object(key)

    if json_params:
        scaffolder = get_scaffolder(obj)
        if isinstance(scaffolder, ScaffolderUnavailableReason):
            raise Exception(
                f"Object {obj} does not have a scaffolder. Reason: {scaffolder.message}."
            )
        scaffold_params = TypeAdapter(scaffolder.get_scaffold_params()).validate_json(json_params)
    else:
        scaffold_params = {}

    scaffold_object(path, obj, typename, scaffold_params, scaffold_format)
