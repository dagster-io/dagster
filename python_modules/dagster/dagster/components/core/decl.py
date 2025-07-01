import abc
import inspect
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import nullcontext
from functools import cached_property
from pathlib import Path
from typing import Generic, Optional, TypeVar, Union

from dagster_shared.record import record
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


@record
class ComponentDecl(abc.ABC, Generic[T]):
    """Class representing a not-yet-loaded component in the defs hierarchy. In effect, a closure
    with all information needed to load the component. A tree of component decls is initially
    built before any components are loaded.
    """

    path: ComponentPath

    @abc.abstractmethod
    def _load_component(self) -> T:
        """Loads the component represented by this decl."""
        ...

    def iterate_component_decls(self) -> Iterator["ComponentDecl"]:
        for _, component in self.iterate_path_component_decl_pairs():
            yield component

    def iterate_path_component_decl_pairs(
        self,
    ) -> Iterator[tuple[ComponentPath, "ComponentDecl"]]:
        yield self.path, self


@record
class ComponentLoaderDecl(ComponentDecl[Component]):
    """Declaration of a component that is loaded by a user-defined Python function."""

    context: ComponentLoadContext
    component_node_fn: Callable[[ComponentLoadContext], Component]

    def _load_component(self) -> Component:
        return self.component_node_fn(self.context)


@record
class CompositePythonDecl(ComponentDecl[CompositeComponent]):
    """Declaration of a Python CompositeComponent, corresponding to a Python file with one or more
    ComponentLoaderDecls.
    """

    context: ComponentLoadContext
    decls: Mapping[str, ComponentLoaderDecl]

    def _load_component(self) -> "CompositeComponent":
        return CompositeComponent(
            components={
                attr: self.context.load_component_at_path(decl.path)
                for attr, decl in self.decls.items()
            }
        )

    def iterate_path_component_decl_pairs(
        self,
    ) -> Iterator[tuple[ComponentPath, ComponentDecl]]:
        yield self.path, self
        for decl in self.decls.values():
            yield from decl.iterate_path_component_decl_pairs()


def _get_component_class(
    context: ComponentLoadContext, component_file_model: ComponentFileModel
) -> type[Component]:
    # TODO: lookup in cache so we don't have to import the class directly
    type_str = context.normalize_component_type_str(component_file_model.type)
    key = EnvRegistryKey.from_typename(type_str)
    obj = load_module_object(key.namespace, key.name)
    if not isinstance(obj, type) or not issubclass(obj, Component):
        raise DagsterInvalidDefinitionError(
            f"Component type {type_str} is of type {type(obj)}, but must be a subclass of dagster.Component"
        )

    return obj


def _process_attributes_with_enriched_validation_err(
    source_tree: Optional[ValueAndSourcePositionTree],
    component_file_model: Optional[ComponentFileModel],
    model_cls: Optional[type[BaseModel]],
) -> Optional[BaseModel]:
    if (
        model_cls is None
        or not source_tree
        or not component_file_model
        or not component_file_model.attributes
    ):
        return None

    attributes_position_tree = source_tree.source_position_tree.children.get("attributes", None)
    with (
        enrich_validation_errors_with_source_position(attributes_position_tree, ["attributes"])
        if attributes_position_tree
        else nullcontext()
    ):
        return TypeAdapter(model_cls).validate_python(component_file_model.attributes)
    return None


@record
class YamlBackedComponentDecl(ComponentDecl[T]):
    context: ComponentLoadContext
    source_tree: Optional[ValueAndSourcePositionTree]
    component_file_model: Optional[ComponentFileModel]

    @cached_property
    def context_with_component_injected_scope(self) -> ComponentLoadContext:
        if not self.component_file_model:
            return self.context
        return context_with_injected_scope(
            self.context,
            self.component_cls,
            self.component_file_model.template_vars_module,
        )

    @cached_property
    def component_cls(self) -> type[Component]:
        """The class of the component that is being loaded."""
        return _get_component_class(self.context, check.not_none(self.component_file_model))

    def get_asset_post_processor_lists(self) -> list[AssetPostProcessor]:
        if not self.source_tree or not self.component_file_model:
            return []

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


