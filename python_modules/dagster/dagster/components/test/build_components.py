from pathlib import Path
from typing import Any, Optional, TypeVar, Union

from dagster_shared import check
from dagster_shared.yaml_utils import parse_yaml_with_source_position
from pydantic import TypeAdapter

from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.pydantic_yaml import enrich_validation_errors_with_source_position
from dagster.components import Component, ComponentLoadContext
from dagster.components.core.defs_module import CompositeYamlComponent, get_component
from dagster.components.resolved.context import ResolutionContext

T = TypeVar("T")
T_Component = TypeVar("T_Component", bound=Component)


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


def build_component_for_test(
    component_type: type[T_Component], attrs: Union[str, dict[str, Any]]
) -> T_Component:
    """Build a component from a component type and attributes. The attributes are what would be in the yaml file directly deserialized into memory (e.g. with template strings not resolved yet)."""
    _, component = load_context_and_component_for_test(component_type, attrs)
    return component


def build_component_defs_for_test(
    component_type: type[Component], attrs: dict[str, Any]
) -> Definitions:
    """Build a set of definitions from a component type and attributes. The attributes are what would be in the yaml file directly deserialized into memory (e.g. with template strings not resolved yet)."""
    context, component = load_context_and_component_for_test(component_type, attrs)
    return component.build_defs(context)


def build_component_at_defs_path(
    context: ComponentLoadContext, defs_path: Optional[Union[str, Path]] = None
) -> Component:
    """Build a component at the path relative to the defs module. If no path is provided, the component will be built from the information in the context."""
    components = build_components_at_defs_path(context, defs_path)
    check.invariant(len(components) == 1, "Expected a single component")
    return components[0]


def build_component_defs_at_defs_path(
    context: ComponentLoadContext,
    defs_path: Optional[Union[str, Path]] = None,
) -> Definitions:
    """Build a set of definitions at a specific defs_path in a project. If no path is provided, the definitions will be built from the information in the context."""
    components = build_components_at_defs_path(context, defs_path)
    return Definitions.merge(*[component.build_defs(context) for component in components])


def build_components_at_defs_path(
    context: ComponentLoadContext,
    defs_path: Optional[Union[str, Path]] = None,
) -> list[Component]:
    """Build all the component instances in a particular path. Useful when the user declares multiple component instances in a single defs.yaml."""
    component = check.inst(
        get_component(context.for_defs_path(defs_path) if defs_path else context),
        Component,
        "Expected a Component",
    )

    return (
        list(component.components) if isinstance(component, CompositeYamlComponent) else [component]
    )


def defs_relative_component_context(
    *,
    project_root: Path,
    defs_path: Path,
    defs_module_name: str,
    defs_relative_path: Union[str, Path],
) -> ComponentLoadContext:
    return ComponentLoadContext(
        path=defs_path / defs_relative_path,
        project_root=project_root,
        defs_module_path=defs_path,
        defs_module_name=defs_module_name,
        resolution_context=ResolutionContext.default(),
    )


def get_project_root(dunder_file: str) -> Path:
    folder = Path(dunder_file).parent
    while not (folder / "pyproject.toml").exists() and folder != folder.parent:
        folder = folder.parent

    if folder == folder.parent:
        raise ValueError("Could not find project root")

    return folder
