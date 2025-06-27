import abc
import inspect
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import nullcontext
from functools import cached_property
from pathlib import Path
from typing import Generic, Optional, TypeVar, Union

from dagster_shared.serdes.objects import EnvRegistryKey
from dagster_shared.seven import load_module_object
from dagster_shared.yaml_utils import parse_yamls_with_source_position
from dagster_shared.yaml_utils.source_position import SourcePosition, ValueAndSourcePositionTree
from pydantic import BaseModel, TypeAdapter

import dagster._check as check
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.pydantic_yaml import (
    _parse_and_populate_model_with_annotated_errors,
    enrich_validation_errors_with_source_position,
)
from dagster.components.component.component import Component
from dagster.components.component.component_loader import is_component_loader
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.defs_module import (
    EXPLICITLY_IGNORED_GLOB_PATTERNS,
    ComponentFileModel,
    ComponentPath,
    CompositeComponent,
    CompositeYamlComponent,
    DagsterDefsComponent,
    DefsFolderComponent,
    asset_post_processor_list_from_post_processing_dict,
    context_with_injected_scope,
    find_defs_or_component_yaml,
)
from dagster.components.resolved.core_models import AssetPostProcessor

T = TypeVar("T", bound=Component)


class ComponentDecl(abc.ABC, Generic[T]):
    """Class representing a not-yet-loaded component in the defs hierarchy. In effect, a closure
    with all information needed to load the component. A tree of component decls is initially
    built before any components are loaded.
    """

    @abc.abstractmethod
    def _load_component(self) -> T:
        """Loads the component represented by this decl."""


class ComponentLoaderDecl(ComponentDecl[Component]):
    """Declaration of a component that is loaded by a user-defined Python function."""

    def __init__(
        self,
        context: ComponentLoadContext,
        component_node_fn: Callable[[ComponentLoadContext], Component],
    ):
        self.context = context
        self.component_node = component_node_fn

    def _load_component(self) -> Component:
        return self.component_node(self.context)


class CompositePythonDecl(ComponentDecl[CompositeComponent]):
    """Declaration of a Python CompositeComponent, corresponding to a Python file with one or more
    ComponentLoaderDecls.
    """

    def __init__(self, context: ComponentLoadContext, decls: Mapping[str, ComponentLoaderDecl]):
        self.context = context
        self.decls = decls

    def _load_component(self) -> "CompositeComponent":
        return CompositeComponent(
            components={attr: decl._load_component() for attr, decl in self.decls.items()}  # noqa: SLF001
        )


class YamlDecl(ComponentDecl):
    """Declaration of a single component loaded from a YAML file."""

    @staticmethod
    def from_source_tree(
        context: ComponentLoadContext,
        source_tree: ValueAndSourcePositionTree,
    ) -> "YamlDecl":
        component_file_model = _parse_and_populate_model_with_annotated_errors(
            cls=ComponentFileModel, obj_parse_root=source_tree, obj_key_path_prefix=[]
        )
        return YamlDecl(
            context=context, source_tree=source_tree, component_file_model=component_file_model
        )

    def __init__(
        self,
        context: ComponentLoadContext,
        source_tree: ValueAndSourcePositionTree,
        component_file_model: ComponentFileModel,
    ):
        self.context = context
        self.source_tree = source_tree
        self.component_file_model = component_file_model

    def _get_attributes_model(self, model_cls: Optional[type[BaseModel]]) -> Optional[BaseModel]:
        if model_cls is None or not self.source_tree or not self.component_file_model.attributes:
            return None

        attributes_position_tree = self.source_tree.source_position_tree.children.get(
            "attributes", None
        )
        with (
            enrich_validation_errors_with_source_position(attributes_position_tree, ["attributes"])
            if attributes_position_tree
            else nullcontext()
        ):
            return TypeAdapter(model_cls).validate_python(self.component_file_model.attributes)
        return None

    @cached_property
    def context_with_component_injected_scope(self) -> ComponentLoadContext:
        return context_with_injected_scope(
            self.context, self.component_cls, self.component_file_model.template_vars_module
        )

    @cached_property
    def component_cls(self) -> type[Component]:
        """The class of the component that is being loaded."""
        type_str = self.context.normalize_component_type_str(self.component_file_model.type)
        key = EnvRegistryKey.from_typename(type_str)
        obj = load_module_object(key.namespace, key.name)
        if not isinstance(obj, type) or not issubclass(obj, Component):
            raise DagsterInvalidDefinitionError(
                f"Component type {type_str} is of type {type(obj)}, but must be a subclass of dagster.Component"
            )
        return obj

    def _load_component(self) -> "Component":
        context = self.context_with_component_injected_scope

        context = context.with_source_position_tree(
            self.source_tree.source_position_tree,
        )

        model_cls = self.component_cls.get_model_cls()

        attributes = self._get_attributes_model(model_cls)

        return self.component_cls.load(attributes, context)

    def get_asset_post_processor_lists(self) -> list[AssetPostProcessor]:
        post_processing_position_tree = self.source_tree.source_position_tree.children.get(
            "post_processing", None
        )
        with (
            enrich_validation_errors_with_source_position(
                post_processing_position_tree, ["post_processing"]
            )
            if post_processing_position_tree
            else nullcontext()
        ):
            return asset_post_processor_list_from_post_processing_dict(
                self.context_with_component_injected_scope.resolution_context,
                self.component_file_model.post_processing,
            )


