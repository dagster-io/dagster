from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from .builtin_enum import BuiltinEnum
from .config import Any, ConfigType, List, Nullable
from .field_utils import FieldImpl, FIELD_NO_DEFAULT_PROVIDED, INFER_OPTIONAL_COMPOSITE_FIELD
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
        return ConfigType.from_builtin_enum(dagster_type)
    if isinstance(dagster_type, WrappingListType):
        return resolve_to_config_list(dagster_type).inst()
    if isinstance(dagster_type, WrappingNullableType):
        return resolve_to_config_nullable(dagster_type).inst()
    if isinstance(dagster_type, type) and issubclass(dagster_type, ConfigType):
        return dagster_type.inst()

    return None


def Field(
    dagster_type,
    default_value=FIELD_NO_DEFAULT_PROVIDED,
    is_optional=INFER_OPTIONAL_COMPOSITE_FIELD,
    description=None,
):
    config_type = resolve_to_config_type(dagster_type)
    if not config_type:
        raise DagsterInvalidDefinitionError(
            (
                'Attempted to pass {value_repr} to a Field that expects a valid '
                'dagster type usable in config (e.g. Dict, NamedDict, Int, String et al).'
            ).format(value_repr=repr(dagster_type))
        )
    return FieldImpl(resolve_to_config_type(dagster_type), default_value, is_optional, description)
