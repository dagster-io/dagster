import os
from pathlib import Path
from typing import Any, Mapping, Type

import click
import yaml
from dagster._generate.generate import generate_project
from dagster._utils import pushd

from dagster_components.core.component import (
    Component,
    ComponentGeneratorCommand,
    GenerateComponentRequest,
)


class ComponentDumper(yaml.Dumper):
    def write_line_break(self) -> None:
        # add an extra line break between top-level keys
        if self.indent == 0:
            super().write_line_break()
        super().write_line_break()


class ComponentTemplatedFolderGenerate(ComponentGeneratorCommand):
    def run(self, request: GenerateComponentRequest) -> None:
        generate_project(
            path=str(request.target_path),
            name_placeholder="COMPONENT_INSTANCE_NAME_PLACEHOLDER",
            templates_path=os.path.join(
                os.path.dirname(__file__), "templates", "COMPONENT_INSTANCE_NAME_PLACEHOLDER"
            ),
            project_name=request.name,
            component_type=request.component_type_name,
        )


class ComponentYamlGenerate(ComponentGeneratorCommand):
    def __init__(self, component_type: str, params: Mapping[str, Any]):
        self.params = params
        self.component_type = component_type

    def run(self, request: GenerateComponentRequest) -> None:
        with pushd(str(request.target_path)):
            component_data = {"type": self.component_type, "params": self.params}
            with open(request.target_path / "component.yaml", "w") as f:
                yaml.dump(
                    component_data,
                    f,
                    Dumper=ComponentDumper,
                    sort_keys=False,
                    default_flow_style=False,
                )


def generate_component_instance(
    root_path: str,
    name: str,
    component_type: Type[Component],
    component_type_name: str,
    generate_params: Any,
) -> None:
    click.echo(f"Creating a Dagster component instance at {root_path}/{name}.py.")

    component_instance_root_path = os.path.join(root_path, name)
    request = GenerateComponentRequest(
        target_path=Path(component_instance_root_path),
        name=name,
        component_type_name=component_type_name,
    )
    ComponentTemplatedFolderGenerate().run(request)

    with pushd(component_instance_root_path):
        component_params = component_type.generate_files(request, generate_params)
        ComponentYamlGenerate(component_type_name, component_params or {}).run(request)
