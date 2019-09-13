'''This file contains the typing api that should exist in python in
order to do metaprogramming and reflection on the built-in typing module'''

import typing

from dagster import check


def _get_origin(ttype):
    return getattr(ttype, '__origin__', None)


def is_python_list_type(ttype):
    '''Returns true for list, List, and List[T]'''
    if ttype is list or ttype is typing.List:
        return True
    origin = _get_origin(ttype)
    return origin == typing.List or origin == list


def is_closed_python_optional_type(ttype):
    # Optional[X] is Union[X, NoneType] which is what we match against here
    origin = _get_origin(ttype)
    return origin == typing.Union and len(ttype.__args__) == 2 and ttype.__args__[1] == type(None)


def is_python_dict_type(ttype):
    if ttype is dict or ttype is typing.Dict:
        return True
    if not ttype:
        return False

    origin = _get_origin(ttype)
    # py37 origin is typing.Dict, pre-37 is dict
    return origin == typing.Dict or origin == dict


def is_closed_python_dict_type(ttype):
    if not ttype:
        return False
    if ttype is typing.Dict:
        return False
    if not hasattr(ttype, '__args__'):
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


def get_optional_inner_type(ttype):
    check.invariant(
        is_closed_python_optional_type(ttype), 'type must pass is_closed_python_optional_type check'
    )

    return ttype.__args__[0]
