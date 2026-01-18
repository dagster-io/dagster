import importlib
from typing import Optional

import dagster as dg
import pytest
from dagster.components.core.component_tree import ComponentTreeException
from dagster.components.testing import create_defs_folder_sandbox
from pydantic import BaseModel


class FooComponent(dg.Component):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()


class FooSubclassComponent(FooComponent): ...


class BarComponent(dg.Component):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()


class ErrorComponent(dg.Component):
    @classmethod
    def load(
        cls, attributes: Optional[BaseModel], context: dg.ComponentLoadContext
    ) -> "ErrorComponent":
        raise Exception("Can't load this component!")


def test_get_all_components_yaml() -> None:
    with create_defs_folder_sandbox() as sandbox:
        sandbox.scaffold_component(
            component_cls=FooComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.component_tree_tests.test_get_all_components.FooComponent",
            },
        )

        sandbox.scaffold_component(
            component_cls=FooSubclassComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.component_tree_tests.test_get_all_components.FooSubclassComponent",
            },
        )

        sandbox.scaffold_component(
            component_cls=BarComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.component_tree_tests.test_get_all_components.BarComponent",
            },
        )

        sandbox.scaffold_component(
            component_cls=ErrorComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.component_tree_tests.test_get_all_components.ErrorComponent",
            },
        )

        with sandbox.build_component_tree() as tree:
            foo_components = tree.get_all_components(of_type=FooComponent)
            assert len(foo_components) == 2
            # order is nondeterministic
            assert any(type(component) == FooComponent for component in foo_components)
            assert any(type(component) == FooSubclassComponent for component in foo_components)

            bar_components = tree.get_all_components(of_type=BarComponent)
            assert len(bar_components) == 1
            assert isinstance(bar_components[0], BarComponent)

            # error if you try to load a selection that includes the ErrorComponent
            with pytest.raises(ComponentTreeException):
                tree.get_all_components(of_type=ErrorComponent)

            with pytest.raises(ComponentTreeException):
                tree.get_all_components(of_type=dg.Component)


def test_get_all_components_python_decorator() -> None:
    """Test that Python decorator components with return signature are properly detected."""
    with create_defs_folder_sandbox() as sandbox:
        # Create a Python file with component loaders
        python_file_path = sandbox.defs_folder_path / "python_components.py"
        python_file_path.write_text("""
import dagster as dg

class FooComponent(dg.Component):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions(assets=[dg.AssetSpec("foo_asset")])

class FooSubclassComponent(FooComponent):
    ...

class BarComponent(dg.Component):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions(assets=[dg.AssetSpec("bar_asset")])

@dg.component_instance
def load_foo(context: dg.ComponentLoadContext) -> FooComponent:
    return FooComponent()

@dg.component_instance
def load_foo_subclass(context: dg.ComponentLoadContext) -> FooSubclassComponent:
    return FooSubclassComponent()

@dg.component_instance
def load_bar(context: dg.ComponentLoadContext) -> BarComponent:
    return BarComponent()

@dg.component_instance
def unannotated(context: dg.ComponentLoadContext):
    # note: won't be detected
    return BarComponent()

@dg.component_instance
def error_component(context: dg.ComponentLoadContext):
    raise Exception("Can't load this component!")
""")

        with sandbox.build_component_tree() as tree:
            loaders_module = importlib.import_module(
                f"{sandbox.project_name}.defs.python_components"
            )
            FooComponent = loaders_module.FooComponent
            FooSubclassComponent = loaders_module.FooSubclassComponent
            BarComponent = loaders_module.BarComponent

            # Test getting all FooComponent instances
            foo_components = tree.get_all_components(of_type=FooComponent)
            assert len(foo_components) == 2
            assert isinstance(foo_components[0], FooComponent)
            assert isinstance(foo_components[1], FooSubclassComponent)

            # Test getting all BarComponent instances
            bar_components = tree.get_all_components(of_type=BarComponent)
            assert len(bar_components) == 1
            assert isinstance(bar_components[0], BarComponent)

            # Error if you get all components
            with pytest.raises(ComponentTreeException):
                tree.get_all_components(of_type=dg.Component)
