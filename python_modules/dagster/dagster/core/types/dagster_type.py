from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError

from .builtin_enum import BuiltinEnum
from .wrapping import WrappingType


MAGIC_RUNTIME_TYPE_NAME = '__runtime_type'


def is_runtime_type_decorated_klass(klass):
    check.type_param(klass, 'klass')
    return hasattr(klass, MAGIC_RUNTIME_TYPE_NAME)


def check_dagster_type_param(dagster_type, param_name, base_type):

    # Cannot check base_type because of circular references and no fwd declarations
    if dagster_type is None:
        return dagster_type
    if BuiltinEnum.contains(dagster_type):
        return dagster_type
    if isinstance(dagster_type, WrappingType):
        return dagster_type

    if not isinstance(dagster_type, type):
        raise DagsterInvalidDefinitionError(
            'Invalid type for "{param_name}": dagster_type is not an instance of "type", got {dagster_type}'.format(
                param_name=param_name, dagster_type=dagster_type
            )
        )

    if is_runtime_type_decorated_klass(dagster_type):
        return dagster_type

    if not issubclass(dagster_type, base_type):
        raise DagsterInvalidDefinitionError(
            (
                'Parameter {param_name} must be a valid dagster type: A builtin (e.g. String, Int, '
                'etc), a wrapping type (List or Optional), or a type class. Got {dagster_type}'
            ).format(param_name=param_name, dagster_type=dagster_type)
        )

    return dagster_type
