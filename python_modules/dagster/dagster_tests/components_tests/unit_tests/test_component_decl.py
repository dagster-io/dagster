import importlib
import sys
from pathlib import Path

import pytest
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.decl import (
    ComponentDecl,
    ComponentLoaderDecl,
    CompositePythonDecl,
    DefsFolderDecl,
)
from dagster.components.core.defs_module import (
    ComponentPath,
    CompositeComponent,
    DefsFolderComponent,
)
from dagster.components.core.tree import ComponentTree
from dagster_shared.record import record


@record(checked=False)
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


class MyComponent(Component):
    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        raise NotImplementedError("Not implemented")


def test_component_loader_decl(component_tree: MockComponentTree):
    my_component = MyComponent()
    decl = ComponentLoaderDecl(
        context=component_tree.decl_load_context,
        path=ComponentPath(file_path=Path(__file__).parent, instance_key=None),
        component_node_fn=lambda context: my_component,
    )

    component_tree.set_root_decl(decl)
    assert component_tree.load_root_component() == my_component


def test_composite_python_decl(component_tree: MockComponentTree):
    my_component = MyComponent()
    loader_decl = ComponentLoaderDecl(
        context=component_tree.decl_load_context,
        path=ComponentPath(file_path=Path(__file__).parent, instance_key="my_component"),
        component_node_fn=lambda context: my_component,
    )
    decl = CompositePythonDecl(
        path=ComponentPath(file_path=Path(__file__).parent, instance_key=None),
        context=component_tree.decl_load_context,
        decls={"my_component": loader_decl},
    )

    component_tree.set_root_decl(decl)
    loaded_component = component_tree.load_root_component()
    assert isinstance(loaded_component, CompositeComponent)
    assert loaded_component.components["my_component"] == my_component


def test_defs_folder_decl(component_tree: MockComponentTree):
    my_component = MyComponent()
    loader_decl = ComponentLoaderDecl(
        context=component_tree.decl_load_context,
        path=ComponentPath(file_path=Path(__file__).parent / "my_component", instance_key=None),
        component_node_fn=lambda context: my_component,
    )

    my_other_component = MyComponent()
    my_other_loader_decl = ComponentLoaderDecl(
        context=component_tree.decl_load_context,
        path=ComponentPath(
            file_path=Path(__file__).parent / "my_other_component", instance_key=None
        ),
        component_node_fn=lambda context: my_other_component,
    )

    defs_path = Path(__file__).parent
    decl = DefsFolderDecl(
        context=component_tree.decl_load_context,
        path=ComponentPath(file_path=defs_path, instance_key=None),
        children={
            defs_path / "my_component": loader_decl,
            defs_path / "my_other_component": my_other_loader_decl,
        },
        source_tree=None,
        component_file_model=None,
    )

    component_tree.set_root_decl(decl)
    loaded_component = component_tree.load_root_component()
    assert isinstance(loaded_component, DefsFolderComponent)
    assert loaded_component.children[defs_path / "my_component"] == my_component

    assert component_tree.find_decl_at_path(defs_path) == decl
    assert component_tree.find_decl_at_path(defs_path / "my_component") == loader_decl
    assert (
        component_tree.find_decl_at_path(defs_path / "my_other_component") == my_other_loader_decl
    )
