from pathlib import Path
from typing import Union

from dagster_shared import check

from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.defs_module import CompositeYamlComponent, get_component


def build_components_at_defs_path(
    context: ComponentLoadContext,
    defs_path: Union[str, Path],
) -> list[Component]:
    component = check.inst(
        get_component(context.for_defs_path(defs_path)), Component, "Expected a Component"
    )

    return (
        list(component.components) if isinstance(component, CompositeYamlComponent) else [component]
    )


def build_component_at_path(
    context: ComponentLoadContext, defs_path: Union[str, Path]
) -> Component:
    components = build_components_at_defs_path(context, defs_path)
    check.invariant(len(components) == 1, "Expected a single component")
    return components[0]


def build_component_defs_at_path(
    context: ComponentLoadContext,
    defs_path: Union[str, Path],
) -> Definitions:
    components = build_components_at_defs_path(context, defs_path)
    return Definitions.merge(*[component.build_defs(context) for component in components])
