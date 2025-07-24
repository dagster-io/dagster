from collections.abc import Sequence
from typing import Any, ForwardRef, Literal, NamedTuple, TypeVar, Union, get_args, get_origin

from typing_extensions import TypeGuard

T = TypeVar("T", bound=Any)


# Use Any for type_ because there isn't a good static type that can handle all the cases listed
# here.
def match_type(obj: object, type_: Union[type[T], tuple[type[T]]]) -> TypeGuard[T]:
    if isinstance(type_, tuple):
        return any(match_type(obj, t) for t in type_)

    origin = get_origin(type_)
    # If typ is not a generic alias, do a normal isinstance check
    if origin is None:
        # If we get here, it's a concrete type like `int`, `str`, or type(None).
        if type_ is Any:
            return True
        elif type_ is NamedTuple:
            return is_named_tuple_instance(obj)
        elif isinstance(type_, ForwardRef):
            raise NotImplementedError(
                f"Got ForwardRef {type_}. ForwardRef is not supported by `match_type`"
            )
        else:
            return isinstance(obj, type_)

    # Handle Union (e.g. Union[int, str])
    if origin is Union:
        subtypes = get_args(type_)  # e.g. (int, str)
        return any(match_type(obj, st) for st in subtypes)

    # Handle Literal (e.g. Literal[3, 5, "hello"])
    if origin is Literal:
        # get_args(typ) will be the allowed literal values
        allowed_values = get_args(type_)  # e.g. (3, 5, "hello")
        return obj in allowed_values

    # Handle list[...] (e.g. list[str])
    if origin is Sequence:
        (item_type,) = get_args(type_)  # e.g. (str,) for list[str]
        if not isinstance(obj, Sequence):
            return False
        return all(match_type(item, item_type) for item in obj)

    # Handle list[...] (e.g. list[str])
    if origin is list:
        (item_type,) = get_args(type_)  # e.g. (str,) for list[str]
        if not isinstance(obj, list):
            return False
        return all(match_type(item, item_type) for item in obj)

    # Handle tuple[...] (e.g. tuple[int, str], tuple[str, ...])
    if origin is tuple:
        arg_types = get_args(type_)
        if not isinstance(obj, tuple):
            return False
        # Distinguish fixed-length vs variable-length (ellipsis) tuples
        if len(arg_types) == 2 and arg_types[1] is Ellipsis:
            # e.g. tuple[str, ...]
            elem_type = arg_types[0]
            return all(match_type(item, elem_type) for item in obj)
        else:
            # e.g. tuple[int, str, float]
            if len(obj) != len(arg_types):
                return False
            return all(match_type(item, t) for item, t in zip(obj, arg_types))

    # Handle dict[...] (e.g. dict[str, int])
    if origin is dict:
        key_type, val_type = get_args(type_)
        if not isinstance(obj, dict):
            return False
        return all(match_type(k, key_type) and match_type(v, val_type) for k, v in obj.items())

    # Extend with other generic types (set, frozenset, etc.) if needed
    raise NotImplementedError(f"No handler for {type_}")


# copied from dagster._utils
def is_named_tuple_instance(obj: object) -> TypeGuard[NamedTuple]:
    return isinstance(obj, tuple) and hasattr(obj, "_fields")


# copied from dagster._utils
def is_named_tuple_subclass(klass: type[object]) -> TypeGuard[type[NamedTuple]]:
    return isinstance(klass, type) and issubclass(klass, tuple) and hasattr(klass, "_fields")
