from pathlib import Path
from typing import Optional

import click
from pydantic import TypeAdapter

from dagster_components.blueprint import BlueprintUnavailableReason, get_blueprint
from dagster_components.component_scaffolding import scaffold_component_instance
from dagster_components.core.component import load_component_type
from dagster_components.core.component_key import ComponentKey


@click.group(name="scaffold")
def scaffold_cli() -> None:
    """Commands for scaffolding Dagster components and related entities."""


@scaffold_cli.command(name="component")
@click.argument("component_type", type=str)
@click.argument("component_path", type=Path)
@click.option("--json-params", type=str, default=None)
def scaffold_component_command(
    component_type: str,
    component_path: Path,
    json_params: Optional[str],
) -> None:
    key = ComponentKey.from_typename(component_type)
    component_type_cls = load_component_type(key)

    if json_params:
        blueprint = get_blueprint(component_type_cls)
        if isinstance(blueprint, BlueprintUnavailableReason):
            raise Exception(
                f"Component type {component_type} does not have a blueprint. Reason: {blueprint.message}."
            )
        scaffold_params = TypeAdapter(blueprint.get_scaffold_params()).validate_json(json_params)
    else:
        scaffold_params = {}

    scaffold_component_instance(
        component_path,
        component_type_cls,
        component_type,
        scaffold_params,
    )
