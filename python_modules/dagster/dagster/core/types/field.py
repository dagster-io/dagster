from dagster import check
from .builtin_enum import BuiltinEnum
from .config import (
    Any,
    Bool,
    ConfigType,
    ConfigTypeAttributes,
    Int,
    Path,
    String,
    resolve_to_config_type,
    DEFAULT_TYPE_ATTRIBUTES,
)
from .dagster_type import check_dagster_type_param


class __FieldValueSentinel:
    pass


class __InferOptionalCompositeFieldSentinel:
    pass


FIELD_NO_DEFAULT_PROVIDED = __FieldValueSentinel

INFER_OPTIONAL_COMPOSITE_FIELD = __InferOptionalCompositeFieldSentinel


def check_config_cls_param(config_cls, param_name):
    if isinstance(config_cls, BuiltinEnum):
        return get_config_cls(config_cls)

    check.invariant(isinstance(config_cls, type))
    check.param_invariant(issubclass(config_cls, ConfigType), param_name)
    return config_cls


def all_optional_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)

    if config_type.is_composite or config_type.is_selector:
        for field in config_type.fields.values():
            if not field.is_optional:
                return False
        return True

    return False


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
                from .evaluator import hard_create_config_value

                self._default_value = lambda: hard_create_config_value(self.config_type, None)
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


def get_config_cls(builtin_enum):
    check.inst_param(builtin_enum, 'builtin_enum', BuiltinEnum)
    return _CONFIG_CLS_MAP[builtin_enum]


_CONFIG_CLS_MAP = {
    BuiltinEnum.ANY: Any,
    BuiltinEnum.STRING: String,
    BuiltinEnum.INT: Int,
    BuiltinEnum.BOOL: Bool,
    BuiltinEnum.PATH: Path,
}


class _ConfigHasFields(ConfigType):
    def __init__(self, fields, *args, **kwargs):

        self.fields = check.dict_param(fields, 'fields', key_type=str, value_type=Field)
        super(_ConfigHasFields, self).__init__(*args, **kwargs)

    @property
    def inner_types(self):
        return list(set(self._yield_inner_types()))

    def _yield_inner_types(self):
        for field in self.fields.values():
            yield field.config_type
            for inner_type in field.config_type.inner_types:
                yield inner_type


class _ConfigComposite(_ConfigHasFields):
    @property
    def is_composite(self):
        return True


class _ConfigSelector(_ConfigHasFields):
    @property
    def is_selector(self):
        return True


# HACK HACK HACK
#
# This is not good and a better solution needs to be found. In order
# for the client-side typeahead in dagit to work as currently structured,
# dictionaries need names. While we deal with that we're going to automatically
# name dictionaries. This will cause odd behavior and bugs is you restart
# the server-side process, the type names changes, and you do not refresh the client.
#
# A possible short term mitigation would to name the dictionary based on the hash
# of its member fields to provide stability in between process restarts.
#
class DictCounter:
    _count = 0

    @staticmethod
    def get_next_count():
        DictCounter._count += 1
        return DictCounter._count


def NamedDict(name, fields, description=None, type_attributes=DEFAULT_TYPE_ATTRIBUTES):
    class _NamedDict(_ConfigComposite):
        def __init__(self):
            super(_NamedDict, self).__init__(
                name=name, fields=fields, description=description, type_attributes=type_attributes
            )

    return _NamedDict


def Dict(fields):
    class _Dict(_ConfigComposite):
        def __init__(self):
            super(_Dict, self).__init__(
                name='Dict.' + str(DictCounter.get_next_count()),
                fields=fields,
                description='A configuration dictionary with typed fields',
                type_attributes=ConfigTypeAttributes(is_named=True, is_builtin=True),
            )

    return _Dict


def Selector(fields):
    class _Selector(_ConfigSelector):
        def __init__(self):
            super(_Selector, self).__init__(
                name='Selector.' + str(DictCounter.get_next_count()),
                fields=fields,
                # description='A configuration dictionary with typed fields',
                type_attributes=ConfigTypeAttributes(is_named=True, is_builtin=True),
            )

    return _Selector


def NamedSelector(name, fields, description=None, type_attributes=DEFAULT_TYPE_ATTRIBUTES):
    class _NamedSelector(_ConfigSelector):
        def __init__(self):
            super(_NamedSelector, self).__init__(
                name=name, fields=fields, description=description, type_attributes=type_attributes
            )

    return _NamedSelector
