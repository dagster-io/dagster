import inspect
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence, Union

from dagster._record import record
from dagster._seven import import_uncached_module_from_path
from dagster._utils.pydantic_yaml import parse_yaml_file_to_pydantic
from pydantic import BaseModel

from dagster_components.core.component import (
    Component,
    ComponentDeclNode,
    ComponentInstanceDeclNode,
    ComponentKey,
    ComponentLoadContext,
    get_component_name,
)
from dagster_components.core.component_declaration import is_component_declaration


class ComponentFileModel(BaseModel):
    type: str
    params: Optional[Mapping[str, Any]] = None


@record
class YamlComponentDecl(ComponentInstanceDeclNode):
    component_file_model: ComponentFileModel


@record
class PythonComponentDecl(ComponentInstanceDeclNode):
    component_declaration: Callable[[ComponentLoadContext], Component]


@record
class ComponentFolder(ComponentDeclNode):
    path: Path
    sub_decls: Sequence[Union[YamlComponentDecl, "ComponentFolder"]]


def path_to_decl_node(
    path: Path, current_key: ComponentKey, code_location_name: str
) -> Optional[ComponentDeclNode]:
    # right now, we only support two types of components, both of which are folders
    # if the folder contains a component.yaml file, it's a component instance
    # otherwise, it's a folder containing sub-components

    if not path.is_dir():
        return None

    component_path = path / "component.yaml"

    if component_path.exists():
        component_file_model = parse_yaml_file_to_pydantic(
            ComponentFileModel, component_path.read_text(), str(path)
        )
        return YamlComponentDecl(
            path=path,
            component_file_model=component_file_model,
            key=current_key.child(path.name),
            component_type=component_file_model.type,
        )

    python_component_path = path / "component.py"

    if python_component_path.exists():
        python_decl_key = current_key.child(path.name)
        module = import_uncached_module_from_path(
            f"__dagster_code_location__.{code_location_name}.__component_decl__.{python_decl_key.dot_path}",
            str(python_component_path),
        )

        for _name, obj in inspect.getmembers(module, inspect.isfunction):
            if is_component_declaration(obj):
                signature = inspect.signature(obj)
                component_type_name = get_component_name(signature.return_annotation)
                return PythonComponentDecl(
                    path=path,
                    key=python_decl_key,
                    component_declaration=obj,
                    component_type=component_type_name,
                )

        raise Exception(f"Could not find component declaration in {python_component_path}")

    subs = []
    for subpath in path.iterdir():
        component = path_to_decl_node(subpath, current_key.child(subpath.name), code_location_name)
        if component:
            subs.append(component)

    return ComponentFolder(path=path, sub_decls=subs)
