import importlib
import inspect
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, TypeVar, Union

from dagster_shared.record import record, replace
from dagster_shared.yaml_utils.source_position import SourcePosition
from pydantic import BaseModel, ConfigDict, TypeAdapter

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.metadata import ArbitraryMetadataMapping
from dagster._core.definitions.metadata.metadata_value import ObjectMetadataValue
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataSet,
    CodeReferencesMetadataValue,
)
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_module,
)
from dagster._core.definitions.module_loaders.utils import find_objects_in_module_of_types
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster.components.component.component import Component
from dagster.components.component.template_vars import (
    find_inline_template_vars_in_module,
    get_context_aware_static_template_vars,
)
from dagster.components.core.context import ComponentDeclLoadContext, ComponentLoadContext
from dagster.components.definitions import LazyDefinitions
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetPostProcessor, post_process_defs
from dagster.components.resolved.model import Model

if TYPE_CHECKING:
    from dagster.components.core.decl import ComponentDecl

T = TypeVar("T", bound=BaseModel)

ResolvableToComponentPath = Union[Path, "ComponentPath", str]


class ComponentRequirementsModel(BaseModel):
    """Describes dependencies for a component to load."""

    env: Optional[list[str]] = None


class ComponentPostProcessingModel(Resolvable, Model):
    assets: Optional[Sequence[AssetPostProcessor]] = None


class ComponentFileModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    attributes: Optional[Mapping[str, Any]] = None
    template_vars_module: Optional[str] = None
    requirements: Optional[ComponentRequirementsModel] = None
    post_processing: Optional[Mapping[str, Any]] = None


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
        "dagster/component_origin": ObjectMetadataValue(component),
        # maybe ComponentPath.get_relative_key too
    }


def _add_defs_py_metadata(
    component: Component,
    metadata: ArbitraryMetadataMapping,
):
    return {
        **metadata,
        "dagster/component_origin": ObjectMetadataValue(component),
    }


class CompositeYamlComponent(Component):
    def __init__(
        self,
        components: Sequence[Component],
        source_positions: Sequence[SourcePosition],
        asset_post_processor_lists: Sequence[Sequence[AssetPostProcessor]],
    ):
        self.components = components
        self.source_positions = source_positions
        check.invariant(
            len(components) == len(asset_post_processor_lists),
            "Number of components and post processors must match",
        )

        self.asset_post_processors_list = asset_post_processor_lists

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        component_yaml = check.not_none(find_defs_or_component_yaml(context.path))

        defs_list = []
        for component_decl, component, source_position, asset_post_processors in zip(
            context.component_decl.iterate_child_component_decls(),
            self.components,
            self.source_positions,
            self.asset_post_processors_list,
        ):
            defs_list.append(
                post_process_defs(
                    context.build_defs_at_path(component_decl.path).with_definition_metadata_update(
                        lambda metadata: _add_defs_yaml_metadata(
                            component_yaml_path=component_yaml,
                            load_context=context,
                            component=component,
                            source_position=source_position,
                            metadata=metadata,
                        )
                    ),
                    list(asset_post_processors),
                )
            )

        return Definitions.merge(*defs_list)


@record
class ComponentPath:
    """Identifier for where a Component instance was defined:
    file_path_posix: The absolute path to the file or directory.
    instance_key: The optional identifier to distinguish instances originating from the same file.
    """

    file_path_posix: str
    instance_key: Optional[Union[int, str]] = None

    @property
    def file_path(self) -> Path:
        return Path(self.file_path_posix)

    @staticmethod
    def from_resolvable(root_path: Path, path: ResolvableToComponentPath) -> "ComponentPath":
        if isinstance(path, ComponentPath):
            return path
        path = Path(path)
        normalized_path = (root_path / path) if not path.is_absolute() else path
        return ComponentPath.from_path(path=normalized_path, instance_key=None)

    @staticmethod
    def from_path(path: Path, instance_key: Optional[Union[int, str]] = None) -> "ComponentPath":
        check.param_invariant(path.is_absolute(), "Path must be absolute")
        return ComponentPath(file_path_posix=path.as_posix(), instance_key=instance_key)

    def without_instance_key(self) -> "ComponentPath":
        return replace(self, instance_key=None)

    def get_relative_key(self, parent_path: Path):
        key = self.file_path.relative_to(parent_path).as_posix()

        if self.instance_key is not None:
            return f"{key}[{self.instance_key}]"

        return key


