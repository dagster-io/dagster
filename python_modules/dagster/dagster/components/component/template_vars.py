import inspect
from typing import Any, Callable, Optional, Union, overload

from typing_extensions import TypeAlias

from dagster._symbol_annotations.public import public

TemplateVarFn: TypeAlias = Callable[..., Any]

TEMPLATE_VAR_ATTR = "__dagster_template_var"


@overload
def template_var(fn: TemplateVarFn) -> TemplateVarFn: ...


@overload
def template_var() -> Callable[[TemplateVarFn], TemplateVarFn]: ...


@public
def template_var(
    fn: Optional[TemplateVarFn] = None,
) -> Union[TemplateVarFn, Callable[[TemplateVarFn], TemplateVarFn]]:
    def decorator(func: TemplateVarFn) -> TemplateVarFn:
        setattr(func, TEMPLATE_VAR_ATTR, True)
        return func

    if fn is None:
        return decorator
    else:
        return decorator(fn)


def is_template_var(obj: Any) -> bool:
    return getattr(obj, TEMPLATE_VAR_ATTR, False)


def find_inline_template_vars_in_module(module: Any) -> dict[str, TemplateVarFn]:
    """Finds all template functions in the given module.

    Args:
        module: The module to search for template functions

    Returns:
        dict[str, TemplateVarFn]: A dictionary of template variable functions indexed by name
    """
    return {name: obj for name, obj in inspect.getmembers(module, is_template_var)}


def is_staticmethod(cls, method):
    """Check if a method is a static method by examining the class descriptor.

    Args:
        cls: The class where the method is defined
        method: The method reference (e.g., cls.method_name)

    Returns:
        bool: True if the method is a static method, False otherwise
    """
    # Get the method name from the method reference
    if not hasattr(method, "__name__"):
        return False

    method_name = method.__name__

    # Check the class hierarchy to find where this method is defined
    for base_cls in inspect.getmro(cls):
        if method_name in base_cls.__dict__:
            method_descriptor = base_cls.__dict__[method_name]
            return isinstance(method_descriptor, staticmethod)

    return False


def get_static_template_vars(cls: type, context=None) -> dict[str, TemplateVarFn]:
    """Find all staticmethods in a class that can be used as template variables.

    Args:
        cls: The class to search through
        context: Optional ComponentLoadContext to pass to template variables that accept it

    Returns:
        A dictionary mapping method names to their callable functions for each matching staticmethod
    """
    results = {}
    for name, method in cls.__dict__.items():
        if is_staticmethod(cls, method):
            # Get the actual function from the staticmethod wrapper
            func = method.__get__(None, cls)
            if is_template_var(func):
                sig = inspect.signature(func)
                if len(sig.parameters) == 1:
                    if context is None:
                        # Skip context-requiring functions when no context provided
                        continue
                    results[name] = func(context)
                elif len(sig.parameters) == 0:
                    results[name] = func()
                else:
                    raise ValueError(
                        f"Static template var {name} must have 0 or 1 parameters, got {len(sig.parameters)}"
                    )

    return results


def get_context_aware_static_template_vars(cls: type, context) -> dict[str, TemplateVarFn]:
    """Find staticmethods that require context and invoke them with the provided context.

    Args:
        cls: The class to search through
        context: ComponentLoadContext to pass to template variables

    Returns:
        A dictionary mapping method names to their values for context-requiring staticmethods
    """
    results = {}
    for name, method in cls.__dict__.items():
        if is_staticmethod(cls, method):
            # Get the actual function from the staticmethod wrapper
            func = method.__get__(None, cls)
            if is_template_var(func):
                sig = inspect.signature(func)
                if len(sig.parameters) == 1:
                    results[name] = func(context)
                # Skip 0-parameter functions as they're handled by get_static_template_vars

    return results
