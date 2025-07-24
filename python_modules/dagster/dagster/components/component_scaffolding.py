import textwrap
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional, cast

import click
import yaml
from dagster_shared import check
from dagster_shared.serdes.objects import EnvRegistryKey
from dagster_shared.seven import load_module_object
from pydantic import BaseModel, TypeAdapter

from dagster.components.scaffold.scaffold import (
    NoParams,
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

    # Format list elements with indentation - see https://github.com/yaml/pyyaml/issues/234
    def increase_indent(self, flow=False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)


def scaffold_component(
    request: ScaffoldRequest[Any],
    yaml_attributes: Optional[Mapping[str, Any]] = None,
) -> None:
    if request.scaffold_format == "yaml":
        with open(request.target_path / "defs.yaml", "w") as f:
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
                        from dagster import component_instance, ComponentLoadContext
                        from {module_path} import {class_name}

                        @component_instance
                        def load(context: ComponentLoadContext) -> {class_name}: ...
                """
                ).lstrip()
            )
    else:
        check.assert_never(request.scaffold_format)


def scaffold_object(
    path: Path,
    typename: str,
    json_params: Optional[str],
    scaffold_format: str,
    project_root: Optional[Path],
) -> None:
    from dagster.components.component.component import Component

    key = EnvRegistryKey.from_typename(typename)
    obj = load_module_object(key.namespace, key.name)

    scaffolder = get_scaffolder(obj)

    if isinstance(scaffolder, ScaffolderUnavailableReason):
        raise Exception(
            f"Object type {typename} does not have a scaffolder. Reason: {scaffolder.message}."
        )

    check.invariant(
        scaffold_format in ["yaml", "python"],
        f"scaffold must be either 'yaml' or 'python'. Got {scaffold_format}.",
    )

    params_model = parse_params_model(obj=obj, json_params=json_params)

    click.echo(f"Creating defs at {path}.")
    if not path.exists():
        path.mkdir(parents=True)

    scaffolder.scaffold(
        ScaffoldRequest(
            type_name=typename,
            target_path=path,
            scaffold_format=cast("ScaffoldFormatOptions", scaffold_format),
            project_root=project_root,
            params=params_model,
        ),
    )

    if isinstance(obj, type) and issubclass(obj, Component):
        defs_yaml_path = path / "defs.yaml"
        component_py_path = path / "component.py"
        if not (defs_yaml_path.exists() or component_py_path.exists()):
            raise Exception(
                f"Currently all components require a defs.yaml or component.py file. Please ensure your implementation of scaffold writes this file at {defs_yaml_path} or {component_py_path}."
            )


def parse_params_model(obj: object, json_params: Optional[str]) -> BaseModel:
    scaffolder = get_scaffolder(obj)

    if isinstance(scaffolder, ScaffolderUnavailableReason):
        raise Exception(f"Object {obj} does not have a scaffolder. Reason: {scaffolder.message}.")

    # Get the params model class from the scaffolder
    params_model_cls = scaffolder.get_scaffold_params()

    if params_model_cls is NoParams and not (not json_params or json_params.strip() == "{}"):
        check.invariant(not json_params or json_params.strip() == "{}", "Input should be null")
        return NoParams()

    scaffold_params = TypeAdapter(params_model_cls).validate_json(json_params or "{}")
    json_params_dict = scaffold_params.model_dump()

    return params_model_cls.model_validate(json_params_dict or {})
