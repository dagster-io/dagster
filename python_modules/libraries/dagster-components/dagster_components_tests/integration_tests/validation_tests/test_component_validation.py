from dagster_components import Component, component_type
from dagster_components.core.component import get_component_type_name, is_registered_component_type


def test_registered_component_with_default_name() -> None:
    @component_type
    class RegisteredComponent(Component): ...

    assert is_registered_component_type(RegisteredComponent)
    assert get_component_type_name(RegisteredComponent) == "registered_component"
