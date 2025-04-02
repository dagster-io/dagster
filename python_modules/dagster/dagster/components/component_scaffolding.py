import textwrap
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional, cast

import click
import yaml
from dagster_shared import check

from dagster.components.scaffold.scaffold import (
    ScaffolderUnavailableReason,
    ScaffoldFormatOptions,
    ScaffoldRequest,
    get_scaffolder,
)


class ComponentDumper(yaml.Dumper):
    def write_line_break(self) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        # add an extra line break between top-level keys
        if self.indent == 0:
            super().write_line_break()
        super().write_line_break()


def scaffold_component(
    request: ScaffoldRequest,
    yaml_attributes: Optional[Mapping[str, Any]] = None,
) -> None:
    if request.scaffold_format == "yaml":
        with open(request.target_path / "component.yaml", "w") as f:
            component_data = {"type": request.type_name, "attributes": yaml_attributes or {}}
            yaml.dump(
                component_data, f, Dumper=ComponentDumper, sort_keys=False, default_flow_style=False
            )
            f.writelines([""])
    elif request.scaffold_format == "python":
        with open(request.target_path / "component.py", "w") as f:
            fqtn = request.type_name
            check.invariant("." in fqtn, "Component must be a fully qualified type name")
            module_path, class_name = (
                ".".join(fqtn.split(".")[:-1]),
                fqtn.split(".")[-1],
            )
            f.write(
                textwrap.dedent(
                    f"""
                        from dagster.components import component, ComponentLoadContext
                        from {module_path} import {class_name}

                        @component
                        def load(context: ComponentLoadContext) -> {class_name}: ...
                """
                ).lstrip()
            )
    else:
        check.assert_never(request.scaffold_format)


def scaffold_object(
    path: Path,
    obj: object,
    typename: str,
    scaffold_params: Mapping[str, Any],
    scaffold_format: str,
) -> None:
    from dagster.components.component.component import Component

    click.echo(f"Creating a folder at {path}.")
    if not path.exists():
        path.mkdir(parents=True)
    scaffolder = get_scaffolder(obj)
    if isinstance(scaffolder, ScaffolderUnavailableReason):
        raise Exception(
            f"Object type {typename} does not have a scaffolder. Reason: {scaffolder.message}."
        )

    check.invariant(
        scaffold_format in ["yaml", "python"],
        f"scaffold must be either 'yaml' or 'python'. Got {scaffold_format}.",
    )

    scaffolder.scaffold(
        ScaffoldRequest(
            type_name=typename,
            target_path=path,
            scaffold_format=cast(ScaffoldFormatOptions, scaffold_format),
        ),
        scaffold_params,
    )

    if isinstance(obj, type) and issubclass(obj, Component):
        component_yaml_path = path / "component.yaml"
        component_py_path = path / "component.py"
        if not (component_yaml_path.exists() or component_py_path.exists()):
            raise Exception(
                f"Currently all components require a component.yaml or component.py file. Please ensure your implementation of scaffold writes this file at {component_yaml_path} or {component_py_path}."
            )
