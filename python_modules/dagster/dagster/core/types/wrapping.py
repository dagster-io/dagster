import sys

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError

from .typing_api import get_optional_inner_type, is_closed_python_optional_type, is_python_list_type


class WrappingType(object):
    def __init__(self, inner_type):
        # Cannot check inner_type because of circular references and no fwd declarations
        from dagster.core.types import BuiltinEnum

        if inner_type == BuiltinEnum.NOTHING:
            raise DagsterInvalidDefinitionError(
                'Type Nothing can not be wrapped in List or Optional'
            )

        self.inner_type = inner_type


class WrappingListType(WrappingType):
    pass


class WrappingNullableType(WrappingType):
    pass


def remap_to_dagster_list_type(ttype):
    check.invariant(is_python_list_type(ttype), 'type must pass is_python_list_type check')
    return WrappingListType(ttype.__args__[0])


def remap_to_dagster_optional_type(ttype):
    check.invariant(
        is_closed_python_optional_type(ttype), 'type must pass is_closed_python_optional_type check'
    )
    return WrappingNullableType(get_optional_inner_type(ttype))


if sys.version_info.major >= 3:
    import typing

    List = typing.List

    Optional = typing.Optional


else:

    class ListStub:
        def __getitem__(self, inner_type):
            return WrappingListType(inner_type)

    List = ListStub()

    class OptionalStub:
        def __getitem__(self, inner_type):
            return WrappingNullableType(inner_type)

    Optional = OptionalStub()
