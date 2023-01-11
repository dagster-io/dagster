"""This file contains the typing api that should exist in python in
order to do metaprogramming and reflection on the built-in typing module.
"""

import typing

from typing_extensions import get_args, get_origin

import dagster._check as check


def is_closed_python_optional_type(ttype):
    # Optional[X] is Union[X, NoneType] which is what we match against here
    origin = get_origin(ttype)
    args = get_args(ttype)
    return origin is typing.Union and len(args) == 2 and args[1] is type(None)


def is_python_dict_type(ttype):
    origin = get_origin(ttype)
    return ttype is dict or origin is dict


def is_closed_python_list_type(ttype):
    origin = get_origin(ttype)
    args = get_args(ttype)

    return (
        origin is list
        and args != ()
        # py3.7 compat
        and type(args[0]) != typing.TypeVar
    )


def is_closed_python_dict_type(ttype):
    """A "closed" generic type has all of its type parameters parameterized
    by other closed or concrete types.

    e.g.

    Returns true for typing.Dict[int, str] but not for typing.Dict.

    Tests document current behavior (not recursive) -- i.e., typing.Dict[str, Dict] returns True.
    """
    origin = get_origin(ttype)
    args = get_args(ttype)

    return (
        origin is dict
        and args != ()
        # py3.7 compat
        and type(args[0]) != typing.TypeVar
        and type(args[1]) != typing.TypeVar
    )


def is_closed_python_tuple_type(ttype):
    """
    A "closed" generic type has all of its type parameters parameterized
    by other closed or concrete types.

    e.g.

    Returns true for Tuple[int] or Tuple[str, int] but false for Tuple or tuple
    """
    origin = get_origin(ttype)
    args = get_args(ttype)

    return origin is tuple and args != ()


def is_closed_python_set_type(ttype):
    """
    A "closed" generic type has all of its type parameters parameterized
    by other closed or concrete types.

    e.g.

    Returns true for Set[string] but false for Set or set
    """
    origin = get_origin(ttype)
    args = get_args(ttype)

    return (
        origin is set
        and args != ()
        # py3.7 compat
        and type(args[0]) != typing.TypeVar
    )


def get_optional_inner_type(ttype):
    check.invariant(
        is_closed_python_optional_type(ttype), "type must pass is_closed_python_optional_type check"
    )

    return get_args(ttype)[0]


def get_list_inner_type(ttype):
    check.param_invariant(is_closed_python_list_type(ttype), "ttype")
    return get_args(ttype)[0]


def get_set_inner_type(ttype):
    check.param_invariant(is_closed_python_set_type(ttype), "ttype")
    return get_args(ttype)[0]


def get_tuple_type_params(ttype):
    check.param_invariant(is_closed_python_tuple_type(ttype), "ttype")
    return get_args(ttype)


def get_dict_key_value_types(ttype):
    check.param_invariant(is_closed_python_dict_type(ttype), "ttype")
    return get_args(ttype)


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
