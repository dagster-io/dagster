from dagster_components import Component, component
from dagster_components.core.component import get_component_name, is_registered_component


def test_registered_component_with_default_name() -> None:
    @component
    class RegisteredComponent(Component): ...

    assert is_registered_component(RegisteredComponent)
    assert get_component_name(RegisteredComponent) == "registered_component"


def test_registered_component_with_default_name_and_parens() -> None:
    @component()
    class RegisteredComponent(Component): ...

    assert is_registered_component(RegisteredComponent)
    assert get_component_name(RegisteredComponent) == "registered_component"


def test_registered_component_with_explicit_kwarg_name() -> None:
    @component(name="explicit_name")
    class RegisteredComponent(Component): ...

    assert is_registered_component(RegisteredComponent)
    assert get_component_name(RegisteredComponent) == "explicit_name"


def test_unregistered_component() -> None:
    class UnregisteredComponent(Component): ...

    assert not is_registered_component(UnregisteredComponent)
