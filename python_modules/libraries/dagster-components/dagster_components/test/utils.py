from typing import Optional, TypeVar

from dagster._core.definitions.definitions_class import Definitions
from dagster_shared import check

from dagster_components import Component, ComponentLoadContext
from dagster_components.component.component_loader import ComponentLoadFn, is_component_loader

TComponent = TypeVar("TComponent", bound=Component)


def load_component_defs(
    *,
    context: Optional["ComponentLoadContext"] = None,
    component_fn: ComponentLoadFn,
) -> Definitions:
    check.param_invariant(
        is_component_loader(component_fn),
        "component_fn",
        "Component function must be decorated with @component.",
    )
    context = context or ComponentLoadContext.for_test()
    component_inst = component_fn(context)
    return component_inst.build_defs(context)
