import os
from pathlib import Path
from typing import Any, Mapping, Optional, Type

import click
import yaml
from dagster._utils import mkdir_p

from dagster_components.core.component import Component, ComponentGenerateRequest


class ComponentDumper(yaml.Dumper):
    def write_line_break(self) -> None:
        # add an extra line break between top-level keys
        if self.indent == 0:
            super().write_line_break()
        super().write_line_break()


def generate_component_yaml(
    request: ComponentGenerateRequest, component_params: Optional[Mapping[str, Any]]
) -> None:
    with open(request.component_instance_root_path / "component.yaml", "w") as f:
        component_data = {"type": request.component_type_name, "params": component_params or {}}
        yaml.dump(
            component_data, f, Dumper=ComponentDumper, sort_keys=False, default_flow_style=False
        )


def generate_component_instance(
    root_path: str,
    name: str,
    component_type: Type[Component],
    component_type_name: str,
    generate_params: Mapping[str, Any],
) -> None:
    component_instance_root_path = Path(os.path.join(root_path, name))
    click.echo(f"Creating a Dagster component instance folder at {component_instance_root_path}.")
    mkdir_p(str(component_instance_root_path))
    component_type.generate_files(
        ComponentGenerateRequest(
            component_type_name=component_type_name,
            component_instance_root_path=component_instance_root_path,
        ),
        generate_params,
    )

    component_yaml_path = component_instance_root_path / "component.yaml"

    if not component_yaml_path.exists():
        raise Exception(
            f"Currently all components require a component.yaml file. Please ensure your implementation of generate_files writes this file at {component_yaml_path}."
        )
