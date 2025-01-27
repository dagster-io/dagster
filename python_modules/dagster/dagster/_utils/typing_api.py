"""This file contains the typing api that should exist in python in
order to do metaprogramming and reflection on the built-in typing module.
"""

import typing

from typing_extensions import get_args, get_origin

import dagster._check as check

try:
    # this type only exists in python 3.10+
    from types import UnionType  # type: ignore
except ImportError:
    UnionType = typing.Union


def is_closed_python_optional_type(annotation) -> bool:
    """Returns true if the annotation signifies an Optional type
    that is closed over a non-None T.

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
    if get_origin(annotation) == typing.Union:
        return len(get_args(annotation)) == 2 and type(None) in get_args(annotation)

    # The Python 3.10 pipe syntax evaluates to a UnionType
    # rather than a Union, so we need to check for that as well
    # UnionType values are equivalent to Unions, e.g. str | None == Union[str, None]
    # but the types themselves are not, e.g. type(str | None) != type(Union[str, None])
    if get_origin(annotation) == UnionType:
        return len(get_args(annotation)) == 2 and type(None) in get_args(annotation)

    return False


def is_python_dict_type(ttype):
    origin = get_origin(ttype)
    return ttype is dict or origin is dict


def is_closed_python_list_type(ttype):
    origin = get_origin(ttype)
    args = get_args(ttype)

    return origin is list and args != ()


def is_closed_python_dict_type(ttype):
    """A "closed" generic type has all of its type parameters parameterized
    by other closed or concrete types.

    e.g.

    Returns true for typing.Dict[int, str] but not for typing.Dict.

    Tests document current behavior (not recursive) -- i.e., typing.Dict[str, Dict] returns True.
    """
    origin = get_origin(ttype)
    args = get_args(ttype)

    return origin is dict and args != ()


def is_closed_python_tuple_type(ttype):
    """A "closed" generic type has all of its type parameters parameterized
    by other closed or concrete types.

    e.g.

    Returns true for Tuple[int] or Tuple[str, int] but false for Tuple or tuple
    """
    origin = get_origin(ttype)
    args = get_args(ttype)

    return origin is tuple and args != ()


def is_closed_python_set_type(ttype):
    """A "closed" generic type has all of its type parameters parameterized
    by other closed or concrete types.

    e.g.

    Returns true for Set[string] but false for Set or set
    """
    origin = get_origin(ttype)
    args = get_args(ttype)

    return origin is set and args != ()


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
        or ttype is typing.Tuple  # noqa: UP006
        or ttype is typing.Set  # noqa: UP006
        or ttype is typing.Dict  # noqa: UP006
        or ttype is typing.List  # noqa: UP006
    )


def flatten_unions(ttype: type) -> typing.AbstractSet[type]:
    """Accepts a type that may be a Union of other types, and returns those other types.
    In addition to explicit Union annotations, works for Optional, which is represented as
    Union[T, None] under the covers.

    E.g. Optional[Union[str, Union[int, float]]] would result in (str, int, float, type(None))
    """
    return set(_flatten_unions_inner(ttype))


def _flatten_unions_inner(ttype: type) -> typing.Iterable[type]:
    if get_origin(ttype) is typing.Union:
        for arg in get_args(ttype):
            yield from flatten_unions(arg)
    else:
        yield ttype
