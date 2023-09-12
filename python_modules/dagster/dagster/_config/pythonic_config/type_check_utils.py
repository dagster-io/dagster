from typing import Any, Type, Union

try:
    # this type only exists in python 3.10+
    from types import UnionType  # type: ignore
except ImportError:
    UnionType = Union

from typing_extensions import get_args, get_origin


def safe_is_subclass(cls: Any, possible_parent_cls: Type) -> bool:
    """Version of issubclass that returns False if cls is not a Type."""
    if not isinstance(cls, type):
        return False

    try:
        return issubclass(cls, possible_parent_cls)
    except TypeError:
        # Using builtin Python types in python 3.9+ will raise a TypeError when using issubclass
        # even though the isinstance check will succeed (as will inspect.isclass), for example
        # list[dict[str, str]] will raise a TypeError
        return False


def is_optional(annotation: Type) -> bool:
    """Returns true if the annotation is Optional[T] or Union[T, None]."""
    return (
        get_origin(annotation) in (Union, UnionType)
        and len(get_args(annotation)) == 2
        and type(None) in get_args(annotation)
    )
