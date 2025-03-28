import inspect
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from functools import cached_property
from pathlib import Path
from types import ModuleType
from typing import Any, Optional, TypeVar

import dagster._check as check
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_module,
)
from dagster._core.definitions.module_loaders.utils import find_objects_in_module_of_types
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._record import record
from dagster._utils import pushd
from dagster._utils.pydantic_yaml import (
    _parse_and_populate_model_with_annotated_errors,
    enrich_validation_errors_with_source_position,
)
from dagster_shared.serdes.objects import LibraryObjectKey
from dagster_shared.yaml_utils import parse_yaml_with_source_positions
from dagster_shared.yaml_utils.source_position import SourcePositionTree
from pydantic import BaseModel, ConfigDict, TypeAdapter

from dagster_components.component.component import Component
from dagster_components.component.component_loader import is_component_loader
from dagster_components.core.context import ComponentLoadContext
from dagster_components.core.library_object import load_library_object

T = TypeVar("T", bound=BaseModel)


class ComponentFileModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    attributes: Optional[Mapping[str, Any]] = None


#########
# MODULES
#########


@record
class DefsModule(ABC):
    path: Path

    @abstractmethod
    def build_defs(self) -> Definitions: ...


@record
class SubpackageDefsModule(DefsModule):
    """A folder containing multiple submodules."""

    submodules: Sequence[DefsModule]

    def build_defs(self) -> Definitions:
        return Definitions.merge(*(submodule.build_defs() for submodule in self.submodules))


@record
class PythonDefsModule(DefsModule):
    """A module containing python dagster definitions."""

    module: Any  # ModuleType

    def build_defs(self) -> Definitions:
        definitions_objects = list(find_objects_in_module_of_types(self.module, Definitions))
        if len(definitions_objects) == 0:
            return load_definitions_from_module(self.module)
        elif len(definitions_objects) == 1:
            return next(iter(definitions_objects))
        else:
            raise DagsterInvalidDefinitionError(
                f"Found multiple Definitions objects in {self.path}. At most one Definitions object "
                "may be specified per module."
            )


@record
class ComponentDefsModule(DefsModule):
    """A module containing a component definition."""

    context: ComponentLoadContext
    component: Component

    def build_defs(self) -> Definitions:
        return self.component.build_defs(self.context)


#######
# DECLS
#######


def _parse_component_yaml(path: Path) -> tuple[SourcePositionTree, ComponentFileModel]:
    component_file_path = path / "component.yaml"
    source_tree = parse_yaml_with_source_positions(
        component_file_path.read_text(), str(component_file_path)
    )
    return (
        source_tree.source_position_tree,
        _parse_and_populate_model_with_annotated_errors(
            cls=ComponentFileModel, obj_parse_root=source_tree, obj_key_path_prefix=[]
        ),
    )


@record
class DefsModuleDecl(ABC):
    path: Path

    def get_source_position_tree(self) -> Optional[SourcePositionTree]:
        return None

    @staticmethod
    def from_path(path: Path) -> Optional["DefsModuleDecl"]:
        # this defines the priority of the decl types, we return the first one that matches
        decltypes = (
            YamlComponentDecl,
            PythonComponentDecl,
            PythonModuleDecl,
            SubpackageDefsModuleDecl,
        )
        decl_filter = filter(None, (cls.from_path(path) for cls in decltypes))
        return next(decl_filter, None)

    @staticmethod
    def from_module(module: ModuleType) -> Optional["DefsModuleDecl"]:
        """Given a Python module, returns a corresponding defs declaration.

        Args:
            module (ModuleType): The Python module to convert to a component declaration node.

        Returns:
            Optional[ComponentDeclNode]: The corresponding component declaration node, or None if the module does not contain a component.
        """
        module_path = (
            Path(module.__file__).parent
            if module.__file__
            else Path(module.__path__[0])
            if module.__path__
            else None
        )
        return DefsModuleDecl.from_path(
            check.not_none(module_path, f"Module {module.__name__} has no filepath")
        )

    @abstractmethod
    def load(self, context: ComponentLoadContext) -> DefsModule: ...


@record
class SubpackageDefsModuleDecl(DefsModuleDecl):
    """A folder containing multiple submodules."""

    subdecls: Sequence[DefsModuleDecl]

    @staticmethod
    def from_path(path: Path) -> Optional["SubpackageDefsModuleDecl"]:
        if path.is_dir():
            subdecls = (DefsModuleDecl.from_path(subpath) for subpath in path.iterdir())
            return SubpackageDefsModuleDecl(
                path=path,
                subdecls=list(filter(None, subdecls)),
            )
        else:
            return None

    def load(self, context: ComponentLoadContext) -> SubpackageDefsModule:
        return SubpackageDefsModule(
            path=self.path,
            submodules=[decl.load(context.for_decl(decl)) for decl in self.subdecls],
        )


