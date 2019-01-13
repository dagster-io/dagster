from dagster import check
from .config import ConfigType
from .default_applier import apply_default_values


def all_optional_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)

    if config_type.is_composite or config_type.is_selector:
        for field in config_type.fields.values():
            if not field.is_optional:
                return False
        return True

    return False


class __FieldValueSentinel:
    pass


class __InferOptionalCompositeFieldSentinel:
    pass


FIELD_NO_DEFAULT_PROVIDED = __FieldValueSentinel

INFER_OPTIONAL_COMPOSITE_FIELD = __InferOptionalCompositeFieldSentinel


def check_field_param(obj, param_name):
    return check.inst_param(obj, param_name, FieldImpl)


def check_opt_field_param(obj, param_name):
    return check.opt_inst_param(obj, param_name, FieldImpl)


class FieldImpl:
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
        config_type,
        default_value=FIELD_NO_DEFAULT_PROVIDED,
        is_optional=INFER_OPTIONAL_COMPOSITE_FIELD,
        description=None,
    ):
        self.config_type = check.inst_param(config_type, 'config_type', ConfigType)
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
