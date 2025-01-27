import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import click
import yaml
from dagster._utils import mkdir_p

from dagster_components.core.component import Component
from dagster_components.core.component_scaffolder import (
    ComponentScaffolderUnavailableReason,
    ComponentScaffoldRequest,
)


class ComponentDumper(yaml.Dumper):
    def write_line_break(self) -> None:
        # add an extra line break between top-level keys
        if self.indent == 0:
            super().write_line_break()
        super().write_line_break()


def scaffold_component_yaml(
    request: ComponentScaffoldRequest, component_params: Optional[Mapping[str, Any]]
) -> None:
    with open(request.component_instance_root_path / "component.yaml", "w") as f:
        component_data = {"type": request.component_type_name, "params": component_params or {}}
        yaml.dump(
            component_data, f, Dumper=ComponentDumper, sort_keys=False, default_flow_style=False
        )
        f.writelines([""])


def scaffold_component_instance(
    root_path: str,
    name: str,
    component_type: type[Component],
    component_type_name: str,
    scaffold_params: Mapping[str, Any],
) -> None:
    component_instance_root_path = Path(os.path.join(root_path, name))
    click.echo(f"Creating a Dagster component instance folder at {component_instance_root_path}.")
    mkdir_p(str(component_instance_root_path))
    scaffolder = component_type.get_scaffolder()

    if isinstance(scaffolder, ComponentScaffolderUnavailableReason):
        raise Exception(
            f"Component type {component_type_name} does not have a scaffolder. Reason: {scaffolder.message}."
        )

    scaffolder.scaffold(
        ComponentScaffoldRequest(
            component_type_name=component_type_name,
            component_instance_root_path=component_instance_root_path,
        ),
        scaffold_params,
    )

    component_yaml_path = component_instance_root_path / "component.yaml"

    if not component_yaml_path.exists():
        raise Exception(
            f"Currently all components require a component.yaml file. Please ensure your implementation of scaffold writes this file at {component_yaml_path}."
        )
