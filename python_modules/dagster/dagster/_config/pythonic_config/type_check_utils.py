from typing import Any, Literal, Union

from typing_extensions import (
    Literal as ExtLiteral,
    get_origin,
)


def safe_is_subclass(cls: Any, possible_parent_cls: Union[type, tuple[type, ...]]) -> bool:
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


def is_literal(annotation: type) -> bool:
    return get_origin(annotation) in (Literal, ExtLiteral)
