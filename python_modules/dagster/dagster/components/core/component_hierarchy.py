import hashlib
from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Optional

from dagster_shared.record import record

from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext, use_component_load_context


def compute_file_hash(path: Path) -> str:
    return hashlib.sha1(path.read_text().encode("utf-8")).hexdigest()


@record
class ComponentYamlFile:
    path: Path
    sha: str


@record
class ComponentDeclaration(ABC):
    path: Path

    @abstractmethod
    def load(self, context: ComponentLoadContext) -> Component:
        """Load a component from this declaration."""
        pass


@record
class YamlComponentDeclaration(ComponentDeclaration):
    yaml_file: ComponentYamlFile

    def load(self, context: ComponentLoadContext) -> Component:
        from dagster.components.core.defs_module import load_yaml_component

        return load_yaml_component(context)


class PythonicComponentDeclaration(ComponentDeclaration):
    def load(self, context: ComponentLoadContext) -> Component:
        from dagster.components.core.defs_module import load_pythonic_component

        return load_pythonic_component(context)


class DefsComponentDeclaration(ComponentDeclaration):
    def load(self, context: ComponentLoadContext) -> Component:
        from dagster.components.core.defs_module import DagsterDefsComponent

        return DagsterDefsComponent(path=context.path / "definitions.py")


class PythonModuleComponentDeclaration(ComponentDeclaration):
    def load(self, context: ComponentLoadContext) -> Component:
        from dagster.components.core.defs_module import DagsterDefsComponent

        return DagsterDefsComponent(path=context.path)


@record
class FolderComponentDeclaration(ComponentDeclaration):
    children: Mapping[Path, ComponentDeclaration]
    yaml_file: Optional[ComponentYamlFile] = None

    def load(self, context: ComponentLoadContext) -> Component:
        from dagster.components.core.defs_module import DefsFolderComponent

        return DefsFolderComponent(
            path=context.path,
            children={
                path: child_decl.load(context.for_path(path))
                for path, child_decl in self.children.items()
            },
            asset_post_processors=None,
        )


@record
class ComponentHierarchy:
    root: ComponentDeclaration


def build_component_declaration(
    context: ComponentLoadContext,
) -> Optional[ComponentDeclaration]:
    component_yaml_path = context.path / "component.yaml"
    if component_yaml_path.exists():
        return YamlComponentDeclaration(
            path=context.path,
            yaml_file=ComponentYamlFile(
                path=component_yaml_path, sha=compute_file_hash(component_yaml_path)
            ),
        )
    # pythonic component
    elif (context.path / "component.py").exists():
        return PythonicComponentDeclaration(path=context.path)
    # defs
    elif (context.path / "definitions.py").exists():
        return DefsComponentDeclaration(path=context.path)
    elif context.path.suffix == ".py":
        return PythonModuleComponentDeclaration(path=context.path)
    # folder
    elif context.path.is_dir():
        return build_folder_component_declaration(context)

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
