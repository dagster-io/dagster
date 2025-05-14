from typing import TYPE_CHECKING, Any, Callable, TypeVar

from dagster._annotations import preview, public

if TYPE_CHECKING:
    from dagster.components.component.component import Component
    from dagster.components.core.context import ComponentLoadContext

COMPONENT_LOADER_FN_ATTR = "__dagster_component_loader_fn"


T_Component = TypeVar("T_Component", bound="Component")


@public
@preview(emit_runtime_warning=False)
def component(
    fn: Callable[["ComponentLoadContext"], T_Component],
) -> Callable[["ComponentLoadContext"], T_Component]:
    """Decorator for a function to be used to load an instance of a Component.
    This is used when instantiating components in python instead of via yaml.
    """
    setattr(fn, COMPONENT_LOADER_FN_ATTR, True)
    return fn


def is_component_loader(obj: Any) -> bool:
    return getattr(obj, COMPONENT_LOADER_FN_ATTR, False)
