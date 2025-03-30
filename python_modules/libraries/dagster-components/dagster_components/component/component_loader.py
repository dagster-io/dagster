from typing import TYPE_CHECKING, Any, Callable, TypeVar

from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from dagster_components.component.component import Component
    from dagster_components.core.context import ComponentLoadContext

COMPONENT_LOADER_FN_ATTR = "__dagster_component_loader_fn"


T_Component = TypeVar("T_Component", bound="Component")

ComponentLoadFn: TypeAlias = Callable[["ComponentLoadContext"], T_Component]


def component(fn: ComponentLoadFn) -> ComponentLoadFn:
    setattr(fn, COMPONENT_LOADER_FN_ATTR, True)
    return fn


def is_component_loader(obj: Any) -> bool:
    return getattr(obj, COMPONENT_LOADER_FN_ATTR, False)
