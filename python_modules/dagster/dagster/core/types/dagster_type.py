from dagster import check

from .builtin_enum import BuiltinEnum


class WrappingType(object):
    def __init__(self, inner_type):
        # Cannot check inner_type because of circular references and no fwd declarations
        self.inner_type = inner_type


def List(inner_type):
    return WrappingListType(inner_type)


class WrappingListType(WrappingType):
    pass


def Nullable(inner_type):
    return WrappingNullableType(inner_type)


class WrappingNullableType(WrappingType):
    pass


def check_dagster_type_param(dagster_type, param_name, base_type):
    # Cannot check base_type because of circular references and no fwd declarations
    if dagster_type is None:
        return dagster_type
    if isinstance(dagster_type, BuiltinEnum):
        return dagster_type
    if isinstance(dagster_type, WrappingType):
        return dagster_type

    check.param_invariant(
        isinstance(dagster_type, type),
        'dagster_type',
        'Invalid dagster_type got {dagster_type}'.format(dagster_type=dagster_type),
    )

    check.param_invariant(
        issubclass(dagster_type, base_type),
        'dagster_type',
        (
            'Parameter {param_name} must be a valid dagster type: A builtin (e.g. String, Int, '
            'etc), a wrapping type (List or Nullable), or a type class'
        ).format(param_name=param_name),
    )

    return dagster_type
