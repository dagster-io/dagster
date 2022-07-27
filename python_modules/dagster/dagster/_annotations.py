import inspect
from functools import wraps
from typing import Callable, Type, TypeVar, cast

import dagster._check as check
from dagster._utils.backcompat import (
    experimental_class_warning,
    experimental_decorator_warning,
    experimental_fn_warning,
)

T_Callable = TypeVar("T_Callable", bound=Callable)

##### PUBLIC


def public(obj: T_Callable) -> T_Callable:
    """
    Mark a method on a public class as public. This distinguishes the method from "internal"
    methods, which are methods that are public in the Python sense of being non-underscored, but
    not intended for user access. Only `public` methods of a class are rendered in the docs.
    """
    check.callable_param(obj, "obj")
    setattr(obj, "_is_public", True)
    return obj


def is_public(fn: Callable) -> bool:
    check.callable_param(fn, "fn")
    return hasattr(fn, "_is_public") and getattr(fn, "_is_public")


##### DEPRECATED


def deprecated(obj: T_Callable) -> T_Callable:
    """
    Mark a class/method/function as deprecated. This appends some metadata to tee fucntion that
    causes it to be rendered with a "deprecated" tag in the docs.

    Note that this decorator does not add any warnings-- they should be added separately.
    """
    check.callable_param(obj, "obj")
    setattr(obj, "_is_deprecated", True)
    return obj


def is_deprecated(fn: Callable) -> bool:
    check.callable_param(fn, "fn")
    return hasattr(fn, "_is_deprecated") and getattr(fn, "_is_deprecated")


##### EXPERIMENTAL


def experimental(obj: T_Callable, *, decorator: bool = False) -> T_Callable:
    """
    Mark a class/method/function as experimental. This appends some metadata to the function that
    causes it to be rendered with an "experimental" tag in the docs.

    Also triggers an "experimental" warning whenever the passed callable is called. If the argument
    is a class, this means the warning will be emitted when the class is instantiated.

    Usage:

        .. code-block:: python

            @experimental
            def my_experimental_function(my_arg):
                do_stuff()

            @experimental
            class MyExperimentalClass:
                pass
    """
    check.callable_param(obj, "fn")
    setattr(obj, "_is_experimental", True)

    if inspect.isfunction(obj):

        warning_fn = experimental_decorator_warning if decorator else experimental_fn_warning

        @wraps(obj)
        def inner(*args, **kwargs):
            warning_fn(obj.__name__, stacklevel=3)
            return obj(*args, **kwargs)

        return cast(T_Callable, inner)

    elif inspect.isclass(obj):

        undecorated_init = obj.__init__

        def __init__(self, *args, **kwargs):
            experimental_class_warning(obj.__name__, stacklevel=3)
            # Tuples must be handled differently, because the undecorated_init does not take any
            # arguments-- they're assigned in __new__.
            if issubclass(cast(Type, obj), tuple):
                undecorated_init(self)
            else:
                undecorated_init(self, *args, **kwargs)

        obj.__init__ = __init__

        return cast(T_Callable, obj)

    else:
        check.failed("obj must be a function or a class")


def is_experimental(obj: Callable) -> bool:
    check.callable_param(obj, "obj")
    return hasattr(obj, "_is_experimental") and getattr(obj, "_is_experimental")
