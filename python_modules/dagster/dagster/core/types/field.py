from dagster import check
from .builtin_enum import BuiltinEnum
from .config import Any, ConfigType, List, Nullable
from .field_utils import FieldImpl, FIELD_NO_DEFAULT_PROVIDED, INFER_OPTIONAL_COMPOSITE_FIELD
from .runtime import RuntimeType
from .wrapping import WrappingListType, WrappingNullableType


def resolve_to_config_list(list_type):
    check.inst_param(list_type, 'list_type', WrappingListType)
    return List(resolve_to_config_type(list_type.inner_type))


def resolve_to_config_nullable(nullable_type):
    check.inst_param(nullable_type, 'nullable_type', WrappingNullableType)
    return Nullable(resolve_to_config_type(nullable_type.inner_type))


def resolve_to_config_type(dagster_type):
    if dagster_type is None:
        return Any.inst()
    if isinstance(dagster_type, BuiltinEnum):
        runtime_type = RuntimeType.from_builtin_enum(dagster_type)
        check.invariant(runtime_type.input_schema)
        return runtime_type.input_schema.schema_type
    ## TODO need to check for runtime type. e.g. List(DataFrame)
    if isinstance(dagster_type, WrappingListType):
        return resolve_to_config_list(dagster_type).inst()
    if isinstance(dagster_type, WrappingNullableType):
        return resolve_to_config_nullable(dagster_type).inst()
    if issubclass(dagster_type, ConfigType):
        return dagster_type.inst()

    check.failed('should not reach')


def Field(
    dagster_type,
    default_value=FIELD_NO_DEFAULT_PROVIDED,
    is_optional=INFER_OPTIONAL_COMPOSITE_FIELD,
    description=None,
):
    return FieldImpl(resolve_to_config_type(dagster_type), default_value, is_optional, description)
