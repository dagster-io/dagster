from collections import namedtuple

import six

from dagster import check

from .builtin_enum import BuiltinEnum


class ConfigTypeAttributes(namedtuple('_ConfigTypeAttributes', 'is_builtin is_system_config')):
    def __new__(cls, is_builtin=False, is_system_config=False):
        return super(ConfigTypeAttributes, cls).__new__(
            cls,
            is_builtin=check.bool_param(is_builtin, 'is_builtin'),
            is_system_config=check.bool_param(is_system_config, 'is_system_config'),
        )


DEFAULT_TYPE_ATTRIBUTES = ConfigTypeAttributes()


class ConfigType(object):
    '''
    The class backing DagsterTypes as they are used processing configuration data.
    '''

    def __init__(self, key, name, type_attributes=DEFAULT_TYPE_ATTRIBUTES, description=None):

        type_obj = type(self)
        if type_obj in ConfigType.__cache:
            check.failed(
                (
                    '{type_obj} already in cache. You **must** use the inst() class method '
                    'to construct ConfigTypes and not the ctor'.format(type_obj=type_obj)
                )
            )
        self.key = check.str_param(key, 'key')
        self.name = check.opt_str_param(name, 'name')
        self.description = check.opt_str_param(description, 'description')
        self.type_attributes = check.inst_param(
            type_attributes, 'type_attributes', ConfigTypeAttributes
        )

    __cache = {}

    @classmethod
    def inst(cls):
        if cls not in ConfigType.__cache:
            ConfigType.__cache[cls] = cls()  # pylint: disable=E1120
        return ConfigType.__cache[cls]

    @staticmethod
    def from_builtin_enum(builtin_enum):
        check.invariant(BuiltinEnum.contains(builtin_enum), 'param must be member of BuiltinEnum')
        return _CONFIG_MAP[builtin_enum]

    @property
    def is_system_config(self):
        return self.type_attributes.is_system_config

    @property
    def is_builtin(self):
        return self.type_attributes.is_builtin

    @property
    def has_fields(self):
        return self.is_composite or self.is_selector

    @property
    def is_scalar(self):
        return False

    @property
    def is_list(self):
        return False

    @property
    def is_nullable(self):
        return False

    @property
    def is_composite(self):
        return False

    @property
    def is_selector(self):
        return False

    @property
    def is_any(self):
        return False

    @property
    def inner_types(self):
        return []

    @property
    def is_enum(self):
        return False


# Scalars, Composites, Selectors, Lists, Optional, Any


class ConfigScalar(ConfigType):
    @property
    def is_scalar(self):
        return True

    def is_config_scalar_valid(self, _config_value):
        check.not_implemented('must implement')


class ConfigList(ConfigType):
    def __init__(self, inner_type, *args, **kwargs):
        self.inner_type = check.inst_param(inner_type, 'inner_type', ConfigType)
        super(ConfigList, self).__init__(*args, **kwargs)

    def is_list(self):
        return True

    @property
    def inner_types(self):
        return [self.inner_type] + self.inner_type.inner_types


class ConfigNullable(ConfigType):
    def __init__(self, inner_type, *args, **kwargs):
        self.inner_type = check.inst_param(inner_type, 'inner_type', ConfigType)
        super(ConfigNullable, self).__init__(*args, **kwargs)

    @property
    def is_nullable(self):
        return True

    @property
    def inner_types(self):
        return [self.inner_type] + self.inner_type.inner_types


class ConfigAny(ConfigType):
    @property
    def is_any(self):
        return True


class BuiltinConfigScalar(ConfigScalar):
    def __init__(self, description=None):
        super(BuiltinConfigScalar, self).__init__(
            key=type(self).__name__,
            name=type(self).__name__,
            description=description,
            type_attributes=ConfigTypeAttributes(is_builtin=True),
        )


class Int(BuiltinConfigScalar):
    def __init__(self):
        super(Int, self).__init__(description='')

    def is_config_scalar_valid(self, config_value):
        return not isinstance(config_value, bool) and isinstance(config_value, six.integer_types)


