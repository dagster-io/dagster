from dagster import check
from .builtin_enum import BuiltinEnum
from .config import (
    Any,
    Bool,
    ConfigType,
    ConfigTypeAttributes,
    Int,
    Path,
    List,
    Nullable,
    String,
    DEFAULT_TYPE_ATTRIBUTES,
)
from .dagster_type import check_dagster_type_param
from .default_applier import apply_default_values
from .wrapping import WrappingListType, WrappingNullableType


class __FieldValueSentinel:
    pass


class __InferOptionalCompositeFieldSentinel:
    pass


FIELD_NO_DEFAULT_PROVIDED = __FieldValueSentinel

INFER_OPTIONAL_COMPOSITE_FIELD = __InferOptionalCompositeFieldSentinel


def all_optional_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)

    if config_type.is_composite or config_type.is_selector:
        for field in config_type.fields.values():
            if not field.is_optional:
                return False
        return True

    return False


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
    if issubclass(dagster_type, ConfigType):
        return dagster_type.inst()

    check.failed('should not reach')


class Field:
    '''
    A field in a config object.

    Attributes:
        config_type (ConfigType): The type of the field.
        default_value (Any):
            If the Field is optional, a default value can be provided when the field value
            is not specified.
        is_optional (bool): Is the field optional.
        description (str): Description of the field.
    '''

    def __init__(
        self,
        dagster_type,
        default_value=FIELD_NO_DEFAULT_PROVIDED,
        is_optional=INFER_OPTIONAL_COMPOSITE_FIELD,
        description=None,
    ):
        check_dagster_type_param(dagster_type, 'dagster_type', ConfigType)
        self.config_type = resolve_to_config_type(dagster_type)
        self.config_cls = type(self.config_type)

        self.description = check.opt_str_param(description, 'description')
        if is_optional == INFER_OPTIONAL_COMPOSITE_FIELD:
            is_optional = all_optional_type(self.config_type)
            if is_optional is True:
                self._default_value = apply_default_values(self.config_type, None)
            else:
                self._default_value = default_value
        else:
            is_optional = check.bool_param(is_optional, 'is_optional')
            self._default_value = default_value

        if is_optional is False:
            check.param_invariant(
                default_value == FIELD_NO_DEFAULT_PROVIDED,
                'default_value',
                'required arguments should not specify default values',
            )

        self.is_optional = is_optional

    @property
    def is_required(self):
        return not self.is_optional

    @property
    def default_provided(self):
        '''Was a default value provided

        Returns:
            bool: Yes or no
        '''
        return self._default_value != FIELD_NO_DEFAULT_PROVIDED

    @property
    def default_value(self):
        check.invariant(self.default_provided, 'Asking for default value when none was provided')

        if callable(self._default_value):
            return self._default_value()

        return self._default_value

    @property
    def default_value_as_str(self):
        check.invariant(self.default_provided, 'Asking for default value when none was provided')

        if callable(self._default_value):
            return repr(self._default_value)

        return str(self._default_value)
