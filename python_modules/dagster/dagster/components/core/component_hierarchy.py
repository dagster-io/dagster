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
class ComponentDeclaration:
    path: Path

    @classmethod
    def build(cls, context: ComponentLoadContext) -> "ComponentDeclaration":
        return cls(path=context.path)


@record
class YamlComponentDeclaration(ComponentDeclaration):
    yaml_file: ComponentYamlFile

    @classmethod
    def build(cls, context: ComponentLoadContext) -> "YamlComponentDeclaration":
        component_yaml_path = context.path / "component.yaml"
        return cls(
            path=context.path,
            yaml_file=ComponentYamlFile(
                path=component_yaml_path, sha=compute_file_hash(component_yaml_path)
            ),
        )


class PythonicComponentDeclaration(ComponentDeclaration): ...


class DefsComponentDeclaration(ComponentDeclaration): ...


class PythonModuleComponentDeclaration(ComponentDeclaration): ...


@record
class FolderComponentDeclaration(ComponentDeclaration):
    children: Mapping[Path, ComponentDeclaration]
    yaml_file: Optional[ComponentYamlFile] = None

    @classmethod
    def build(cls, context: ComponentLoadContext) -> "FolderComponentDeclaration":
        found: dict[Path, ComponentDeclaration] = {}
        for subpath in context.path.iterdir():
            sub_ctx = context.for_path(subpath)
            with use_component_load_context(sub_ctx):
                component = build_component_declaration(sub_ctx)
                if component:
                    found[subpath] = component

        component_yaml_path = context.path / "component.yaml"
        return cls(
            path=context.path,
            children=found,
            yaml_file=None
            if not component_yaml_path.exists()
            else ComponentYamlFile(
                path=component_yaml_path, sha=compute_file_hash(component_yaml_path)
            ),
        )


@record
class ComponentHierarchy:
    root: ComponentDeclaration


def build_component_declaration(
    context: ComponentLoadContext,
) -> Optional[ComponentDeclaration]:
    # Check for yaml component
    component_yaml_path = context.path / "component.yaml"
    if component_yaml_path.exists():
        return YamlComponentDeclaration.build(context)

    # Check for pythonic component
    if (context.path / "component.py").exists():
        return PythonicComponentDeclaration.build(context)

    # Check for defs component
    if (context.path / "definitions.py").exists():
        return DefsComponentDeclaration.build(context)

    # Check for python module
    if context.path.suffix == ".py":
        return PythonModuleComponentDeclaration.build(context)

    # Check for folder component
    if context.path.is_dir():
        return FolderComponentDeclaration.build(context)

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
    root_decl = build_component_declaration(context)
    if not root_decl:
        raise ValueError("Expected root_decl to be defined, but got None")
    return ComponentHierarchy(root=root_decl)


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
    context: ComponentLoadContext, decl: ComponentDeclaration
) -> Component:
    """Builds a component from the given context and hierarchy node.

    Args:
        context (ComponentLoadContext): The context from which to start building the component.
        decl (ComponentDeclaration): The node representing the component in the hierarchy.

    Returns:
        Component: The built component.
    """
    from dagster.components.core.defs_module import (
        DagsterDefsComponent,
        DefsFolderComponent,
        load_pythonic_component,
        load_yaml_component,
    )

    if isinstance(decl, YamlComponentDeclaration):
        return load_yaml_component(context)
    elif isinstance(decl, PythonicComponentDeclaration):
        return load_pythonic_component(context)
    elif isinstance(decl, DefsComponentDeclaration):
        return DagsterDefsComponent(path=context.path / "definitions.py")
    elif isinstance(decl, PythonModuleComponentDeclaration):
        return DagsterDefsComponent(path=context.path)
    elif isinstance(decl, FolderComponentDeclaration):
        return DefsFolderComponent(
            path=context.path,
            children={
                path: build_component_from_node(context.for_path(path), child_decl)
                for path, child_decl in decl.children.items()
            },
            asset_post_processors=None,
        )
    else:
        check.failed(f"Unexpected ComponentDeclaration type: {type(decl)}")


def build_folder_component_declaration(
    context: ComponentLoadContext,
) -> FolderComponentDeclaration:
    found: dict[Path, ComponentDeclaration] = {}
    for subpath in context.path.iterdir():
        sub_ctx = context.for_path(subpath)
        with use_component_load_context(sub_ctx):
            component = build_component_declaration(sub_ctx)
            if component:
                found[subpath] = component
    component_yaml_path = context.path / "component.yaml"
    return FolderComponentDeclaration(
        path=context.path,
        children=found,
        yaml_file=None
        if not component_yaml_path.exists()
        else ComponentYamlFile(
            path=component_yaml_path, sha=compute_file_hash(component_yaml_path)
        ),
    )