class YamlFileDecl(ComponentDecl[CompositeYamlComponent]):
    """Declaration of a CompositeYamlComponent, corresponding to a YAML file with one or more
    YamlDecls.
    """

    def __init__(
        self,
        context: ComponentLoadContext,
        decls: Sequence[YamlDecl],
        source_positions: Sequence[SourcePosition],
    ):
        self.context = context
        self.decls = decls
        self.source_positions = source_positions

    def _load_component(self) -> "CompositeYamlComponent":
        return CompositeYamlComponent(
            components=[decl._load_component() for decl in self.decls],  # noqa: SLF001
            source_positions=self.source_positions,
            asset_post_processor_lists=[
                decl.get_asset_post_processor_lists() for decl in self.decls
            ],
        )


class DagsterDefsDecl(ComponentDecl[DagsterDefsComponent]):
    def __init__(self, context: ComponentLoadContext, path: Path):
        self.path = path

    def _load_component(self) -> DagsterDefsComponent:
        return DagsterDefsComponent(path=self.path)


class DefsFolderDecl(ComponentDecl[DefsFolderComponent]):
    def __init__(
        self, context: ComponentLoadContext, path: Path, children: Mapping[Path, ComponentDecl]
    ):
        self.path = path
        self.children = children

    @classmethod
    def get(cls, context: ComponentLoadContext) -> "DefsFolderDecl":
        component = get_component_decl(context)
        return check.inst(
            component,
            DefsFolderDecl,
            f"Expected DefsFolderDecl at {context.path}, got {component}.",
        )

    def _load_component(self) -> "DefsFolderComponent":
        return DefsFolderComponent(
            path=self.path,
            children={subpath: decl._load_component() for subpath, decl in self.children.items()},  # noqa: SLF001
        )

    def iterate_component_decls(self) -> Iterator[ComponentDecl]:
        for _, component in self.iterate_path_component_decl_pairs():
            yield component

    def iterate_path_component_decl_pairs(
        self,
    ) -> Iterator[tuple[ComponentPath, ComponentDecl]]:
        for path, component_node in self.children.items():
            yield ComponentPath(file_path=path), component_node

            if isinstance(component_node, DefsFolderDecl):
                yield from component_node.iterate_path_component_decl_pairs()

            if isinstance(component_node, YamlFileDecl):
                for idx, inner_comp in enumerate(component_node.decls):
                    yield ComponentPath(file_path=path, instance_key=idx), inner_comp

            if isinstance(component_node, CompositePythonDecl):
                for attr, inner_comp in component_node.decls.items():
                    yield ComponentPath(file_path=path, instance_key=attr), inner_comp


def get_component_decl(context: ComponentLoadContext) -> Optional[ComponentDecl]:
    """Attempts to determine the type of component that should be loaded for the given context.  Iterates through potential component
    type matches, prioritizing more specific types: YAML, Python, plain Dagster defs, and component
    folder.
    """
    # in priority order
    # yaml component
    if find_defs_or_component_yaml(context.path):
        return load_yaml_component_decl(context)
    # pythonic component
    elif (
        context.terminate_autoloading_on_keyword_files and (context.path / "component.py").exists()
    ):
        return get_component_decl_from_python_file(context)
    # defs
    elif (
        context.terminate_autoloading_on_keyword_files
        and (context.path / "definitions.py").exists()
    ):
        return DagsterDefsDecl(context=context, path=context.path / "definitions.py")
    elif context.path.suffix == ".py":
        return DagsterDefsDecl(context=context, path=context.path)
    # folder
    elif context.path.is_dir():
        children = find_component_decls_from_context(context)
        if children:
            return DefsFolderDecl(
                context=context,
                path=context.path,
                children=children,
            )

    return None


def find_component_decls_from_context(
    context: ComponentLoadContext,
) -> Mapping[Path, ComponentDecl]:
    found = {}
    for subpath in context.path.iterdir():
        relative_subpath = subpath.relative_to(context.path)
        if any(relative_subpath.match(pattern) for pattern in EXPLICITLY_IGNORED_GLOB_PATTERNS):
            continue
        component_node = get_component_decl(context.for_path(subpath))
        if component_node:
            found[subpath] = component_node
    return found


def get_component_decl_from_python_file(
    context: ComponentLoadContext,
) -> Union[ComponentLoaderDecl, CompositePythonDecl]:
    # backcompat for component.yaml
    component_def_path = context.path / "component.py"
    module = context.load_defs_relative_python_module(component_def_path)
    component_loaders = list(inspect.getmembers(module, is_component_loader))
    if len(component_loaders) == 0:
        raise DagsterInvalidDefinitionError("No component nodes found in module")
    elif len(component_loaders) == 1:
        _, component_loader = component_loaders[0]
        return ComponentLoaderDecl(context=context, component_node_fn=component_loader)
    else:
        return CompositePythonDecl(
            context=context,
            decls={
                attr: ComponentLoaderDecl(context=context, component_node_fn=component_loader)
                for attr, component_loader in component_loaders
            },
        )


def load_yaml_component_decl(context: ComponentLoadContext) -> ComponentDecl:
    component_def_path = check.not_none(find_defs_or_component_yaml(context.path))
    return get_component_decl_from_yaml_file(context=context, component_def_path=component_def_path)


def get_component_decl_from_yaml_file(
    context: ComponentLoadContext, component_def_path: Path
) -> ComponentDecl:
    source_trees = parse_yamls_with_source_position(
        component_def_path.read_text(), str(component_def_path)
    )
    component_nodes = []
    for source_tree in source_trees:
        component_nodes.append(YamlDecl.from_source_tree(context=context, source_tree=source_tree))

    check.invariant(len(component_nodes) > 0, "No components found in YAML file")
    return YamlFileDecl(
        context=context,
        decls=component_nodes,
        source_positions=[
            source_tree.source_position_tree.position for source_tree in source_trees
        ],
    )
