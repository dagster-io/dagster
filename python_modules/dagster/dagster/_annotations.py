import inspect
from functools import wraps
from typing import Callable, Optional, Type, TypeVar, Union, cast

from typing_extensions import Annotated, Final, TypeAlias

import dagster._check as check
from dagster._utils.backcompat import (
    experimental_class_warning,
    experimental_decorator_warning,
    experimental_fn_warning,
)

Annotatable: TypeAlias = Union[Callable, property, staticmethod, classmethod]

T_Annotatable = TypeVar("T_Annotatable", bound=Annotatable)

##### PUBLIC


def public(obj: T_Annotatable) -> T_Annotatable:
    """
    Mark a method on a public class as public. This distinguishes the method from "internal"
    methods, which are methods that are public in the Python sense of being non-underscored, but
    not intended for user access. Only `public` methods of a class are rendered in the docs.
    """
    target = _get_target(obj)
    setattr(target, "_is_public", True)
    return obj


def is_public(obj: Annotatable, attr: Optional[str] = None) -> bool:
    target = _get_target(obj, attr)
    return hasattr(target, "_is_public") and getattr(target, "_is_public")


# Use `PublicAttr` to annotate public attributes on `NamedTuple`:
#
# from dagster._annotations import PublicAttr
#
# class Foo(NamedTuple("_Foo", [("bar", PublicAttr[int])])):
#     ...

T = TypeVar("T")

PUBLIC: Final[str] = "public"

PublicAttr: TypeAlias = Annotated[T, PUBLIC]


##### DEPRECATED


def deprecated(obj: T_Annotatable) -> T_Annotatable:
    """
    Mark a class/method/function as deprecated. This appends some metadata to the function that
    causes it to be rendered with a "deprecated" tag in the docs.

    Note that this decorator does not add any warnings-- they should be added separately.
    """
    target = _get_target(obj)
    setattr(target, "_is_deprecated", True)
    return obj


def is_deprecated(obj: Annotatable, attr: Optional[str] = None) -> bool:
    target = _get_target(obj, attr)
    return hasattr(target, "_is_deprecated") and getattr(target, "_is_deprecated")


##### EXPERIMENTAL


def experimental(obj: T_Annotatable, *, decorator: bool = False) -> T_Annotatable:
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
    target = _get_target(obj)
    setattr(target, "_is_experimental", True)

    if isinstance(obj, (property, staticmethod, classmethod)):
        # warning not currently supported for these cases
        return obj  # type: ignore

    elif inspect.isfunction(target):

        warning_fn = experimental_decorator_warning if decorator else experimental_fn_warning

        @wraps(target)
        def inner(*args, **kwargs):
            warning_fn(target.__name__, stacklevel=3)
            return target(*args, **kwargs)

        return cast(T_Annotatable, inner)

    elif inspect.isclass(target):

        undecorated_init = target.__init__

        def __init__(self, *args, **kwargs):
            experimental_class_warning(target.__name__, stacklevel=3)
            # Tuples must be handled differently, because the undecorated_init does not take any
            # arguments-- they're assigned in __new__.
            if issubclass(cast(Type, target), tuple):
                undecorated_init(self)
            else:
                undecorated_init(self, *args, **kwargs)

        target.__init__ = __init__

        return cast(T_Annotatable, obj)

    else:
        check.failed("obj must be a function or a class")


def is_experimental(obj: Annotatable, attr: Optional[str] = None) -> bool:
    target = _get_target(obj, attr)
    return hasattr(target, "_is_experimental") and getattr(target, "_is_experimental")


def _get_target(obj: Annotatable, attr: Optional[str] = None):
    lookup_obj = obj.__dict__[attr] if attr else obj
    return lookup_obj.fget if isinstance(lookup_obj, property) else lookup_obj
