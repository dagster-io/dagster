import importlib
import sys
from pathlib import Path

import dagster as dg
import pytest
from dagster.components.core.component_tree import ComponentTree
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.decl import (
    ComponentDecl,
    ComponentLoaderDecl,
    DefsFolderDecl,
    PythonFileDecl,
)
from dagster.components.core.defs_module import ComponentPath, PythonFileComponent


class MockComponentTree(ComponentTree):
    def set_root_decl(self, root_decl: ComponentDecl):
        setattr(self, "_root_decl", root_decl)

    def find_root_decl(self):
        if hasattr(self, "_root_decl"):
            return getattr(self, "_root_decl")
        return super().find_root_decl()


@pytest.fixture
def component_tree() -> MockComponentTree:
    # add file parent to sys path to make it a package
    sys.path.append(str(Path(__file__).parent))
    return MockComponentTree(
        defs_module=importlib.import_module(Path(__file__).stem),
        project_root=Path(__file__).parent,
    )


class MyComponent(dg.Component):
    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        raise NotImplementedError("Not implemented")


def test_component_loader_decl(component_tree: MockComponentTree):
    my_component = MyComponent()
    decl = ComponentLoaderDecl(
        context=component_tree.decl_load_context,
        path=ComponentPath.from_path(Path(__file__).parent),
        component_node_fn=lambda context: my_component,
    )

    component_tree.set_root_decl(decl)
    assert component_tree.load_root_component() == my_component


def test_composite_python_decl(component_tree: MockComponentTree):
    my_component = MyComponent()
    loader_decl = ComponentLoaderDecl(
        context=component_tree.decl_load_context,
        path=ComponentPath.from_path(Path(__file__).parent, "my_component"),
        component_node_fn=lambda context: my_component,
    )
    decl = PythonFileDecl(
        path=ComponentPath.from_path(Path(__file__).parent),
        context=component_tree.decl_load_context,
        decls={"my_component": loader_decl},
    )

    component_tree.set_root_decl(decl)
    loaded_component = component_tree.load_root_component()
    assert isinstance(loaded_component, PythonFileComponent)
    assert loaded_component.components["my_component"] == my_component


def test_defs_folder_decl(component_tree: MockComponentTree):
    my_component = MyComponent()
    loader_decl = ComponentLoaderDecl(
        context=component_tree.decl_load_context,
        path=ComponentPath.from_path(Path(__file__).parent / "my_component"),
        component_node_fn=lambda context: my_component,
    )

    my_other_component = MyComponent()
    my_other_loader_decl = ComponentLoaderDecl(
        context=component_tree.decl_load_context,
        path=ComponentPath.from_path(Path(__file__).parent / "my_other_component"),
        component_node_fn=lambda context: my_other_component,
    )

    defs_path = Path(__file__).parent
    decl = DefsFolderDecl(
        context=component_tree.decl_load_context,
        path=ComponentPath.from_path(defs_path),
        children={
            defs_path / "my_component": loader_decl,
            defs_path / "my_other_component": my_other_loader_decl,
        },
        source_tree=None,
        component_file_model=None,
    )

    component_tree.set_root_decl(decl)
    loaded_component = component_tree.load_root_component()
    assert isinstance(loaded_component, dg.DefsFolderComponent)
    assert loaded_component.children[defs_path / "my_component"] == my_component

    assert component_tree.find_decl_at_path(defs_path) == decl
    assert component_tree.find_decl_at_path(defs_path / "my_component") == loader_decl
    assert (
        component_tree.find_decl_at_path(defs_path / "my_other_component") == my_other_loader_decl
    )
