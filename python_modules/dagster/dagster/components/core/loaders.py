import abc
import inspect
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Generic, Optional, TypeVar, Union

from dagster_shared.serdes.objects import PluginObjectKey
from dagster_shared.yaml_utils import parse_yamls_with_source_position
from dagster_shared.yaml_utils.source_position import SourcePosition, ValueAndSourcePositionTree
from pydantic import TypeAdapter

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
    ComponentPath,
    CompositeComponent,
    CompositeYamlComponent,
    DagsterDefsComponent,
    DefsFolderComponent,
    context_with_injected_scope,
    find_defs_or_component_yaml,
)
from dagster.components.core.package_entry import load_package_object

T = TypeVar("T", bound=Component)


class ComponentNode(abc.ABC, Generic[T]):
    """Class representing a component in the defs hierarchy. A tree of component nodes
    is initially built before any components are loaded.
    """

    @abc.abstractmethod
    def load_component(self, context: ComponentLoadContext) -> T:
        pass


class ComponentLoaderNode(ComponentNode[Component]):
    def __init__(self, component_node_fn: Callable[[ComponentLoadContext], Component]):
        self.component_node = component_node_fn

    def load_component(self, context: ComponentLoadContext) -> Component:
        return self.component_node(context)


class CompositeYamlComponentNode(ComponentNode[CompositeYamlComponent]):
    def __init__(
        self, components: Sequence[ComponentNode], source_positions: Sequence[SourcePosition]
    ):
        self.components = components
        self.source_positions = source_positions

    def load_component(self, context: ComponentLoadContext) -> "CompositeYamlComponent":
        return CompositeYamlComponent(
            components=[component.load_component(context) for component in self.components],
            source_positions=self.source_positions,
        )


class CompositeComponentNode(ComponentNode[CompositeComponent]):
    def __init__(self, components: Mapping[str, ComponentLoaderNode]):
        self.components = components

    def load_component(self, context: ComponentLoadContext) -> "CompositeComponent":
        return CompositeComponent(
            components={
                attr: component.load_component(context)
                for attr, component in self.components.items()
            }
        )


class YamlComponentNode(ComponentNode):
    def __init__(self, source_tree: ValueAndSourcePositionTree):
        self.source_tree = source_tree

    def load_component(self, context: ComponentLoadContext) -> "Component":
        from dagster.components.core.defs_module import ComponentFileModel

        component_file_model = _parse_and_populate_model_with_annotated_errors(
            cls=ComponentFileModel, obj_parse_root=self.source_tree, obj_key_path_prefix=[]
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
            self.source_tree.source_position_tree,
        )

        model_cls = obj.get_model_cls()

        # grab the attributes from the yaml file
        if model_cls is None:
            attributes = None
        elif self.source_tree:
            attributes_position_tree = self.source_tree.source_position_tree.children["attributes"]
            with enrich_validation_errors_with_source_position(
                attributes_position_tree, ["attributes"]
            ):
                attributes = TypeAdapter(model_cls).validate_python(component_file_model.attributes)
        else:
            attributes = TypeAdapter(model_cls).validate_python(component_file_model.attributes)

        return obj.load(attributes, context)


class DagsterDefsComponentNode(ComponentNode[DagsterDefsComponent]):
    def __init__(self, path: Path):
        self.path = path

    def load_component(self, context: ComponentLoadContext) -> DagsterDefsComponent:
        return DagsterDefsComponent(path=self.path)


