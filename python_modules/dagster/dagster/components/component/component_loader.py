from typing import TYPE_CHECKING, Any, Callable, TypeVar

if TYPE_CHECKING:
    from dagster.components.component.component import Component
    from dagster.components.core.context import ComponentLoadContext

COMPONENT_LOADER_FN_ATTR = "__dagster_component_loader_fn"


T_Component = TypeVar("T_Component", bound="Component")


def component(
    fn: Callable[["ComponentLoadContext"], T_Component],
) -> Callable[["ComponentLoadContext"], T_Component]:
    setattr(fn, COMPONENT_LOADER_FN_ATTR, True)
    return fn


def is_component_loader(obj: Any) -> bool:
    return getattr(obj, COMPONENT_LOADER_FN_ATTR, False)
