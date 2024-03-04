from typing import Type, TypeVar, cast, get_args

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


def validate_typeddict(cls: Type[_TypedDictClass], potential_typeddict: dict) -> _TypedDictClass:
    """Validate a TypedDict."""
    from dagster._config.pythonic_config.type_check_utils import is_optional

    if not is_typeddict(cls):
        raise Exception("Must pass a TypedDict class to validate_typeddict")

    for key, field_type in cls.__annotations__.items():
        if key not in potential_typeddict:
            if get_origin(field_type) is NotRequired:
                continue
            raise Exception(f"Missing required field {key} in {cls.__name__}")
        if is_optional(field_type):
            if potential_typeddict[key] is not None:
                inner_type = next(iter(get_args(field_type)))
                if not isinstance(potential_typeddict[key], inner_type):
                    raise Exception(
                        f"Field {key} must be either None or of type {inner_type.__name__}"
                    )
            else:
                continue

        if is_typeddict(field_type):
            validate_typeddict(field_type, potential_typeddict[key])
        elif get_origin(field_type) is dict:
            if not isinstance(potential_typeddict[key], dict):
                raise Exception(f"Field {key} must be a dictionary")
        elif get_origin(field_type) is NotRequired:
            continue
        elif not isinstance(potential_typeddict[key], field_type):
            raise Exception(f"Field {key} must be of type {field_type.__name__}")
    return cast(_TypedDictClass, potential_typeddict)