@record
class PythonModuleDecl(DefsModuleDecl):
    """A python module containing a `definitions.py` file."""

    path: Path

    @staticmethod
    def from_path(path: Path) -> Optional["PythonModuleDecl"]:
        if (path / "definitions.py").exists() or path.suffix == ".py":
            return PythonModuleDecl(path=path)
        else:
            return None

    def load(self, context: ComponentLoadContext) -> PythonDefsModule:
        if self.path.is_dir():
            module = context.load_defs_relative_python_module(self.path / "definitions.py")
        else:
            module = context.load_defs_relative_python_module(self.path)
        return PythonDefsModule(path=self.path, module=module)


@record
class YamlComponentDecl(DefsModuleDecl):
    """A component configured with a `component.yaml` file."""

    component_file_model: ComponentFileModel
    source_position_tree: Optional[SourcePositionTree] = None

    @staticmethod
    def from_path(path: Path) -> Optional["YamlComponentDecl"]:
        if (path / "component.yaml").exists():
            position_tree, component_file_model = _parse_component_yaml(path)
            return YamlComponentDecl(
                path=path,
                component_file_model=component_file_model,
                source_position_tree=position_tree,
            )
        else:
            return None

    def get_source_position_tree(self) -> Optional[SourcePositionTree]:
        return self.source_position_tree

    def get_attributes(self, schema: type[T]) -> T:
        with pushd(str(self.path)):
            if self.source_position_tree:
                source_position_tree_of_attributes = self.source_position_tree.children[
                    "attributes"
                ]
                with enrich_validation_errors_with_source_position(
                    source_position_tree_of_attributes, ["attributes"]
                ):
                    return TypeAdapter(schema).validate_python(self.component_file_model.attributes)
            else:
                return TypeAdapter(schema).validate_python(self.component_file_model.attributes)

    def load(self, context: ComponentLoadContext) -> ComponentDefsModule:
        type_str = context.normalize_component_type_str(self.component_file_model.type)
        key = LibraryObjectKey.from_typename(type_str)
        obj = load_library_object(key)
        if not isinstance(obj, type) or not issubclass(obj, Component):
            raise DagsterInvalidDefinitionError(
                f"Component type {type_str} is of type {type(obj)}, but must be a subclass of dagster_components.Component"
            )
        component_schema = obj.get_schema()
        context = context.with_rendering_scope(obj.get_additional_scope())

        attributes = self.get_attributes(component_schema) if component_schema else None
        component = obj.load(attributes, context)
        return ComponentDefsModule(path=self.path, context=context, component=component)


@record
class PythonComponentDecl(DefsModuleDecl):
    """A component configured with a `component.py` file."""

    @staticmethod
    def from_path(path: Path) -> Optional["PythonComponentDecl"]:
        if (path / "component.py").exists():
            return PythonComponentDecl(path=path)
        else:
            return

    def load(self, context: ComponentLoadContext) -> ComponentDefsModule:
        module = context.load_defs_relative_python_module(self.path / "component.py")
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
            return ComponentDefsModule(
                path=self.path,
                context=context,
                component=component_loader(context),
            )


@record
class DirectForTestComponentDecl(DefsModuleDecl):
    component_type: type[Component]
    attributes_yaml: str

    @cached_property
    def _obj_and_tree(self) -> tuple[Any, SourcePositionTree]:
        parsed = parse_yaml_with_source_positions(self.attributes_yaml)
        attr_schema = check.not_none(
            self.component_type.get_schema(), "Component must have schema for direct test"
        )
        obj = _parse_and_populate_model_with_annotated_errors(
            cls=attr_schema, obj_parse_root=parsed, obj_key_path_prefix=[]
        )
        return obj, parsed.source_position_tree

    def get_source_position_tree(self) -> SourcePositionTree:
        _, tree = self._obj_and_tree
        return tree

    def load(self, context: ComponentLoadContext):  # type: ignore
        context = context.with_rendering_scope(self.component_type.get_additional_scope())
        obj, tree = self._obj_and_tree
        attr_schema = check.not_none(
            self.component_type.get_schema(), "Component must have schema for direct test"
        )
        with enrich_validation_errors_with_source_position(tree, []):
            attributes = TypeAdapter(attr_schema).validate_python(obj)
        return [self.component_type.load(attributes, context)]
