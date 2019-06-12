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
    from .mapping import remap_python_type

    dagster_type = remap_python_type(dagster_type)

    if dagster_type is None:
        return Any.inst()
    if BuiltinEnum.contains(dagster_type):
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
    is_secret=False,
    description=None,
):
    '''
    The schema for configuration data that describes the type, optionality, defaults, and description.

    Args:
        dagster_type (DagsterType):
            A ``DagsterType`` describing the schema of this field, ie `Dict({'example': Field(String)})`
        default_value (Any):
            A default value to use that respects the schema provided via dagster_type
        is_optional (bool): Whether the presence of this field is optional
        description (str):
    '''
    config_type = resolve_to_config_type(dagster_type)
    if not config_type:
        raise DagsterInvalidDefinitionError(
            (
                'Attempted to pass {value_repr} to a Field that expects a valid '
                'dagster type usable in config (e.g. Dict, NamedDict, Int, String et al).'
            ).format(value_repr=repr(dagster_type))
        )
    return FieldImpl(
        config_type=config_type,
        default_value=default_value,
        is_optional=is_optional,
        is_secret=is_secret,
        description=description,
    )
