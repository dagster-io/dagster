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
from dagster_shared.yaml_utils import parse_yaml_with_source_positions
from dagster_shared.yaml_utils.source_position import SourcePositionTree
from pydantic import BaseModel, ConfigDict, TypeAdapter

from dagster_components.core.component import (
    Component,
    ComponentLoadContext,
    DefsLoader,
    DefsModule,
    is_defs_module,
    load_component_type,
)
from dagster_components.core.component_key import ComponentKey
from dagster_components.utils import load_module_from_path

T = TypeVar("T", bound=BaseModel)


class ComponentFileModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    attributes: Optional[Mapping[str, Any]] = None


#########
# Module Resolver
#########


@record
class DefsModuleResolver(ABC):
    path: Path

    @abstractmethod
    def build_defs(self) -> Definitions: ...


@record
class SubpackageDefsModule(DefsModuleResolver):
    """A folder containing multiple submodules."""

    submodules: Sequence[DefsModuleResolver]

    def build_defs(self) -> Definitions:
        return Definitions.merge(*(submodule.build_defs() for submodule in self.submodules))


@record
class PythonDefsModule(DefsModuleResolver):
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
class DefsFactoryModuleResolver(DefsModuleResolver):
    """A module containing a defs factory."""

    context: ComponentLoadContext
    defs_factory: DefsLoader
    defs_module: Optional[DefsModule]  # created for pythonic components

    def build_defs(self) -> Definitions:
        return self.defs_factory.build_defs(self.context)


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
class DefsModuleDeclNode(ABC):
    path: Path

    def get_source_position_tree(self) -> Optional[SourcePositionTree]:
        return None

    @staticmethod
    def from_path(path: Path) -> Optional["DefsModuleDeclNode"]:
        # this defines the priority of the decl types, we return the first one that matches
        decltypes = (
            YamlComponentDeclNode,
            PythonComponentDeclNode,
            PythonModuleDecl,
            SubpackageDefsModuleDecl,
        )
        decl_filter = filter(None, (cls.from_path(path) for cls in decltypes))
        return next(decl_filter, None)

    @staticmethod
    def from_module(module: ModuleType) -> Optional["DefsModuleDeclNode"]:
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
        return DefsModuleDeclNode.from_path(
            check.not_none(module_path, f"Module {module.__name__} has no filepath")
        )

    @abstractmethod
    def load(self, context: ComponentLoadContext) -> DefsModuleResolver: ...


@record
class SubpackageDefsModuleDecl(DefsModuleDeclNode):
    """A folder containing multiple submodules."""

    subdecls: Sequence[DefsModuleDeclNode]

    @staticmethod
    def from_path(path: Path) -> Optional["SubpackageDefsModuleDecl"]:
        if path.is_dir():
            subdecls = (DefsModuleDeclNode.from_path(subpath) for subpath in path.iterdir())
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
class PythonModuleDecl(DefsModuleDeclNode):
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
class YamlComponentDeclNode(DefsModuleDeclNode):
    """A component configured with a `component.yaml` file."""

    component_file_model: ComponentFileModel
    source_position_tree: Optional[SourcePositionTree] = None

    @staticmethod
    def from_path(path: Path) -> Optional["YamlComponentDeclNode"]:
        if (path / "component.yaml").exists():
            position_tree, component_file_model = _parse_component_yaml(path)
            return YamlComponentDeclNode(
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

    def load(self, context: ComponentLoadContext) -> DefsFactoryModuleResolver:
        type_str = context.normalize_component_type_str(self.component_file_model.type)
        key = ComponentKey.from_typename(type_str)
        component_type = load_component_type(key)
        component_schema = component_type.get_schema()
        context = context.with_rendering_scope(component_type.get_additional_scope())

        attributes = self.get_attributes(component_schema) if component_schema else None
        component = component_type.load(attributes, context)
        return DefsFactoryModuleResolver(
            path=self.path, context=context, defs_factory=component, defs_module=None
        )


@record
class PythonComponentDeclNode(DefsModuleDeclNode):
    """A component configured with a `component.py` file."""

    @staticmethod
    def from_path(path: Path) -> Optional["PythonComponentDeclNode"]:
        if (path / "component.py").exists():
            return PythonComponentDeclNode(path=path)
        else:
            return

    def load(self, context: ComponentLoadContext) -> DefsFactoryModuleResolver:
        module = load_module_from_path(self.path.stem, self.path / "component.py")
        defs_modules_in_module = inspect.getmembers(module, is_defs_module)

        if len(defs_modules_in_module) < 1:
            raise DagsterInvalidDefinitionError("No defs modules found in python module")
        elif len(defs_modules_in_module) > 1:
            # note: we could support defs modules in the same file, just
            # being more restrictive to start
            raise DagsterInvalidDefinitionError(
                f"Multiple defs modules found in python module: {defs_modules_in_module}"
            )
        else:
            defs_module = check.inst(defs_modules_in_module[0][1], DefsModule)

            return DefsFactoryModuleResolver(
                path=self.path,
                context=context,
                defs_factory=defs_module.create_defs_loader(context),
                defs_module=defs_module,
            )


@record
class DirectForTestComponentDeclNode(DefsModuleDeclNode):
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

    def load(self, context: ComponentLoadContext):
        context = context.with_rendering_scope(self.component_type.get_additional_scope())
        obj, tree = self._obj_and_tree
        attr_schema = check.not_none(
            self.component_type.get_schema(), "Component must have schema for direct test"
        )
        with enrich_validation_errors_with_source_position(tree, []):
            attributes = TypeAdapter(attr_schema).validate_python(obj)
        return [self.component_type.load(attributes, context)]
