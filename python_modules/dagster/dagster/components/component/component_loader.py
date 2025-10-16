from typing import TYPE_CHECKING, Any, Callable, TypeVar

from dagster._annotations import public, superseded

if TYPE_CHECKING:
    from dagster.components.component.component import Component
    from dagster.components.core.context import ComponentLoadContext

COMPONENT_LOADER_FN_ATTR = "__dagster_component_loader_fn"


T_Component = TypeVar("T_Component", bound="Component")


@public
@superseded(additional_warn_text="Use `component_instance` instead.")
def component(
    fn: Callable[["ComponentLoadContext"], T_Component],
) -> Callable[["ComponentLoadContext"], T_Component]:
    """Decorator for a function to be used to load an instance of a Component.
    This is used when instantiating components in python instead of via yaml.

    Example:
        .. code-block:: python

            @component
            def load(context: ComponentLoadContext):
                return MyComponent(
                    asset=AssetSpec('example')
                )
    """
    return component_instance(fn)


@public
def component_instance(
    fn: Callable[["ComponentLoadContext"], T_Component],
) -> Callable[["ComponentLoadContext"], T_Component]:
    """Decorator for a function to be used to load an instance of a Component.
    This is used when instantiating components in python instead of via yaml.

    Example:
        .. code-block:: python

            import dagster as dg

            class MyComponent(dg.Component):
                ...

            @dg.component_instance
            def load(context: dg.ComponentLoadContext) -> MyComponent:
                return MyComponent(...)
    """
    setattr(fn, COMPONENT_LOADER_FN_ATTR, True)
    return fn


def is_component_loader(obj: Any) -> bool:
    return getattr(obj, COMPONENT_LOADER_FN_ATTR, False)
