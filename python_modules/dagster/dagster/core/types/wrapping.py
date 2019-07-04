import sys
from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError


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


if sys.version_info.major >= 3:
    import typing

    List = typing.List

    def is_python_list_typehint(type_annotation):
        origin = getattr(type_annotation, '__origin__', None)
        return origin == typing.List or origin == list

    def remap_to_dagster_list_type(type_annotation):
        check.invariant(
            is_python_list_typehint(type_annotation), 'type must pass is_python_list_typehint check'
        )
        return WrappingListType(type_annotation.__args__[0])

    Optional = typing.Optional

    def is_python_optional_typehint(type_annotation):
        # Optional[X] is Union[X, NoneType] which is what we match against here
        origin = getattr(type_annotation, '__origin__', None)
        return (
            origin == typing.Union
            and len(type_annotation.__args__) == 2
            and type_annotation.__args__[1] == type(None)
        )

    def remap_to_dagster_optional_type(type_annotation):
        check.invariant(
            is_python_optional_typehint(type_annotation),
            'type must pass is_python_optional_typehint check',
        )
        return WrappingNullableType(type_annotation.__args__[0])


else:

    class ListStub:
        def __getitem__(self, inner_type):
            return WrappingListType(inner_type)

    List = ListStub()

    def is_python_list_typehint(_):
        return False

    def remap_to_dagster_list_type(_):
        check.failed('Not valid to call in python 2')

    class OptionalStub:
        def __getitem__(self, inner_type):
            return WrappingNullableType(inner_type)

    Optional = OptionalStub()

    def is_python_optional_typehint(_):
        return False

    def remap_to_dagster_optional_type(_):
        check.failed('Not valid to call in python 2')
