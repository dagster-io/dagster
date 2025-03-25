import inspect
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from functools import cached_property
from pathlib import Path
from types import ModuleType
from typing import Any, Optional, TypeVar

import dagster._check as check
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
from typing_extensions import Self

from dagster_components.component.component import Component
from dagster_components.core.context import ComponentLoadContext
from dagster_components.core.defs_module.defs_loader import DefsLoader
from dagster_components.core.defs_module.defs_module import (
    BuilderDefsModule,
    DefsModule,
    PythonDefsModule,
    SubpackageDefsModule,
)
from dagster_components.core.library_object import load_library_object

T = TypeVar("T", bound=BaseModel)


class ComponentFileModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    attributes: Optional[Mapping[str, Any]] = None


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
class DefsModuleLoader(ABC):
    path: Path

    def get_source_position_tree(self) -> Optional[SourcePositionTree]:
        return None

    @classmethod
    def from_path(cls, path: Path) -> Optional["DefsModuleLoader"]:
        # this defines the priority of the decl types, we return the first one that matches
        decltypes = (
            YamlComponentDecl,
            PythonComponentDecl,
            PythonModuleDecl,
            SubpackageDefsModuleDecl,
        )
        decl_filter = filter(None, (t.from_path(path) for t in decltypes))
        return next(decl_filter, None)

    @staticmethod
    def from_module(module: ModuleType) -> Optional["DefsModuleLoader"]:
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
        return DefsModuleLoader.from_path(
            check.not_none(module_path, f"Module {module.__name__} has no filepath")
        )

    @abstractmethod
    def load(self, context: ComponentLoadContext) -> DefsModule: ...


@record
class SubpackageDefsModuleDecl(DefsModuleLoader):
    """A folder containing multiple submodules."""

    subdecls: Sequence[DefsModuleLoader]

    @classmethod
    def from_path(cls, path: Path) -> Optional["SubpackageDefsModuleDecl"]:
        if path.is_dir():
            subdecls = (DefsModuleLoader.from_path(subpath) for subpath in path.iterdir())
            return cls(path=path, subdecls=list(filter(None, subdecls)))
        else:
            return None

    def load(self, context: ComponentLoadContext) -> SubpackageDefsModule:
        return SubpackageDefsModule(
            path=self.path,
            submodules=[decl.load(context.for_decl(decl)) for decl in self.subdecls],
        )


@record
class PythonModuleDecl(DefsModuleLoader):
    """A python module containing a `definitions.py` file."""

    path: Path

    @classmethod
    def from_path(cls, path: Path) -> Optional["PythonModuleDecl"]:
        if (path / "definitions.py").exists() or path.suffix == ".py":
            return cls(path=path)
        else:
            return None

    def load(self, context: ComponentLoadContext) -> PythonDefsModule:
        if self.path.is_dir():
            module = context.load_defs_relative_python_module(self.path / "definitions.py")
        else:
            module = context.load_defs_relative_python_module(self.path)
        return PythonDefsModule(path=self.path, module=module)


@record
class YamlComponentDecl(DefsModuleLoader):
    """A component configured with a `component.yaml` file."""

    component_file_model: ComponentFileModel
    source_position_tree: Optional[SourcePositionTree] = None

    @classmethod
    def from_path(cls, path: Path) -> Optional["YamlComponentDecl"]:
        if (path / "component.yaml").exists():
            position_tree, component_file_model = _parse_component_yaml(path)
            return cls(
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

    def load(self, context: ComponentLoadContext) -> BuilderDefsModule:
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
        return BuilderDefsModule(path=self.path, inner=component)


@record
class PythonBuilderDecl(DefsModuleLoader):
    """A DefsBuilder configured with a `defs.py` file."""

    @classmethod
    def _path(cls, path: Path) -> Path:
        return path / "defs.py"

    @classmethod
    def from_path(cls, path: Path) -> Optional[Self]:
        if cls._path(path).exists():
            return cls(path=path)
        else:
            return None

    def load(self, context: ComponentLoadContext) -> BuilderDefsModule:
        module = context.load_defs_relative_python_module(self._path(self.path))
        defs_loaders = list(inspect.getmembers(module, lambda x: isinstance(x, DefsLoader)))
        if len(defs_loaders) < 1:
            raise DagsterInvalidDefinitionError("No defs modules found in module")
        elif len(defs_loaders) > 1:
            raise DagsterInvalidDefinitionError(
                f"Multiple defs loaders found in module {module.__name__}: {[name for name, _ in defs_loaders]}"
            )
        else:
            _, defs_loader = defs_loaders[0]
            return BuilderDefsModule(path=self.path, inner=defs_loader(context))


@record
class PythonComponentDecl(PythonBuilderDecl):
    """A component configured with a `component.py` file."""

    @classmethod
    def _path(cls, path: Path) -> Path:
        return path / "component.py"


@record
class DirectForTestComponentDecl(DefsModuleLoader):
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