@record
class YamlDecl(YamlBackedComponentDecl):
    """Declaration of a single component loaded from a YAML file."""

    @staticmethod
    def from_source_tree(
        context: ComponentLoadContext,
        source_tree: ValueAndSourcePositionTree,
        path: ComponentPath,
    ) -> "YamlDecl":
        component_file_model = _parse_and_populate_model_with_annotated_errors(
            cls=ComponentFileModel, obj_parse_root=source_tree, obj_key_path_prefix=[]
        )
        return YamlDecl(
            context=context,
            source_tree=source_tree,
            component_file_model=component_file_model,
            path=path,
        )

    def _load_component(self) -> "Component":
        context = self.context_with_component_injected_scope.with_source_position_tree(
            check.not_none(self.source_tree).source_position_tree,
        )

        model_cls = self.component_cls.get_model_cls()

        attributes = _process_attributes_with_enriched_validation_err(
            self.source_tree, self.component_file_model, model_cls
        )

        return self.component_cls.load(attributes, context)


@record
class YamlFileDecl(ComponentDecl[CompositeYamlComponent]):
    """Declaration of a CompositeYamlComponent, corresponding to a YAML file with one or more
    YamlDecls.
    """

    context: ComponentLoadContext
    decls: Sequence[YamlBackedComponentDecl]
    source_positions: Sequence[SourcePosition]

    def _load_component(self) -> "CompositeYamlComponent":
        return CompositeYamlComponent(
            components=[self.context.load_component_at_path(decl.path) for decl in self.decls],
            source_positions=self.source_positions,
            asset_post_processor_lists=[
                decl.get_asset_post_processor_lists() for decl in self.decls
            ],
        )

    def iterate_path_component_decl_pairs(
        self,
    ) -> Iterator[tuple[ComponentPath, ComponentDecl]]:
        yield self.path, self
        for decl in self.decls:
            yield from decl.iterate_path_component_decl_pairs()


@record
class DagsterDefsDecl(ComponentDecl[DagsterDefsComponent]):
    context: ComponentLoadContext

    def _load_component(self) -> DagsterDefsComponent:
        return DagsterDefsComponent(path=self.path.file_path)


@record
class DefsFolderDecl(YamlBackedComponentDecl[DefsFolderComponent]):
    children: Mapping[Path, ComponentDecl]

    @classmethod
    def get(cls, context: ComponentLoadContext) -> "DefsFolderDecl":
        component = build_component_decl_from_context(context)
        return check.inst(
            component,
            DefsFolderDecl,
            f"Expected DefsFolderDecl at {context.path}, got {component}.",
        )

    def _load_component(self) -> "DefsFolderComponent":
        _process_attributes_with_enriched_validation_err(
            self.source_tree, self.component_file_model, DefsFolderComponent.get_model_cls()
        )
        return DefsFolderComponent(
            path=self.path.file_path,
            children={
                subpath: self.context.load_component_at_path(decl.path)
                for subpath, decl in self.children.items()
            },
        )

    def iterate_path_component_decl_pairs(
        self,
    ) -> Iterator[tuple[ComponentPath, ComponentDecl]]:
        yield self.path, self
        for component_node in self.children.values():
            yield from component_node.iterate_path_component_decl_pairs()


