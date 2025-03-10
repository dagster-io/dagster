from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import click
import yaml

from dagster_components.blueprint import BlueprintUnavailableReason, ScaffoldRequest, get_blueprint
from dagster_components.core.component import Component


class ComponentDumper(yaml.Dumper):
    def write_line_break(self) -> None:
        # add an extra line break between top-level keys
        if self.indent == 0:
            super().write_line_break()
        super().write_line_break()


def scaffold_component_yaml(
    request: ScaffoldRequest, attributes: Optional[Mapping[str, Any]]
) -> None:
    with open(request.target_path / "component.yaml", "w") as f:
        component_data = {"type": request.type_name, "attributes": attributes or {}}
        yaml.dump(
            component_data, f, Dumper=ComponentDumper, sort_keys=False, default_flow_style=False
        )
        f.writelines([""])


def scaffold_component_instance(
    path: Path,
    component_type: type[Component],
    component_type_name: str,
    scaffold_params: Mapping[str, Any],
) -> None:
    from dagster_components.components.shim_components.base import ShimComponent

    click.echo(f"Creating a Dagster component instance folder at {path}.")
    if not path.exists():
        path.mkdir()
    blueprint = get_blueprint(component_type)

    if isinstance(blueprint, BlueprintUnavailableReason):
        raise Exception(
            f"Component type {component_type_name} does not have a blueprint. Reason: {blueprint.message}."
        )

    blueprint.scaffold(
        ScaffoldRequest(
            type_name=component_type_name,
            target_path=path,
        ),
        scaffold_params,
    )

    if not issubclass(component_type, ShimComponent):
        component_yaml_path = path / "component.yaml"
        if not component_yaml_path.exists():
            raise Exception(
                f"Currently all components require a component.yaml file. Please ensure your implementation of scaffold writes this file at {component_yaml_path}."
            )
