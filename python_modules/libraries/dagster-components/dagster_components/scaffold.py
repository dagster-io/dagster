from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import click
import yaml
from pydantic import TypeAdapter

from dagster_components.core.component import Component
from dagster_components.scaffoldable.registry import get_scaffolder
from dagster_components.scaffoldable.scaffolder import ScaffolderUnavailableReason, ScaffoldRequest


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


def scaffold_object_instance(
    path: Path,
    object_type: type,
    object_type_name: str,
    raw_params: Optional[str],
) -> None:
    click.echo(f"Creating a Dagster def instance folder at {path}.")
    if not path.exists():
        path.mkdir()
    scaffolder = get_scaffolder(object_type)

    if isinstance(scaffolder, ScaffolderUnavailableReason):
        raise Exception(
            f"Object type {object_type_name} does not have a scaffolder. Reason: {scaffolder.message}."
        )

    validated_params = (
        TypeAdapter(scaffolder.get_params()).validate_json(raw_params) if raw_params else None
    )
    scaffolder.scaffold(
        ScaffoldRequest(
            type_name=object_type_name,
            target_path=path,
        ),
        validated_params,
    )

    if issubclass(object_type, Component):
        component_yaml_path = path / "component.yaml"
        if not component_yaml_path.exists():
            raise Exception(
                f"Currently all components require a component.yaml file. Please ensure your implementation of scaffold writes this file at {component_yaml_path}."
            )
