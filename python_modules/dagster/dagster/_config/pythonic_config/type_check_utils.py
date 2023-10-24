from typing import Any, Literal, Type, Union

from typing_extensions import Literal as ExtLiteral

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
    """Returns true if the annotation signifies an Optional type.

    In particular, this can be:
    - Optional[T]
    - Union[T, None]
    - Union[None, T]
    - T | None (in Python 3.10+)
    - None | T (in Python 3.10+).

    """
    # Optional[T] is equivalent to Union[T, None], see
    # https://docs.python.org/3/library/typing.html#typing.Optional
    # A user could also specify a Union themselves
    if get_origin(annotation) == Union:
        return len(get_args(annotation)) == 2 and type(None) in get_args(annotation)

    # The Python 3.10 pipe syntax evaluates to a UnionType
    # rather than a Union, so we need to check for that as well
    # UnionType values are equivalent to Unions, e.g. str | None == Union[str, None]
    # but the types themselves are not, e.g. type(str | None) != type(Union[str, None])
    if get_origin(annotation) == UnionType:
        return len(get_args(annotation)) == 2 and type(None) in get_args(annotation)

    return False


def is_literal(annotation: Type) -> bool:
    return get_origin(annotation) in (Literal, ExtLiteral)
