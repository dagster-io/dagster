from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

from dagster._record import record
from dagster._utils.pydantic_yaml import parse_yaml_file_to_pydantic
from pydantic import BaseModel

from dagster_components.core.component import ComponentDeclNode


class ComponentFileModel(BaseModel):
    type: str
    params: Optional[Mapping[str, Any]] = None


@record
class YamlComponentDecl(ComponentDeclNode):
    path: Path
    component_file_model: ComponentFileModel


@record
class ComponentFolder(ComponentDeclNode):
    path: Path
    sub_decls: Sequence[Union[YamlComponentDecl, "ComponentFolder"]]


def path_to_decl_node(path: Path) -> Optional[ComponentDeclNode]:
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
        return YamlComponentDecl(path=path, component_file_model=component_file_model)

    subs = []
    for subpath in path.iterdir():
        component = path_to_decl_node(subpath)
        if component:
            subs.append(component)

    return ComponentFolder(path=path, sub_decls=subs) if subs else None
