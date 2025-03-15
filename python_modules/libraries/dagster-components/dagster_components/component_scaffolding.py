from collections.abc import Mapping
from pathlib import Path
from pprint import pformat
from typing import Any, Optional

import click
import yaml

from dagster_components.core.component import Component
from dagster_components.scaffold import (
    DeclFormatOptions,
    ScaffolderUnavailableReason,
    ScaffoldRequest,
    get_scaffolder,
)


class ComponentDumper(yaml.Dumper):
    def write_line_break(self) -> None:
        # add an extra line break between top-level keys
        if self.indent == 0:
            super().write_line_break()
        super().write_line_break()


def scaffold_component_decl(
    request: ScaffoldRequest, attributes: Optional[Mapping[str, Any]]
) -> None:
    if request.decl_format == "yaml":
        with open(request.target_path / "component.yaml", "w") as f:
            component_data = {"type": request.type_name, "attributes": attributes or {}}
            yaml.dump(
                component_data, f, Dumper=ComponentDumper, sort_keys=False, default_flow_style=False
            )
            f.writelines([""])

    elif request.decl_format == "python":
        class_name = request.type_name.split(".")[-1]  # get the class name only
        package_name = ".".join(request.type_name.split(".")[:-1])  # package name
        with open(request.target_path / "component.py", "w") as f:
            f.write(f"""from dagster_components import component, ComponentLoadContext
from {package_name} import {class_name}


@component
def load(context: ComponentLoadContext) -> {class_name}:
    return {class_name}.from_dict(context=context, attributes={pformat(attributes or {}, indent=4)})
""")
    else:
        raise Exception(
            f"Decl format {request.decl_format} is not supported for component scaffolding."
        )


def scaffold_component_instance(
    path: Path,
    component_type: type[Component],
    component_type_name: str,
    scaffold_params: Mapping[str, Any],
    decl_format: DeclFormatOptions,
) -> None:
    from dagster_components.components.shim_components.base import ShimComponent

    click.echo(f"Creating a Dagster component instance folder at {path}.")
    if not path.exists():
        path.mkdir()
    scaffolder = get_scaffolder(component_type)

    if isinstance(scaffolder, ScaffolderUnavailableReason):
        raise Exception(
            f"Component type {component_type_name} does not have a scaffolder. Reason: {scaffolder.message}."
        )

    scaffolder.scaffold(
        ScaffoldRequest(
            type_name=component_type_name,
            target_path=path,
            decl_format=decl_format,
        ),
        scaffold_params,
    )

    if not issubclass(component_type, ShimComponent):
        component_yaml_path = path / "component.yaml"
        component_py_path = path / "component.py"
        if not (component_yaml_path.exists() or component_py_path.exists()):
            raise Exception(
                f"Currently all components require a component.yaml or a component.py file. Please ensure your implementation of scaffold writes this file at {component_yaml_path}."
            )
