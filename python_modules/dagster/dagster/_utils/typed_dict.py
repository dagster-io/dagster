from typing import Type, TypedDict, TypeVar, cast, is_typeddict

_TypedDictClass = TypeVar("_TypedDictClass", bound=TypedDict)


def init_optional_typeddict(cls: Type[_TypedDictClass]) -> _TypedDictClass:
    from dagster._config.pythonic_config.type_check_utils import is_optional

    result = {}
    for key, value in cls.__annotations__.items():
        # If the value is a typed dict, recursively initialize it
        if is_typeddict(value):
            result[key] = init_optional_typeddict(value)
        elif is_optional(value):
            result[key] = None
        else:
            raise Exception("fields must be either optional or typed dicts")
    """Initialize a TypedDict with optional values."""
    return cast(_TypedDictClass, result)
