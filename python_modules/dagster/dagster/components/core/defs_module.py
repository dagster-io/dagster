import importlib
import inspect
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, TypeVar, Union

from dagster_shared.record import record
from dagster_shared.serdes.objects import PluginObjectKey
from dagster_shared.yaml_utils import parse_yamls_with_source_position
from dagster_shared.yaml_utils.source_position import SourcePosition
from pydantic import BaseModel, ConfigDict, TypeAdapter

import dagster._check as check
from dagster._annotations import preview, public
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.metadata import ArbitraryMetadataMapping
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataSet,
    CodeReferencesMetadataValue,
)
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
from dagster.components.component.template_vars import find_inline_template_vars_in_module
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.package_entry import load_package_object
from dagster.components.definitions import LazyDefinitions
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
    template_vars_module: Optional[str] = None
    requirements: Optional[ComponentRequirementsModel] = None


def _add_defs_yaml_metadata(
    component_yaml_path: Path,
    load_context: ComponentLoadContext,
    component: Component,
    source_position: SourcePosition,
    metadata: ArbitraryMetadataMapping,
) -> ArbitraryMetadataMapping:
    existing_references_meta = CodeReferencesMetadataSet.extract(metadata)

    references = (
        existing_references_meta.code_references.code_references
        if existing_references_meta.code_references
        else []
    )
    references_to_add = component.get_code_references_for_yaml(
        component_yaml_path, source_position, load_context
    )

    return {
        **metadata,
        **CodeReferencesMetadataSet(
            code_references=CodeReferencesMetadataValue(
                code_references=[
                    *references,
                    *references_to_add,
                ],
            )
        ),
        "dagster/component_origin": component,
        # maybe ComponentPath.get_relative_key too
    }


class CompositeYamlComponent(Component):
    def __init__(self, components: Sequence[Component], source_positions: Sequence[SourcePosition]):
        self.components = components
        self.source_positions = source_positions

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        component_yaml = check.not_none(_find_defs_or_component_yaml(context.path))

        return Definitions.merge(
            *(
                component.build_defs(context).with_definition_metadata_update(
                    lambda metadata: _add_defs_yaml_metadata(
                        component_yaml_path=component_yaml,
                        load_context=context,
                        component=component,
                        source_position=source_position,
                        metadata=metadata,
                    )
                )
                for component, source_position in zip(self.components, self.source_positions)
            )
        )


class CompositeComponent(Component):
    def __init__(self, components: Mapping[str, Component]):
        self.components = components

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions.merge(
            *[component.build_defs(context) for component in self.components.values()]
        )


def get_component(context: ComponentLoadContext) -> Optional[Component]:
    """Attempts to load a component from the given context. Iterates through potential component
    type matches, prioritizing more specific types: YAML, Python, plain Dagster defs, and component
    folder.
    """
    # in priority order
    # yaml component
    if _find_defs_or_component_yaml(context.path):
        return load_yaml_component(context)
    # pythonic component
    elif (
        context.terminate_autoloading_on_keyword_files and (context.path / "component.py").exists()
    ):
        return load_pythonic_component(context)
    # defs
    elif (
        context.terminate_autoloading_on_keyword_files
        and (context.path / "definitions.py").exists()
    ):
        return DagsterDefsComponent(path=context.path / "definitions.py")
    elif context.path.suffix == ".py":
        return DagsterDefsComponent(path=context.path)
    # folder
    elif context.path.is_dir():
        children = find_components_from_context(context)
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


@record
class ComponentPath:
    """Identifier for where a Component instance was defined:
    file_path: The Path to the file or directory relative to the root defs module.
    instance_key: The optional identifier to distinguish instances originating from the same file.
    """

    file_path: Path
    instance_key: Optional[Union[int, str]] = None

    def get_relative_key(self, parent_path: Path):
        key = self.file_path.relative_to(parent_path).as_posix()

        if self.instance_key is not None:
            return f"{key}[{self.instance_key}]"

        return key


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
            children=find_components_from_context(context),
            asset_post_processors=resolved_attributes.asset_post_processors,
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        child_defs = []
        for path, child in self.children.items():
            child_defs.append(child.build_defs(context.for_path(path)))
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
        for _, component in self.iterate_path_component_pairs():
            yield component

    def iterate_path_component_pairs(self) -> Iterator[tuple[ComponentPath, Component]]:
        for path, component in self.children.items():
            yield ComponentPath(file_path=path), component

            if isinstance(component, DefsFolderComponent):
                yield from component.iterate_path_component_pairs()

            if isinstance(component, CompositeYamlComponent):
                for idx, inner_comp in enumerate(component.components):
                    yield ComponentPath(file_path=path, instance_key=idx), inner_comp

            if isinstance(component, CompositeComponent):
                for attr, inner_comp in component.components.items():
                    yield ComponentPath(file_path=path, instance_key=attr), inner_comp


