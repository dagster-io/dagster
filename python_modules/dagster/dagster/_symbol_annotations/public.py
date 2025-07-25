import inspect
from typing import Annotated, Final, TypeVar, cast

from dagster._symbol_annotations.annotatable import Annotatable, _get_annotation_target

T_Annotatable = TypeVar("T_Annotatable", bound=Annotatable)

# ########################
# ##### PUBLIC
# ########################

_PUBLIC_ATTR_NAME: Final[str] = "_is_public"


def public(obj: T_Annotatable) -> T_Annotatable:
    """Mark a method or class as public. For methods, this distinguishes them from "internal"
    methods, which are methods that are public in the Python sense of being non-underscored, but
    not intended for user access. Only `public` methods of a class are rendered in the docs.
    When applied to a class, only that specific class is marked public, not its superclasses or subclasses.
    """
    if inspect.isclass(obj):
        # For classes, we need to use type.__setattr__ instead of object.__setattr__
        # This ensures the attribute is set directly on the class's __dict__
        type.__setattr__(obj, _PUBLIC_ATTR_NAME, True)
        return cast("T_Annotatable", obj)
    else:
        target = _get_annotation_target(obj)
        setattr(target, _PUBLIC_ATTR_NAME, True)
        return obj


def is_public(obj: Annotatable) -> bool:
    """Check if a method or class is marked as public. For classes, this only checks
    the specific class, not its superclasses or subclasses.
    """
    if inspect.isclass(obj):
        # Only consider the attribute if it is set directly on the class, not inherited
        return _PUBLIC_ATTR_NAME in getattr(obj, "__dict__", {}) and getattr(obj, _PUBLIC_ATTR_NAME)
    else:
        target = _get_annotation_target(obj)
        return hasattr(target, _PUBLIC_ATTR_NAME) and getattr(target, _PUBLIC_ATTR_NAME)


# Use `PublicAttr` to annotate public attributes on `NamedTuple`:
#
# from dagster._symbol_annotations import PublicAttr
#
# class Foo(NamedTuple("_Foo", [("bar", PublicAttr[int])])):
#     ...

T = TypeVar("T")

PUBLIC: Final[str] = "public"

PublicAttr = Annotated[T, PUBLIC]