class _StringishBuiltin(BuiltinConfigScalar):
    def is_config_scalar_valid(self, config_value):
        return isinstance(config_value, six.string_types)


class String(_StringishBuiltin):
    def __init__(self):
        super(String, self).__init__(description='')


class Path(_StringishBuiltin):
    def __init__(self):
        super(Path, self).__init__(description='')


class Bool(BuiltinConfigScalar):
    def __init__(self):
        super(Bool, self).__init__(description='')

    def is_config_scalar_valid(self, config_value):
        return isinstance(config_value, bool)


class Float(BuiltinConfigScalar):
    def __init__(self):
        super(Float, self).__init__(description='')

    def is_config_scalar_valid(self, config_value):
        return isinstance(config_value, float)


class Any(ConfigAny):
    def __init__(self):
        super(Any, self).__init__(
            key='Any', name='Any', type_attributes=ConfigTypeAttributes(is_builtin=True)
        )


def Nullable(inner_type):
    check.inst_param(inner_type, 'inner_type', ConfigType)

    class _Nullable(ConfigNullable):
        def __init__(self):
            super(_Nullable, self).__init__(
                key='Optional.{inner_type}'.format(inner_type=inner_type.key),
                name=None,
                type_attributes=ConfigTypeAttributes(is_builtin=True),
                inner_type=inner_type,
            )

    return _Nullable


def List(inner_type):
    check.inst_param(inner_type, 'inner_type', ConfigType)

    class _List(ConfigList):
        def __init__(self):
            # Avoiding a very nasty circular dependency which would require us to restructure the
            # entire module
            from .type_printer import print_config_type_to_string

            super(_List, self).__init__(
                key='List.{inner_type}'.format(inner_type=inner_type.key),
                name=None,
                type_attributes=ConfigTypeAttributes(is_builtin=True),
                inner_type=inner_type,
            )

            self.description = 'List of {inner_type}'.format(
                inner_type=print_config_type_to_string(self, with_lines=False)
            )

    return _List


class EnumValue:
    def __init__(self, config_value, python_value=None, description=None):
        self.config_value = check.str_param(config_value, 'config_value')
        self.python_value = config_value if python_value is None else python_value
        self.description = check.opt_str_param(description, 'description')


class ConfigEnum(ConfigType):
    def __init__(self, name, enum_values):
        check.str_param(name, 'name')
        super(ConfigEnum, self).__init__(key=name, name=name)
        self.enum_values = check.list_param(enum_values, 'enum_values', of_type=EnumValue)
        self._valid_python_values = {ev.python_value for ev in enum_values}
        check.invariant(len(self._valid_python_values) == len(enum_values))
        self._valid_config_values = {ev.config_value for ev in enum_values}
        check.invariant(len(self._valid_config_values) == len(enum_values))

    @property
    def config_values(self):
        return [ev.config_value for ev in self.enum_values]

    @property
    def is_enum(self):
        return True

    def is_valid_config_enum_value(self, config_value):
        return config_value in self._valid_config_values

    def to_python_value(self, config_value):
        for ev in self.enum_values:
            if ev.config_value == config_value:
                return ev.python_value

        check.failed('should never reach this. config_value should be pre-validated')


def Enum(name, enum_values):
    class _EnumType(ConfigEnum):
        def __init__(self):
            super(_EnumType, self).__init__(name=name, enum_values=enum_values)

    return _EnumType


_CONFIG_MAP = {
    BuiltinEnum.ANY: Any.inst(),
    BuiltinEnum.BOOL: Bool.inst(),
    BuiltinEnum.FLOAT: Float.inst(),
    BuiltinEnum.INT: Int.inst(),
    BuiltinEnum.PATH: Path.inst(),
    BuiltinEnum.STRING: String.inst(),
}

ALL_CONFIG_BUILTINS = set(_CONFIG_MAP.values())
