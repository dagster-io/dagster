import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Optional

from dagster_shared.record import record

import dagster._check as check
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext, use_component_load_context


def compute_file_hash(path: Path) -> str:
    return hashlib.sha1(path.read_text().encode("utf-8")).hexdigest()


@record
class ComponentYamlFile:
    path: Path
    sha: str


@record
class ComponentHierarchyNode:
    path: Path


@record
class YamlComponentHierarchyNode(ComponentHierarchyNode):
    yaml_file: ComponentYamlFile


class PythonicComponentHierarchyNode(ComponentHierarchyNode): ...


class DefsComponentHierarchyNode(ComponentHierarchyNode): ...


class PythonModuleComponentHierarchyNode(ComponentHierarchyNode): ...


@record
class FolderComponentHierarchyNode(ComponentHierarchyNode):
    children: Mapping[Path, ComponentHierarchyNode]
    yaml_file: Optional[ComponentYamlFile] = None


@record
class ComponentHierarchy:
    root: ComponentHierarchyNode


def build_component_hierarchy_node(
    context: ComponentLoadContext,
) -> Optional[ComponentHierarchyNode]:
    component_yaml_path = context.path / "component.yaml"
    if component_yaml_path.exists():
        return YamlComponentHierarchyNode(
            path=context.path,
            yaml_file=ComponentYamlFile(
                path=component_yaml_path, sha=compute_file_hash(component_yaml_path)
            ),
        )
    # pythonic component
    elif (context.path / "component.py").exists():
        return PythonicComponentHierarchyNode(path=context.path)
    # defs
    elif (context.path / "definitions.py").exists():
        return DefsComponentHierarchyNode(path=context.path)
    elif context.path.suffix == ".py":
        return PythonModuleComponentHierarchyNode(path=context.path)
    # folder
    elif context.path.is_dir():
        return build_folder_component_hierarchy_node(context)

    return None


def build_component_hierarchy(
    context: ComponentLoadContext,
) -> ComponentHierarchy:
    """Builds a hierarchy of components starting from the given context.

    Args:
        context (ComponentLoadContext): The context from which to start building the hierarchy.

    Returns:
        ComponentHierarchy: The root node of the component hierarchy.
    """
    root_node = build_component_hierarchy_node(context)
    if not root_node:
        raise ValueError("Expected root_node to be defined, but got None")
    return ComponentHierarchy(root=root_node)


def build_root_component(
    context: ComponentLoadContext, hierarchy: ComponentHierarchy
) -> Optional[Component]:
    """Builds the root component from the given context.

    Args:
        context (ComponentLoadContext): The context from which to start building the component.

    Returns:
        Optional[Component]: The root component if found, otherwise None.
    """
    with use_component_load_context(context):
        return build_component_from_node(context, hierarchy.root)



def build_component_from_node(
    context: ComponentLoadContext, node: ComponentHierarchyNode
) -> Component:
    """Builds a component from the given context and hierarchy node.

    Args:
        context (ComponentLoadContext): The context from which to start building the component.
        node (ComponentHierarchyNode): The node representing the component in the hierarchy.

    Returns:
        Component: The built component.
    """

    from dagster.components.core.defs_module import (
        DagsterDefsComponent,
        DefsFolderComponent,
        load_pythonic_component,
        load_yaml_component,
    )

    if isinstance(node, YamlComponentHierarchyNode):
        return load_yaml_component(context)
    elif isinstance(node, PythonicComponentHierarchyNode):
        return load_pythonic_component(context)
    elif isinstance(node, DefsComponentHierarchyNode):
        return DagsterDefsComponent(path=context.path / "definitions.py")
    elif isinstance(node, PythonModuleComponentHierarchyNode):
        return DagsterDefsComponent(path=context.path)
    elif isinstance(node, FolderComponentHierarchyNode):
        return DefsFolderComponent(
            path=context.path,

            children={
                path: build_component_from_node(context.for_path(path), child_node)
                for path, child_node in node.children.items()
            },

            asset_post_processors=None,
        )
    else:
        check.failed(f"Unexpected ComponentHierarchyNode type: {type(node)}")


def build_folder_component_hierarchy_node(
    context: ComponentLoadContext,
) -> FolderComponentHierarchyNode:
    found: dict[Path, ComponentHierarchyNode] = {}
    for subpath in context.path.iterdir():
        sub_ctx = context.for_path(subpath)
        with use_component_load_context(sub_ctx):
            component = build_component_hierarchy_node(sub_ctx)
            if component:
                found[subpath] = component
    component_yaml_path = context.path / "component.yaml"
    return FolderComponentHierarchyNode(
        path=context.path,
        children=found,
        yaml_file=None
        if not component_yaml_path.exists()
        else ComponentYamlFile(
            path=component_yaml_path, sha=compute_file_hash(component_yaml_path)
        ),
    )