class DefsFolderComponentNode(ComponentNode["DefsFolderComponent"]):
    def __init__(self, path: Path, children: Mapping[Path, ComponentNode]):
        self.path = path
        self.children = children

    @classmethod
    def get(cls, context: ComponentLoadContext) -> "DefsFolderComponentNode":
        component = get_component_node(context)
        return check.inst(
            component,
            DefsFolderComponentNode,
            f"Expected PendingDefsFolderComponent at {context.path}, got {component}.",
        )

    def load_component(self, context: ComponentLoadContext) -> "DefsFolderComponent":
        return DefsFolderComponent(
            path=self.path,
            children={
                subpath: component_node.load_component(context.for_path(subpath))
                for subpath, component_node in self.children.items()
            },
            asset_post_processors=None,
        )

    def iterate_component_nodes(self) -> Iterator[ComponentNode]:
        for _, component in self.iterate_path_component_node_pairs():
            yield component

    def iterate_path_component_node_pairs(
        self,
    ) -> Iterator[tuple[ComponentPath, ComponentNode]]:
        for path, component_node in self.children.items():
            yield ComponentPath(file_path=path), component_node

            if isinstance(component_node, DefsFolderComponentNode):
                yield from component_node.iterate_path_component_node_pairs()

            if isinstance(component_node, CompositeYamlComponentNode):
                for idx, inner_comp in enumerate(component_node.components):
                    yield ComponentPath(file_path=path, instance_key=idx), inner_comp

            if isinstance(component_node, CompositeComponentNode):
                for attr, inner_comp in component_node.components.items():
                    yield ComponentPath(file_path=path, instance_key=attr), inner_comp


def get_component_node(context: ComponentLoadContext) -> Optional[ComponentNode]:
    """Attempts to determine the type of component that should be loaded for the given context.  Iterates through potential component
    type matches, prioritizing more specific types: YAML, Python, plain Dagster defs, and component
    folder.
    """
    # in priority order
    # yaml component
    if find_defs_or_component_yaml(context.path):
        return load_yaml_component_node(context)
    # pythonic component
    elif (
        context.terminate_autoloading_on_keyword_files and (context.path / "component.py").exists()
    ):
        return get_component_node_from_python_file(context)
    # defs
    elif (
        context.terminate_autoloading_on_keyword_files
        and (context.path / "definitions.py").exists()
    ):
        return DagsterDefsComponentNode(path=context.path / "definitions.py")
    elif context.path.suffix == ".py":
        return DagsterDefsComponentNode(path=context.path)
    # folder
    elif context.path.is_dir():
        children = find_component_nodes_from_context(context)
        if children:
            return DefsFolderComponentNode(
                path=context.path,
                children=children,
            )

    return None


def find_component_nodes_from_context(
    context: ComponentLoadContext,
) -> Mapping[Path, ComponentNode]:
    found = {}
    for subpath in context.path.iterdir():
        relative_subpath = subpath.relative_to(context.path)
        if any(relative_subpath.match(pattern) for pattern in EXPLICITLY_IGNORED_GLOB_PATTERNS):
            continue
        component_node = get_component_node(context.for_path(subpath))
        if component_node:
            found[subpath] = component_node
    return found


def get_component_node_from_python_file(
    context: ComponentLoadContext,
) -> Union[ComponentLoaderNode, CompositeComponentNode]:
    # backcompat for component.yaml
    component_def_path = context.path / "component.py"
    module = context.load_defs_relative_python_module(component_def_path)
    component_loaders = list(inspect.getmembers(module, is_component_loader))
    if len(component_loaders) == 0:
        raise DagsterInvalidDefinitionError("No component nodes found in module")
    elif len(component_loaders) == 1:
        _, component_loader = component_loaders[0]
        return ComponentLoaderNode(component_loader)
    else:
        return CompositeComponentNode(
            {
                attr: ComponentLoaderNode(component_loader)
                for attr, component_loader in component_loaders
            }
        )


def load_yaml_component_node(context: ComponentLoadContext) -> ComponentNode:
    component_def_path = check.not_none(find_defs_or_component_yaml(context.path))
    return get_component_node_from_yaml_file(component_def_path)


def get_component_node_from_yaml_file(component_def_path: Path) -> ComponentNode:
    source_trees = parse_yamls_with_source_position(
        component_def_path.read_text(), str(component_def_path)
    )
    component_nodes = []
    for source_tree in source_trees:
        component_nodes.append(YamlComponentNode(source_tree))

    check.invariant(len(component_nodes) > 0, "No components found in YAML file")
    return CompositeYamlComponentNode(
        component_nodes,
        [source_tree.source_position_tree.position for source_tree in source_trees],
    )
