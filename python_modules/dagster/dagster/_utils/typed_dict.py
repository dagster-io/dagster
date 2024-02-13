from typing import Type, TypeVar, cast

from typing_extensions import NotRequired, get_origin, is_typeddict

_TypedDictClass = TypeVar("_TypedDictClass")


def init_optional_typeddict(cls: Type[_TypedDictClass]) -> _TypedDictClass:
    """Initialize a TypedDict with optional values."""
    from dagster._config.pythonic_config.type_check_utils import is_optional

    if not is_typeddict(cls):
        raise Exception("Must pass a TypedDict class to init_optional_typeddict")
    result = {}
    for key, value in cls.__annotations__.items():
        # If the value is a typed dict, recursively initialize it
        if is_typeddict(value):
            result[key] = init_optional_typeddict(value)
        elif is_optional(value):
            result[key] = None
        elif get_origin(value) is dict:
            result[key] = {}
        elif get_origin(value) is NotRequired:
            continue
        else:
            raise Exception("fields must be either optional or typed dicts")
    return cast(_TypedDictClass, result)
