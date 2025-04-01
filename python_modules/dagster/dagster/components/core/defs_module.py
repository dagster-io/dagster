import inspect
from abc import abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, TypeVar

from dagster_shared.serdes.objects import LibraryObjectKey
from dagster_shared.yaml_utils import parse_yaml_with_source_positions
from pydantic import BaseModel, ConfigDict, TypeAdapter

import dagster._check as check
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_module,
)
from dagster._core.definitions.module_loaders.utils import find_objects_in_module_of_types
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils import pushd
from dagster._utils.pydantic_yaml import (
    _parse_and_populate_model_with_annotated_errors,
    enrich_validation_errors_with_source_position,
)
from dagster.components.component.component import Component
from dagster.components.component.component_loader import is_component_loader
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.library_object import load_library_object
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.core_models import AssetPostProcessor

T = TypeVar("T", bound=BaseModel)


class ComponentFileModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    attributes: Optional[Mapping[str, Any]] = None


#########
# MODULES
#########


@dataclass
class DefsModuleComponent(Component):
    path: Path

    @classmethod
    def from_context(cls, context: ComponentLoadContext) -> Optional["DefsModuleComponent"]:
        # this defines the priority of the module types
        module_types = (
            WrappedYamlComponent,
            WrappedPythonicComponent,
            DagsterDefsComponent,
            DefsFolderComponent,
        )
        module_filter = filter(None, (cls.from_context(context) for cls in module_types))
        return next(module_filter, None)

    @classmethod
    def load(cls, attributes: Any, context: ComponentLoadContext) -> "DefsModuleComponent":
        return check.not_none(cls.from_context(context))


@dataclass
class DefsFolderComponentYamlSchema(Resolvable):
    asset_post_processors: Optional[Sequence[AssetPostProcessor]] = None


