from pathlib import Path
from typing import Optional

import click
from dagster_shared.serdes.objects import PluginObjectKey

from dagster.components.component_scaffolding import scaffold_object
from dagster.components.core.package_entry import load_package_object


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

    scaffold_object(
        path,
        obj,
        typename,
        json_params,
        scaffold_format,
        project_root,
    )
