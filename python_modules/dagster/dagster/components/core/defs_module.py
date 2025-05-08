import inspect
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, TypeVar

from dagster_shared.serdes.objects import PluginObjectKey
from dagster_shared.yaml_utils import parse_yamls_with_source_position
from pydantic import BaseModel, ConfigDict, TypeAdapter

import dagster._check as check
from dagster._annotations import preview, public
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_module,
)
from dagster._core.definitions.module_loaders.utils import find_objects_in_module_of_types
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.pydantic_yaml import (
    _parse_and_populate_model_with_annotated_errors,
    enrich_validation_errors_with_source_position,
)
from dagster.components.component.component import Component
from dagster.components.component.component_loader import is_component_loader
from dagster.components.core.context import ComponentLoadContext, use_component_load_context
from dagster.components.core.package_entry import load_package_object
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.core_models import AssetPostProcessor

T = TypeVar("T", bound=BaseModel)


class ComponentRequirementsModel(BaseModel):
    """Describes dependencies for a component to load."""

    env: Optional[list[str]] = None


class ComponentFileModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    attributes: Optional[Mapping[str, Any]] = None
    requirements: Optional[ComponentRequirementsModel] = None


class CompositeYamlComponent(Component):
    def __init__(self, components: Sequence[Component]):
        self.components = components

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions.merge(*(component.build_defs(context) for component in self.components))


def get_component(context: ComponentLoadContext) -> Optional[Component]:
    """Attempts to load a component from the given context. Iterates through potential component
    type matches, prioritizing more specific types: YAML, Python, plain Dagster defs, and component
    folder.
    """
    # in priority order
    # yaml component
    if (context.path / "component.yaml").exists():
        return load_yaml_component(context)
    # pythonic component
    elif (context.path / "component.py").exists():
        return load_pythonic_component(context)
    # defs
    elif (context.path / "definitions.py").exists():
        return DagsterDefsComponent(path=context.path / "definitions.py")
    elif context.path.suffix == ".py":
        return DagsterDefsComponent(path=context.path)
    # folder
    elif context.path.is_dir():
        children = _crawl(context)
        if children:
            return DefsFolderComponent(
                path=context.path,
                children=children,
                asset_post_processors=None,
            )

    return None


@dataclass
class DefsFolderComponentYamlSchema(Resolvable):
    asset_post_processors: Optional[Sequence[AssetPostProcessor]] = None


@public
@preview(emit_runtime_warning=False)
@dataclass
class DefsFolderComponent(Component):
    """A folder which may contain multiple submodules, each
    which define components.

    Optionally enables postprocessing to modify the Dagster definitions
    produced by submodules.
    """

    path: Path
    children: Mapping[Path, Component]
    asset_post_processors: Optional[Sequence[AssetPostProcessor]]

    @classmethod
    def get_model_cls(cls):
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

        return DefsFolderComponent(
            path=context.path,
            children=_crawl(context),
            asset_post_processors=resolved_attributes.asset_post_processors,
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        child_defs = []
        for path, child in self.children.items():
            sub_ctx = context.for_path(path)
            with use_component_load_context(sub_ctx):
                child_defs.append(child.build_defs(sub_ctx))
        defs = Definitions.merge(*child_defs)
        for post_processor in self.asset_post_processors or []:
            defs = post_processor(defs)
        return defs

    @classmethod
    def get(cls, context: ComponentLoadContext) -> "DefsFolderComponent":
        component = get_component(context)
        return check.inst(
            component,
            DefsFolderComponent,
            f"Expected DefsFolderComponent at {context.path}, got {component}.",
        )

    def iterate_components(self) -> Iterator[Component]:
        for component in self.children.values():
            if isinstance(component, DefsFolderComponent):
                yield from component.iterate_components()

            yield component


def _crawl(context: ComponentLoadContext) -> Mapping[Path, Component]:
    found = {}
    for subpath in context.path.iterdir():
        sub_ctx = context.for_path(subpath)
        with use_component_load_context(sub_ctx):
            component = get_component(sub_ctx)
            if component:
                found[subpath] = component
    return found


@dataclass
class DagsterDefsComponent(Component):
    """A Python module containing Dagster definitions. Used for implicit loading of
    Dagster definitions from Python files in the defs folder.
    """

    path: Path

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


def load_pythonic_component(context: ComponentLoadContext) -> Component:
    module = context.load_defs_relative_python_module(context.path / "component.py")
    component_loaders = list(inspect.getmembers(module, is_component_loader))
    if len(component_loaders) == 0:
        raise DagsterInvalidDefinitionError("No component loaders found in module")
    elif len(component_loaders) == 1:
        _, component_loader = component_loaders[0]
        return component_loader(context)
    else:
        raise DagsterInvalidDefinitionError(
            f"Multiple component loaders found in module: {component_loaders}"
        )


def load_yaml_component(context: ComponentLoadContext) -> Component:
    # parse the yaml file
    component_def_path = context.path / "component.yaml"
    source_trees = parse_yamls_with_source_position(
        component_def_path.read_text(), str(component_def_path)
    )
    components = []
    for source_tree in source_trees:
        component_file_model = _parse_and_populate_model_with_annotated_errors(
            cls=ComponentFileModel, obj_parse_root=source_tree, obj_key_path_prefix=[]
        )

        # find the component type
        type_str = context.normalize_component_type_str(component_file_model.type)
        key = PluginObjectKey.from_typename(type_str)
        obj = load_package_object(key)
        if not isinstance(obj, type) or not issubclass(obj, Component):
            raise DagsterInvalidDefinitionError(
                f"Component type {type_str} is of type {type(obj)}, but must be a subclass of dagster.Component"
            )

        model_cls = obj.get_model_cls()
        context = context.with_rendering_scope(
            obj.get_additional_scope(),
        ).with_source_position_tree(
            source_tree.source_position_tree,
        )

        # grab the attributes from the yaml file
        if model_cls is None:
            attributes = None
        elif source_tree:
            attributes_position_tree = source_tree.source_position_tree.children["attributes"]
            with enrich_validation_errors_with_source_position(
                attributes_position_tree, ["attributes"]
            ):
                attributes = TypeAdapter(model_cls).validate_python(component_file_model.attributes)
        else:
            attributes = TypeAdapter(model_cls).validate_python(component_file_model.attributes)

        components.append(obj.load(attributes, context))

    check.invariant(len(components) > 0, "No components found in YAML file")
    if len(components) == 1:
        return components[0]
    else:
        return CompositeYamlComponent(components)
