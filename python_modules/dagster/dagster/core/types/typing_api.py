'''This file contains the typing api that should exist in python in
order to do metaprogramming and reflection on the built-in typing module'''

import sys
import typing

from dagster import check

if sys.version_info.major >= 3:

    def is_python_list_typehint(type_annotation):
        '''Returns true for list, List, and List[T]'''
        if type_annotation is list or type_annotation is typing.List:
            return True
        origin = getattr(type_annotation, '__origin__', None)
        return origin == typing.List or origin == list

    def is_closed_python_optional_typehint(type_annotation):
        # Optional[X] is Union[X, NoneType] which is what we match against here
        origin = getattr(type_annotation, '__origin__', None)
        return (
            origin == typing.Union
            and len(type_annotation.__args__) == 2
            and type_annotation.__args__[1] == type(None)
        )

    def get_optional_inner_type(type_annotation):
        check.invariant(
            is_closed_python_optional_typehint(type_annotation),
            'type must pass is_closed_python_optional_typehint check',
        )

        return type_annotation.__args__[0]


else:

    def is_python_list_typehint(_):
        return False

    def is_closed_python_optional_typehint(_):
        return False

    def get_optional_inner_type(_type_annotation):
        check.failed('Invalid in python 2')