def build_component_decl_from_context(context: ComponentLoadContext) -> Optional[ComponentDecl]:
    """Attempts to determine the type of component that should be loaded for the given context.  Iterates through potential component
    type matches, prioritizing more specific types: YAML, Python, plain Dagster defs, and component
    folder.
    """
    # in priority order
    # yaml component
    if find_defs_or_component_yaml(context.path):
        return build_component_decl_from_yaml_file_backcompat(context)
    # pythonic component
    elif (
        context.terminate_autoloading_on_keyword_files and (context.path / "component.py").exists()
    ):
        return build_component_decl_from_python_file(context)
    # defs
    elif (
        context.terminate_autoloading_on_keyword_files
        and (context.path / "definitions.py").exists()
    ):
        return DagsterDefsDecl(
            context=context,
            path=ComponentPath(file_path=context.path / "definitions.py", instance_key=None),
        )
    elif context.path.suffix == ".py":
        return DagsterDefsDecl(
            context=context,
            path=ComponentPath(file_path=context.path, instance_key=None),
        )
    # folder
    elif context.path.is_dir():
        children = build_component_decls_from_directory_items(context, None)
        if children:
            return DefsFolderDecl(
                context=context,
                path=ComponentPath(file_path=context.path, instance_key=None),
                children=children,
                source_tree=None,
                component_file_model=None,
            )

    return None


def build_component_decls_from_directory_items(
    context: ComponentLoadContext, component_file_model: Optional[ComponentFileModel]
) -> Mapping[Path, ComponentDecl]:
    found = {}
    for subpath in context.path.iterdir():
        relative_subpath = subpath.relative_to(context.path)
        if any(relative_subpath.match(pattern) for pattern in EXPLICITLY_IGNORED_GLOB_PATTERNS):
            continue
        path_context = context_with_injected_scope(
            context,
            DefsFolderComponent,
            component_file_model.template_vars_module if component_file_model else None,
        ).for_path(subpath)

        component_node = build_component_decl_from_context(path_context)
        if component_node:
            found[subpath] = component_node
    return found


def build_component_decl_from_python_file(
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
        return ComponentLoaderDecl(
            context=context,
            component_node_fn=component_loader,
            path=ComponentPath(file_path=context.path, instance_key=None),
        )
    else:
        return CompositePythonDecl(
            path=ComponentPath(file_path=context.path, instance_key=None),
            context=context,
            decls={
                attr: ComponentLoaderDecl(
                    context=context,
                    component_node_fn=component_loader,
                    path=ComponentPath(file_path=context.path, instance_key=attr),
                )
                for attr, component_loader in component_loaders
            },
        )


def build_component_decl_from_yaml_file_backcompat(context: ComponentLoadContext) -> ComponentDecl:
    component_def_path = check.not_none(find_defs_or_component_yaml(context.path))
    return build_component_decl_from_yaml_file(
        context=context, component_def_path=component_def_path
    )


def build_component_decl_from_yaml_file(
    context: ComponentLoadContext, component_def_path: Path
) -> ComponentDecl:
    source_trees = parse_yamls_with_source_position(
        component_def_path.read_text(), str(component_def_path)
    )
    component_nodes = []
    for i, source_tree in enumerate(source_trees):
        component_nodes.append(
            build_component_decl_from_yaml_document(
                context=context,
                source_tree=source_tree,
                path=ComponentPath(file_path=context.path, instance_key=i),
            )
        )

    check.invariant(len(component_nodes) > 0, "No components found in YAML file")
    return YamlFileDecl(
        path=ComponentPath(file_path=context.path, instance_key=None),
        context=context,
        decls=component_nodes,
        source_positions=[
            source_tree.source_position_tree.position for source_tree in source_trees
        ],
    )


def build_component_decl_from_yaml_document(
    context: ComponentLoadContext,
    source_tree: ValueAndSourcePositionTree,
    path: ComponentPath,
) -> ComponentDecl:
    component_file_model = _parse_and_populate_model_with_annotated_errors(
        cls=ComponentFileModel, obj_parse_root=source_tree, obj_key_path_prefix=[]
    )
    component_cls = _get_component_class(context, component_file_model)
    component_decl_type = component_cls.get_decl_type()
    check.invariant(component_decl_type in (YamlDecl, DefsFolderDecl))

    if component_decl_type == DefsFolderDecl:
        children = build_component_decls_from_directory_items(context, component_file_model)
        return DefsFolderDecl(
            context=context,
            path=path,
            children=children,
            source_tree=source_tree,
            component_file_model=component_file_model,
        )
    else:
        return YamlDecl(
            context=context,
            source_tree=source_tree,
            component_file_model=component_file_model,
            path=path,
        )
