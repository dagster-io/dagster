from pathlib import Path
from typing import cast

from dagster_components.core.component import ComponentTypeRegistry
from dagster_components.core.component_defs_builder import (
    build_components_from_component_path,
    loading_context_for_component_path,
)

from dagster_components_tests.scope_tests.footran_component.component import FootranComponent


def test_custom_scope() -> None:
    components = build_components_from_component_path(
        path=Path(__file__).parent / "footran_component",
        registry=ComponentTypeRegistry.empty(),
        resources={},
    )

    assert len(components) == 1
    component = components[0]
    # This is probably due to lack of module caching?
    # assert isinstance(component, FootranComponent)
    assert type(component).__name__ == "FootranComponent"
    component = cast(FootranComponent, component)

    assert component.target_address == "some_address"
    load_context = loading_context_for_component_path(
        path=Path(__file__).parent / "footran_component",
        registry=ComponentTypeRegistry.empty(),
        resources={},
    )
    assert component.required_env_vars(load_context) == {"FOOTRAN_API_KEY", "FOOTRAN_API_SECRET"}
