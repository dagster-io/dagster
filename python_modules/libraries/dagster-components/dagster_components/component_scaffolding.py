from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import click
import yaml

from dagster_components.scaffold.scaffold import (
    ScaffolderUnavailableReason,
    ScaffoldRequest,
    get_scaffolder,
)


class ComponentDumper(yaml.Dumper):
    def write_line_break(self) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
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


def scaffold_object(
    path: Path, obj: object, typename: str, scaffold_params: Mapping[str, Any]
) -> None:
    from dagster_components.component.component import Component

    click.echo(f"Creating a folder at {path}.")
    if not path.exists():
        path.mkdir(parents=True)
    scaffolder = get_scaffolder(obj)
    if isinstance(scaffolder, ScaffolderUnavailableReason):
        raise Exception(
            f"Object type {typename} does not have a scaffolder. Reason: {scaffolder.message}."
        )

    scaffolder.scaffold(ScaffoldRequest(type_name=typename, target_path=path), scaffold_params)

    if isinstance(obj, type) and issubclass(obj, Component):
        component_yaml_path = path / "component.yaml"
        if not component_yaml_path.exists():
            raise Exception(
                f"Currently all components require a component.yaml file. Please ensure your implementation of scaffold writes this file at {component_yaml_path}."
            )