@dataclass
class DefsFolderComponent(DefsModuleComponent):
    """A folder containing multiple submodules."""

    submodules: Sequence[DefsModuleComponent]
    asset_post_processors: Optional[Sequence[AssetPostProcessor]]

    @classmethod
    def get_schema(cls):
        return DefsFolderComponentYamlSchema.model()

    @classmethod
    def load(cls, attributes: Any, context: ComponentLoadContext) -> "DefsFolderComponent":
        # doing this funky thing because some of our attributes are resolved from the context,
        # so we split up resolving the yaml-defined attributes and the context-defined attributes,
        # meaning we manually invoke the resolution system here
        resolved_attributes = DefsFolderComponentYamlSchema.resolve_from_model(
            context.resolution_context.at_path("attributes"),
            attributes,
        )
        submodules = check.not_none(cls.submodules_from_context(context))
        return DefsFolderComponent(
            path=context.path,
            submodules=submodules,
            asset_post_processors=resolved_attributes.asset_post_processors,
        )

    @classmethod
    def submodules_from_context(
        cls, context: ComponentLoadContext
    ) -> Optional[Sequence[DefsModuleComponent]]:
        if not context.path.is_dir():
            return None
        submodules = (
            DefsModuleComponent.from_context(context.for_path(subpath))
            for subpath in context.path.iterdir()
        )
        return list(filter(None, submodules))

    @classmethod
    def from_context(cls, context: ComponentLoadContext) -> Optional["DefsFolderComponent"]:
        submodules = cls.submodules_from_context(context)
        if submodules is None:
            return None
        return DefsFolderComponent(
            path=context.path, submodules=submodules, asset_post_processors=None
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        defs = Definitions.merge(
            *(
                submodule.build_defs(context.for_path(submodule.path))
                for submodule in self.submodules
            )
        )
        for post_processor in self.asset_post_processors or []:
            defs = post_processor(defs)
        return defs


@dataclass
class DagsterDefsComponent(DefsModuleComponent):
    """A module containing python dagster definitions."""

    @classmethod
    def from_context(cls, context: ComponentLoadContext) -> Optional["DagsterDefsComponent"]:
        if (context.path / "definitions.py").exists():
            return DagsterDefsComponent(path=context.path / "definitions.py")
        elif context.path.suffix == ".py":
            return DagsterDefsComponent(path=context.path)
        return None

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        module = context.load_defs_relative_python_module(self.path)
        definitions_objects = list(find_objects_in_module_of_types(module, Definitions))
        if len(definitions_objects) == 0:
            return load_definitions_from_module(module)
        elif len(definitions_objects) == 1:
            return next(iter(definitions_objects))
        else:
            raise DagsterInvalidDefinitionError(
                f"Found multiple Definitions objects in {self.path}. At most one Definitions object "
                "may be specified per module."
            )


@dataclass
class WrappedDefsModuleComponent(DefsModuleComponent):
    """A module containing a component definition."""

    wrapped: Component

    @staticmethod
    @abstractmethod
    def get_component_def_path(path: Path) -> Path: ...

    @classmethod
    @abstractmethod
    def get_component(cls, context: ComponentLoadContext) -> Component: ...

    @classmethod
    def from_context(cls, context: ComponentLoadContext) -> Optional["WrappedDefsModuleComponent"]:
        if cls.get_component_def_path(context.path).exists():
            return cls(path=context.path, wrapped=cls.get_component(context))
        return None

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return self.wrapped.build_defs(context)


@dataclass
class WrappedPythonicComponent(WrappedDefsModuleComponent):
    @staticmethod
    def get_component_def_path(path: Path) -> Path:
        return path / "component.py"

    @classmethod
    def get_component(cls, context) -> Component:
        module = context.load_defs_relative_python_module(cls.get_component_def_path(context.path))
        component_loaders = list(inspect.getmembers(module, is_component_loader))
        if len(component_loaders) == 0:
            raise DagsterInvalidDefinitionError("No component loaders found in module")
        elif len(component_loaders) == 1:
            _, component_loader = component_loaders[0]
            return WrappedPythonicComponent(path=context.path, wrapped=component_loader(context))
        else:
            raise DagsterInvalidDefinitionError(
                f"Multiple component loaders found in module: {component_loaders}"
            )


@dataclass
class WrappedYamlComponent(WrappedDefsModuleComponent):
    @staticmethod
    def get_component_def_path(path: Path) -> Path:
        return path / "component.yaml"

    @classmethod
    def get_component(cls, context: ComponentLoadContext) -> Component:
        # parse the yaml file
        component_def_path = cls.get_component_def_path(context.path)
        source_tree = parse_yaml_with_source_positions(
            component_def_path.read_text(), str(component_def_path)
        )
        component_file_model = _parse_and_populate_model_with_annotated_errors(
            cls=ComponentFileModel, obj_parse_root=source_tree, obj_key_path_prefix=[]
        )

        # find the component type
        type_str = context.normalize_component_type_str(component_file_model.type)
        key = LibraryObjectKey.from_typename(type_str)
        obj = load_library_object(key)
        if not isinstance(obj, type) or not issubclass(obj, Component):
            raise DagsterInvalidDefinitionError(
                f"Component type {type_str} is of type {type(obj)}, but must be a subclass of dagster.Component"
            )

        component_schema = obj.get_schema()
        context = context.with_rendering_scope(
            obj.get_additional_scope()
        ).with_source_position_tree(source_tree.source_position_tree)

        # grab the attributes from the yaml file
        with pushd(str(context.path)):
            if component_schema is None:
                attributes = None
            elif source_tree:
                attributes_position_tree = source_tree.source_position_tree.children["attributes"]
                with enrich_validation_errors_with_source_position(
                    attributes_position_tree, ["attributes"]
                ):
                    attributes = TypeAdapter(component_schema).validate_python(
                        component_file_model.attributes
                    )
            else:
                attributes = TypeAdapter(component_schema).validate_python(
                    component_file_model.attributes
                )

        return obj.load(attributes, context)
