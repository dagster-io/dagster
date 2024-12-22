from typing import Callable, Optional, TypeVar, Union

from typing_extensions import TypeAlias

from dagster_components import Component, ComponentLoadContext

TComponent = TypeVar("TComponent", bound="Component")

ComponentDeclarationFn: TypeAlias = Callable[[ComponentLoadContext], TComponent]

IS_COMPONENT_DECL_KEY = "__dagster_component_declaration"


def component_declaration(
    func: Optional[ComponentDeclarationFn] = None,
) -> Union[
    Callable[[ComponentDeclarationFn], ComponentDeclarationFn],
    ComponentDeclarationFn,
]:
    """Indicates that the function is a component declaration. Must be annotated by concrete
    type of the component it decorates in order to function.

    A decorator that attaches a key "__dagster_component_declaration" to the function it
    decorates.  It can be used with or without parentheses. The decorated function
    must accept a ComponentLoadContext and return a type that inherits from Component.

    Args:
        func (Optional[Callable[[ComponentLoadContext], TComponent]]): The function to decorate.

    Returns:
        Union[Callable[[Callable[[ComponentLoadContext], TComponent]], Callable[[ComponentLoadContext], TComponent]], Callable[[ComponentLoadContext], TComponent]]:
        If used without parentheses, returns the decorated function. If used with parentheses, returns a decorator.
    """

    def decorator(f: ComponentDeclarationFn) -> ComponentDeclarationFn:
        setattr(f, IS_COMPONENT_DECL_KEY, True)
        return f

    if func is None:
        return decorator
    else:
        return decorator(func)


def is_component_declaration(func: Callable) -> bool:
    """Checks if a function has been annotated with the @component_declaration decorator.

    Args:
        func (Callable): The function to check.

    Returns:
        bool: True if the function has the "__dagster_component_declaration" attribute, False otherwise.
    """
    return getattr(func, IS_COMPONENT_DECL_KEY, False)
