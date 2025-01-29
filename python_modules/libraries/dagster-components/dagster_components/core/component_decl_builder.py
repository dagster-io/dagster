import inspect
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Optional, TypeVar, Union

from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._record import record
from dagster._utils import pushd
from dagster._utils.pydantic_yaml import (
    _parse_and_populate_model_with_annotated_errors,
    enrich_validation_errors_with_source_position,
)
from dagster._utils.source_position import SourcePositionTree
from dagster._utils.yaml_utils import parse_yaml_with_source_positions
from pydantic import BaseModel, TypeAdapter

from dagster_components.core.component import (
    Component,
    ComponentDeclNode,
    ComponentLoadContext,
    ComponentTypeRegistry,
    get_component_type_name,
    is_component_loader,
    is_registered_component_type,
)
from dagster_components.utils import load_module_from_path


class ComponentFileModel(BaseModel):
    type: str
    params: Optional[Mapping[str, Any]] = None


T = TypeVar("T", bound=BaseModel)


def find_local_component_types(component_path: Path) -> list[type[Component]]:
    """Find all component types defined in a component directory."""
    component_types = []
    for py_file in component_path.glob("*.py"):
        module_name = py_file.stem

        module = load_module_from_path(module_name, component_path / f"{module_name}.py")

        for _name, obj in inspect.getmembers(module, inspect.isclass):
            assert isinstance(obj, type)
            if is_registered_component_type(obj):
                component_types.append(obj)
    return component_types


@record
class PythonComponentDecl(ComponentDeclNode):
    path: Path

    @staticmethod
    def component_file_path(path: Path) -> Path:
        return path / "component.py"

    @staticmethod
    def exists_at(path: Path) -> bool:
        return PythonComponentDecl.component_file_path(path).exists()

    @staticmethod
    def from_path(path: Path) -> "PythonComponentDecl":
        return PythonComponentDecl(path=path)

    def load(self, context: ComponentLoadContext) -> Sequence[Component]:
        module = load_module_from_path(
            self.path.stem, PythonComponentDecl.component_file_path(self.path)
        )
        component_loaders = list(inspect.getmembers(module, is_component_loader))
        if len(component_loaders) < 1:
            raise DagsterInvalidDefinitionError("No component loaders found in module")
        elif len(component_loaders) > 1:
            # note: we could support multiple component loaders in the same file, just
            # being more restrictive to start
            raise DagsterInvalidDefinitionError(
                f"Multiple component loaders found in module: {component_loaders}"
            )
        else:
            _, component_loader = component_loaders[0]
            return [component_loader(context)]


@record
class YamlComponentDecl(ComponentDeclNode):
    path: Path
    component_file_model: ComponentFileModel
    source_position_tree: Optional[SourcePositionTree] = None

    @staticmethod
    def component_file_path(path: Path) -> Path:
        return path / "component.yaml"

    @staticmethod
    def exists_at(path: Path) -> bool:
        return YamlComponentDecl.component_file_path(path).exists()

    @staticmethod
    def from_path(path: Path) -> "YamlComponentDecl":
        component_file_path = YamlComponentDecl.component_file_path(path)
        parsed = parse_yaml_with_source_positions(
            component_file_path.read_text(), str(component_file_path)
        )
        obj = _parse_and_populate_model_with_annotated_errors(
            cls=ComponentFileModel, obj_parse_root=parsed, obj_key_path_prefix=[]
        )

        return YamlComponentDecl(
            path=path,
            component_file_model=obj,
            source_position_tree=parsed.source_position_tree,
        )

    def get_component_type(self, registry: ComponentTypeRegistry) -> type[Component]:
        parsed_defs = self.component_file_model
        if parsed_defs.type.startswith("."):
            component_registry_key = parsed_defs.type[1:]

            for component_type in find_local_component_types(self.path):
                if get_component_type_name(component_type) == component_registry_key:
                    return component_type

            raise Exception(
                f"Could not find component type {component_registry_key} in {self.path}"
            )

        return registry.get(parsed_defs.type)

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

    def load(self, context: ComponentLoadContext) -> Sequence[Component]:
        component_type = self.get_component_type(context.registry)
        component_schema = component_type.get_schema()
        context = context.with_rendering_scope(component_type.get_additional_scope())
        loaded_params = self.get_params(context, component_schema) if component_schema else None
        return [component_type.load(loaded_params, context)]


@record
class ComponentFolder(ComponentDeclNode):
    path: Path
    sub_decls: Sequence[Union[YamlComponentDecl, PythonComponentDecl, "ComponentFolder"]]

    def load(self, context: ComponentLoadContext) -> Sequence[Component]:
        components = []
        for sub_decl in self.sub_decls:
            sub_context = context.for_decl_node(sub_decl)
            components.extend(sub_decl.load(sub_context))
        return components


def path_to_decl_node(path: Path) -> Optional[ComponentDeclNode]:
    # right now, we only support two types of components, both of which are folders
    # if the folder contains a component.yaml file, it's a component instance
    # otherwise, it's a folder containing sub-components

    if not path.is_dir():
        return None

    if YamlComponentDecl.exists_at(path):
        return YamlComponentDecl.from_path(path)
    elif PythonComponentDecl.exists_at(path):
        return PythonComponentDecl.from_path(path)

    subs = []
    for subpath in path.iterdir():
        component = path_to_decl_node(subpath)
        if component:
            subs.append(component)

    return ComponentFolder(path=path, sub_decls=subs)
