import pytest
from dagster._components import Component, ComponentRegistry, global_component
from dagster._components.impls.python_script_component import PythonScriptCollection
from dagster._core.errors import DagsterInvalidDefinitionError


def test_global_component_registration():
    global_registry = ComponentRegistry.get_global()
    try:

        @global_component
        class MyGlobalComponent(Component):
            pass

        assert global_registry.get(MyGlobalComponent.registered_name()) is MyGlobalComponent
    finally:
        ComponentRegistry.get_global().unregister(MyGlobalComponent.registered_name())


def test_global_component_registration_fails_not_a_component():
    with pytest.raises(DagsterInvalidDefinitionError, match="is not a subclass of Component"):

        @global_component  # type: ignore
        class NotAComponent:
            pass


def test_known_global_components():
    global_registry = ComponentRegistry.get_global()
    assert global_registry.get("python_script_collection") is PythonScriptCollection
