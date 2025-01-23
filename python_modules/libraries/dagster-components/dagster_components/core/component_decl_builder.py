from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Optional, TypeVar, Union

from dagster._record import record
from dagster._utils import pushd
from dagster._utils.pydantic_yaml import (
    _parse_and_populate_model_with_annotated_errors,
    enrich_validation_errors_with_source_position,
)
from dagster._utils.source_position import SourcePositionTree
from dagster._utils.yaml_utils import parse_yaml_with_source_positions
from pydantic import BaseModel, TypeAdapter

from dagster_components.core.component import ComponentDeclNode, ComponentLoadContext


class ComponentFileModel(BaseModel):
    type: str
    params: Optional[Mapping[str, Any]] = None


T = TypeVar("T", bound=BaseModel)


@record
class YamlComponentDecl(ComponentDeclNode):
    path: Path
    component_file_model: ComponentFileModel
    source_position_tree: Optional[SourcePositionTree] = None

    @staticmethod
    def from_path(component_file_path: Path) -> "YamlComponentDecl":
        parsed = parse_yaml_with_source_positions(
            component_file_path.read_text(), str(component_file_path)
        )
        obj = _parse_and_populate_model_with_annotated_errors(
            cls=ComponentFileModel, obj_parse_root=parsed, obj_key_path_prefix=[]
        )

        return YamlComponentDecl(
            path=component_file_path.parent,
            component_file_model=obj,
            source_position_tree=parsed.source_position_tree,
        )

    def get_params(self, context: ComponentLoadContext, params_schema: type[T]) -> T:
        with pushd(str(self.path)):
            raw_params = self.component_file_model.params
            preprocessed_params = context.templated_value_resolver.resolve_params(
                raw_params, params_schema
            )

            if self.source_position_tree:
                source_position_tree_of_params = self.source_position_tree.children["params"]
                with enrich_validation_errors_with_source_position(
                    source_position_tree_of_params, ["params"]
                ):
                    return TypeAdapter(params_schema).validate_python(preprocessed_params)
            else:
                return TypeAdapter(params_schema).validate_python(preprocessed_params)


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
        return YamlComponentDecl.from_path(component_path)

    subs = []
    for subpath in path.iterdir():
        component = path_to_decl_node(subpath)
        if component:
            subs.append(component)

    return ComponentFolder(path=path, sub_decls=subs)
