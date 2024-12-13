import os
from pathlib import Path
from typing import Any, Type

import click
import yaml
from dagster._utils import mkdir_p, pushd

from dagster_components.core.component import Component


class ComponentDumper(yaml.Dumper):
    def write_line_break(self) -> None:
        # add an extra line break between top-level keys
        if self.indent == 0:
            super().write_line_break()
        super().write_line_break()


def generate_component_instance(
    root_path: str,
    name: str,
    component_type: Type[Component],
    component_type_name: str,
    generate_params: Any,
) -> None:
    component_instance_root_path = os.path.join(root_path, name)
    click.echo(f"Creating a Dagster component instance folder at {component_instance_root_path}.")
    mkdir_p(component_instance_root_path)
    with pushd(component_instance_root_path):
        component_params = component_type.generate_files(generate_params)
        component_data = {"type": component_type_name, "params": component_params or {}}
    with open(Path(component_instance_root_path) / "component.yaml", "w") as f:
        yaml.dump(
            component_data, f, Dumper=ComponentDumper, sort_keys=False, default_flow_style=False
        )