def get_component(context: ComponentLoadContext) -> Optional[Component]:
    """Attempts to load a component from the given context. Iterates through potential component
    type matches, prioritizing more specific types: YAML, Python, plain Dagster defs, and component
    folder.
    """
    from dagster.components.core.decl import build_component_decl_from_context

    component_decl = build_component_decl_from_context(context)
    if component_decl:
        return context.load_structural_component_at_path(component_decl.path)
    return None


@dataclass
class DefsFolderComponentYamlSchema(Resolvable): ...


@public
@public
@dataclass
class DefsFolderComponent(Component):
    """A component that represents a directory containing multiple Dagster definition modules.

    DefsFolderComponent serves as a container for organizing and managing multiple subcomponents
    within a folder structure. It automatically discovers and loads components from subdirectories
    and files, enabling hierarchical organization of Dagster definitions. This component also
    supports post-processing capabilities to modify metadata and properties of definitions
    created by its child components.

    Key Features:
    - **Post-Processing**: Allows modification of child component definitions via configuration
    - **Automatic Discovery**: Recursively finds and loads components from subdirectories
    - **Hierarchical Organization**: Enables nested folder structures for complex projects

    The component automatically scans its directory for:
    - YAML component definitions (``defs.yaml`` files)
    - Python modules containing Dagster definitions
    - Nested subdirectories containing more components

    Here is how a DefsFolderComponent is used in a project by the framework, along
    with other framework-defined classes.

    .. code-block:: text

        my_project/
        └── defs/
            ├── analytics/             # DefsFolderComponent
            │   ├── defs.yaml          # Post-processing configuration
            │   ├── user_metrics/      # User-defined component
            │   │   └── defs.yaml
            │   └── sales_reports/     # User-defined component
            │       └── defs.yaml
            └── data_ingestion/        # DefsFolderComponent
                ├── api_sources/       # DefsFolderComponent
                │   └── some_defs.py   # PythonFileComponent
                └── file_sources/      # DefsFolderComponent
                    └── files.py       # PythonFileComponent

    Args:
        path: The filesystem path to the directory containing child components.
        children: A mapping of child paths to their corresponding Component instances.
            This is typically populated automatically during component discovery.


    DefsFolderComponent supports post-processing through its ``defs.yaml`` configuration,
    allowing you to modify definitions created by child components using target selectors

    Examples:
        Using post-processing in a folder's ``defs.yaml``:

        .. code-block:: yaml

            # analytics/defs.yaml
            type: dagster.DefsFolderComponent
            post_processing:
              assets:
                - target: "*" # add a top level tag to all assets in the folder
                  attributes:
                    tags:
                      top_level_tag: "true"
                - target: "tag:defs_tag=true" # add a tag to all assets in the folder with the tag "defs_tag"
                  attributes:
                    tags:
                      new_tag: "true"


    Please see documentation on post processing and the selection syntax for more examples.

    Component Discovery:

    The component automatically discovers children using these patterns:

    1. **YAML Components**: Subdirectories with ``defs.yaml`` files
    2. **Python Modules**: Any ``.py`` files containing Dagster definitions
    3. **Nested Folders**: Subdirectories that contain any of the above


    Files and directories matching these patterns are ignored:
    - ``__pycache__`` directories
    - Hidden directories (starting with ``.``)

    .. note::

        DefsFolderComponent instances are typically created automatically by Dagster's
        component loading system. Manual instantiation is rarely needed unless building
        custom loading logic or testing scenarios.

        When used with post-processing, the folder's ``defs.yaml`` should only contain
        post-processing configuration, not component type definitions.

    """

    path: Path
    children: Mapping[Path, Component]

    @classmethod
    def get_decl_type(cls) -> type["ComponentDecl"]:
        from dagster.components.core.decl import DefsFolderDecl

        return DefsFolderDecl

    @classmethod
    def get_model_cls(cls):
        return DefsFolderComponentYamlSchema.model()

    @classmethod
    def load(cls, attributes: Any, context: ComponentLoadContext) -> "DefsFolderComponent":
        return DefsFolderComponent(
            path=context.path,
            children=find_components_from_context(context),
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        child_defs = [
            context.build_defs_at_path(child_decl.path)
            for child_decl in context.component_decl.iterate_child_component_decls()
        ]
        return Definitions.merge(*child_defs)

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
            yield ComponentPath.from_path(path), component

            if isinstance(component, DefsFolderComponent):
                yield from component.iterate_path_component_pairs()

            if isinstance(component, CompositeYamlComponent):
                for idx, inner_comp in enumerate(component.components):
                    yield ComponentPath.from_path(path, idx), inner_comp

            if isinstance(component, PythonFileComponent):
                for attr, inner_comp in component.components.items():
                    yield ComponentPath.from_path(path, attr), inner_comp


EXPLICITLY_IGNORED_GLOB_PATTERNS = [
    "__pycache__",
    ".*/",
]


def find_components_from_context(context: ComponentLoadContext) -> Mapping[Path, Component]:
    found = {}
    for subpath in sorted(context.path.iterdir()):
        relative_subpath = subpath.relative_to(context.path)
        if any(relative_subpath.match(pattern) for pattern in EXPLICITLY_IGNORED_GLOB_PATTERNS):
            continue
        component = get_component(
            context.for_component_path(ComponentPath(file_path_posix=subpath.absolute().as_posix()))
        )
        if component:
            found[subpath] = component
    return found


@dataclass
class PythonFileComponent(Component):
    """A Python module containing Dagster definitions or Pythonic
    components. Used for implicit loading of Dagster definitions from
    Python files in the defs folder.
    """

    path: Path
    components: Mapping[str, Component]

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        from dagster.components.core.decl import PythonFileDecl

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

        decl = check.inst(context.component_decl, PythonFileDecl)
        return Definitions.merge(
            *[
                context.build_defs_at_path(child_decl.path).with_definition_metadata_update(
                    lambda metadata: _add_defs_py_metadata(
                        component=self.components[attr],
                        metadata=metadata,
                    )
                )
                for attr, child_decl in decl.decls.items()
            ],
            load_definitions_from_module(module),
        )


def invoke_inline_template_var(context: ComponentDeclLoadContext, tv: Callable) -> Any:
    sig = inspect.signature(tv)
    if len(sig.parameters) == 1:
        return tv(context)
    elif len(sig.parameters) == 0:
        return tv()
    else:
        raise ValueError(f"Template var must have 0 or 1 parameters, got {len(sig.parameters)}")


def load_yaml_component_from_path(context: ComponentLoadContext, component_def_path: Path):
    from dagster.components.core.decl import build_component_decl_from_yaml_file

    decl = build_component_decl_from_yaml_file(context, component_def_path)
    return context.load_structural_component_at_path(decl.path)


# When we remove component.yaml, we can remove this function for just a defs.yaml check
def find_defs_or_component_yaml(path: Path) -> Optional[Path]:
    # Check for defs.yaml has precedence, component.yaml is deprecated
    return next(
        (p for p in (path / "defs.yaml", path / "component.yaml") if p.exists()),
        None,
    )


T = TypeVar("T", bound=ComponentDeclLoadContext)


def context_with_injected_scope(
    context: T,
    component_cls: type[Component],
    template_vars_module: Optional[str],
) -> T:
    # Merge backward-compatible get_additional_scope with context-aware static template vars

    legacy_scope = component_cls.get_additional_scope()
    context_aware_scope = get_context_aware_static_template_vars(component_cls, context)

    # Merge scopes, with context-aware taking precedence
    merged_scope = {**legacy_scope, **context_aware_scope}

    context = context.with_rendering_scope(merged_scope)

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


def asset_post_processor_list_from_post_processing_dict(
    resolution_context: ResolutionContext, post_processing: Optional[Mapping[str, Any]]
) -> list[AssetPostProcessor]:
    if not post_processing:
        return []

    post_processing_model = ComponentPostProcessingModel.resolve_from_model(
        context=resolution_context,
        model=TypeAdapter(ComponentPostProcessingModel.model()).validate_python(post_processing),
    )
    return list(post_processing_model.assets or [])
