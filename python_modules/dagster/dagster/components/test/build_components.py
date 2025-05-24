from pathlib import Path
from typing import Any, TypeVar, Union

from dagster_shared import check
from dagster_shared.yaml_utils import parse_yaml_with_source_position
from pydantic import TypeAdapter

from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.pydantic_yaml import enrich_validation_errors_with_source_position
from dagster.components import Component, ComponentLoadContext
from dagster.components.core.defs_module import CompositeYamlComponent, get_component

T = TypeVar("T")
T_Component = TypeVar("T_Component", bound=Component)


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


def load_context_and_component_for_test(
    component_type: type[T_Component], attrs: Union[str, dict[str, Any]]
) -> tuple[ComponentLoadContext, T_Component]:
    context = ComponentLoadContext.for_test()
    context = context.with_rendering_scope(component_type.get_additional_scope())
    model_cls = check.not_none(
        component_type.get_model_cls(), "Component must have schema for direct test"
    )
    if isinstance(attrs, str):
        source_positions = parse_yaml_with_source_position(attrs)
        with enrich_validation_errors_with_source_position(
            source_positions.source_position_tree, []
        ):
            attributes = TypeAdapter(model_cls).validate_python(source_positions.value)
    else:
        attributes = TypeAdapter(model_cls).validate_python(attrs)
    component = component_type.load(attributes, context)
    return context, component


def load_component_for_test(
    component_type: type[T_Component], attrs: Union[str, dict[str, Any]]
) -> T_Component:
    _, component = load_context_and_component_for_test(component_type, attrs)
    return component


def build_component_defs_for_test(
    component_type: type[Component], attrs: dict[str, Any]
) -> Definitions:
    context, component = load_context_and_component_for_test(component_type, attrs)
    return component.build_defs(context)