EXPLICITLY_IGNORED_GLOB_PATTERNS = [
    "__pycache__",
    ".*/",
]


def find_components_from_context(context: ComponentLoadContext) -> Mapping[Path, Component]:
    found = {}
    for subpath in context.path.iterdir():
        relative_subpath = subpath.relative_to(context.path)
        if any(relative_subpath.match(pattern) for pattern in EXPLICITLY_IGNORED_GLOB_PATTERNS):
            continue
        component = get_component(context.for_path(subpath))
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

        def_objects = check.is_list(
            list(find_objects_in_module_of_types(module, Definitions)), Definitions
        )
        lazy_def_objects = check.is_list(
            list(find_objects_in_module_of_types(module, LazyDefinitions)), LazyDefinitions
        )

        if lazy_def_objects and def_objects:
            raise DagsterInvalidDefinitionError(
                f"Found both @definitions-decorated functions and Definitions objects in {self.path}. "
                "At most one may be specified per module."
            )

        if len(def_objects) == 1:
            return next(iter(def_objects))

        if len(def_objects) > 1:
            raise DagsterInvalidDefinitionError(
                f"Found multiple Definitions objects in {self.path}. At most one Definitions object "
                "may be specified per module."
            )

        if len(lazy_def_objects) == 1:
            lazy_def = next(iter(lazy_def_objects))
            return lazy_def(context)

        if len(lazy_def_objects) > 1:
            return Definitions.merge(*[lazy_def(context) for lazy_def in lazy_def_objects])

        return load_definitions_from_module(module)


def load_pythonic_component(context: ComponentLoadContext) -> Component:
    # backcompat for component.yaml
    component_def_path = context.path / "component.py"
    module = context.load_defs_relative_python_module(component_def_path)
    component_loaders = list(inspect.getmembers(module, is_component_loader))
    if len(component_loaders) == 0:
        raise DagsterInvalidDefinitionError("No component loaders found in module")
    elif len(component_loaders) == 1:
        _, component_loader = component_loaders[0]
        return component_loader(context)
    else:
        return CompositeComponent(
            {attr: component_loader(context) for attr, component_loader in component_loaders}
        )


def invoke_inline_template_var(context: ComponentLoadContext, tv: Callable) -> Any:
    sig = inspect.signature(tv)
    if len(sig.parameters) == 1:
        return tv(context)
    elif len(sig.parameters) == 0:
        return tv()
    else:
        raise ValueError(f"Template var must have 0 or 1 parameters, got {len(sig.parameters)}")


def context_with_injected_scope(
    context: ComponentLoadContext,
    component_cls: type[Component],
    template_vars_module: Optional[str],
) -> ComponentLoadContext:
    context = context.with_rendering_scope(
        component_cls.get_additional_scope(),
    )

    if not template_vars_module:
        return context

    absolute_template_vars_module = (
        f"{context.defs_relative_module_name(context.path)}{template_vars_module}"
        if template_vars_module.startswith(".")
        else template_vars_module
    )

    module = importlib.import_module(absolute_template_vars_module)

    template_var_fns = find_inline_template_vars_in_module(module)

    if not template_var_fns:
        raise DagsterInvalidDefinitionError(
            f"No template vars found in module {absolute_template_vars_module}"
        )

    return context.with_rendering_scope(
        {
            **{
                name: invoke_inline_template_var(context, tv)
                for name, tv in template_var_fns.items()
            },
        },
    )


def load_yaml_component(context: ComponentLoadContext) -> Component:
    # parse the yaml file
    component_def_path = check.not_none(_find_defs_or_component_yaml(context.path))
    return load_yaml_component_from_path(context, component_def_path)


def load_yaml_component_from_path(context: ComponentLoadContext, component_def_path: Path):
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

        context = context_with_injected_scope(
            context, obj, component_file_model.template_vars_module
        )

        context = context.with_source_position_tree(
            source_tree.source_position_tree,
        )

        model_cls = obj.get_model_cls()

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
    return CompositeYamlComponent(
        components, [source_tree.source_position_tree.position for source_tree in source_trees]
    )


# When we remove component.yaml, we can remove this function for just a defs.yaml check
def _find_defs_or_component_yaml(path: Path) -> Optional[Path]:
    # Check for defs.yaml has precedence, component.yaml is deprecated
    return next(
        (p for p in (path / "defs.yaml", path / "component.yaml") if p.exists()),
        None,
    )
