from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

from dagster._record import record
from dagster._utils.pydantic_yaml import parse_yaml_file_to_pydantic
from pydantic import BaseModel

from dagster_components.core.component import ComponentDeclNode


class DefsFileModel(BaseModel):
    component_type: str
    component_params: Optional[Mapping[str, Any]] = None


@record
class YamlComponentDecl(ComponentDeclNode):
    path: Path
    defs_file_model: DefsFileModel


@record
class ComponentFolder(ComponentDeclNode):
    path: Path
    sub_decls: Sequence[Union[YamlComponentDecl, "ComponentFolder"]]


def find_component_decl(path: Path) -> Optional[ComponentDeclNode]:
    # right now, we only support two types of components, both of which are folders
    # if the folder contains a defs.yml file, it's a component instance
    # otherwise, it's a folder containing sub-components

    if not path.is_dir():
        return None

    defs_path = path / "defs.yml"

    if defs_path.exists():
        defs_file_model = parse_yaml_file_to_pydantic(
            DefsFileModel, defs_path.read_text(), str(path)
        )
        return YamlComponentDecl(path=path, defs_file_model=defs_file_model)

    subs = []
    for subpath in path.iterdir():
        component = find_component_decl(subpath)
        if component:
            subs.append(component)

    return ComponentFolder(path=path, sub_decls=subs) if subs else None
