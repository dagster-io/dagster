from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types import BuiltinEnum


class WrappingType(object):
    def __init__(self, inner_type):
        # Cannot check inner_type because of circular references and no fwd declarations

        if inner_type == BuiltinEnum.NOTHING:
            raise DagsterInvalidDefinitionError(
                'Type Nothing can not be wrapped in List or Nullable'
            )

        self.inner_type = inner_type


def List(inner_type):
    '''
    Validates at runtime that the value is ``List[inner_type]``.

    Args:
        inner_type (DagsterType)
    '''
    return WrappingListType(inner_type)


class WrappingListType(WrappingType):
    pass


def Nullable(inner_type):
    '''
    Validates at runtime that the type is either ``None`` or passes validation of ``inner_type``

    Args:
        inner_type (DagsterType)
    '''
    # Cannot check inner_type because of circular references and no fwd declarations
    return WrappingNullableType(inner_type)


class WrappingNullableType(WrappingType):
    pass
