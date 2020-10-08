"""This file contains the typing api that should exist in python in
order to do metaprogramming and reflection on the built-in typing module"""

import typing

from dagster import check


def _get_origin(ttype):
    return getattr(ttype, "__origin__", None)


def is_closed_python_optional_type(ttype):
    # Optional[X] is Union[X, NoneType] which is what we match against here
    origin = _get_origin(ttype)
    return origin == typing.Union and len(ttype.__args__) == 2 and ttype.__args__[1] == type(None)


def is_python_dict_type(ttype):
    if ttype is dict or ttype is typing.Dict:
        return True
    if ttype is None:
        return False

    origin = _get_origin(ttype)
    # py37 origin is typing.Dict, pre-37 is dict
    return origin == typing.Dict or origin == dict


def is_closed_python_list_type(ttype):
    if ttype is None:
        return False
    if ttype is typing.List:
        return False
    if not hasattr(ttype, "__args__"):
        return False
    if ttype.__args__ is None or len(ttype.__args__) != 1:
        return False

    origin = _get_origin(ttype)
    return origin == typing.List or origin is list


def is_closed_python_dict_type(ttype):
    """

    A "closed" generic type has all of its type parameters parameterized
    by other closed or concrete types.

    e.g.

    Returns true for typing.Dict[int, str] but not for typing.Dict
    """
    if ttype is None:
        return False
    if ttype is typing.Dict:
        return False
    if not hasattr(ttype, "__args__"):
        return False
    if ttype.__args__ is None or len(ttype.__args__) != 2:
        return False

    key_type, value_type = ttype.__args__
    origin = _get_origin(ttype)

    # when it is a raw typing.Dict the arguments are instances of TypeVars
    return (
        # py37 origin is typing.Dict, pre-37 is dict
        (origin == typing.Dict or origin is dict)
        and not isinstance(key_type, typing.TypeVar)
        and not isinstance(value_type, typing.TypeVar)
    )


def is_closed_python_tuple_type(ttype):
    """
    A "closed" generic type has all of its type parameters parameterized
    by other closed or concrete types.

    e.g.

    Returns true for Tuple[int] or Tuple[str, int] but false for Tuple or tuple
    """
    if ttype is None:
        return False
    if ttype is typing.Tuple:
        return False
    if not hasattr(ttype, "__args__"):
        return False
    if ttype.__args__ is None:
        return False

    origin = _get_origin(ttype)
    return origin == typing.Tuple or origin is tuple


def is_closed_python_set_type(ttype):
    """
    A "closed" generic type has all of its type parameters parameterized
    by other closed or concrete types.

    e.g.

    Returns true for Set[string] but false for Set or set
    """
    if ttype is None:
        return False
    if ttype is typing.Set:
        return False
    if not hasattr(ttype, "__args__"):
        return False
    if ttype.__args__ is None or len(ttype.__args__) != 1:
        return False

    inner_type = ttype.__args__[0]
    origin = _get_origin(ttype)

    return (origin == typing.Set or origin is set) and not isinstance(inner_type, typing.TypeVar)


def get_optional_inner_type(ttype):
    check.invariant(
        is_closed_python_optional_type(ttype), "type must pass is_closed_python_optional_type check"
    )

    return ttype.__args__[0]


def get_list_inner_type(ttype):
    check.param_invariant(is_closed_python_list_type(ttype), "ttype")
    return ttype.__args__[0]


def get_set_inner_type(ttype):
    check.param_invariant(is_closed_python_set_type(ttype), "ttype")
    return ttype.__args__[0]


def get_tuple_type_params(ttype):
    check.param_invariant(is_closed_python_tuple_type(ttype), "ttype")
    return ttype.__args__


def get_dict_key_value_types(ttype):
    check.param_invariant(is_closed_python_dict_type(ttype), "ttype")
    return (ttype.__args__[0], ttype.__args__[1])


def is_typing_type(ttype):
    return (
        is_closed_python_dict_type(ttype)
        or is_closed_python_optional_type(ttype)
        or is_closed_python_set_type(ttype)
        or is_closed_python_tuple_type(ttype)
        or is_closed_python_list_type(ttype)
        or ttype is typing.Tuple
        or ttype is typing.Set
        or ttype is typing.Dict
        or ttype is typing.List
    )
