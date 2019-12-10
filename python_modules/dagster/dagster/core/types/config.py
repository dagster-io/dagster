from collections import namedtuple
from enum import Enum as PythonEnum

import six

from dagster import check
from dagster.core.serdes import whitelist_for_serdes

from .builtin_enum import BuiltinEnum


@whitelist_for_serdes
class ConfigTypeKind(PythonEnum):
    ANY = 'ANY'
    SCALAR = 'SCALAR'
    ENUM = 'ENUM'

    SELECTOR = 'SELECTOR'
    DICT = 'DICT'
    PERMISSIVE_DICT = 'PERMISSIVE_DICT'

    @staticmethod
    def has_fields(kind):
        return (
            kind == ConfigTypeKind.SELECTOR
            or kind == ConfigTypeKind.DICT
            or kind == ConfigTypeKind.PERMISSIVE_DICT
        )

    # Closed generic types
    LIST = 'LIST'
    NULLABLE = 'NULLABLE'
    SET = 'SET'
    TUPLE = 'TUPLE'

    @staticmethod
    def is_closed_generic(kind):
        return (
            kind == ConfigTypeKind.LIST
            or kind == ConfigTypeKind.NULLABLE
            or kind == ConfigTypeKind.SET
            or kind == ConfigTypeKind.TUPLE
        )


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

    def __init__(
        self,
        key,
        name,
        kind,
        type_attributes=DEFAULT_TYPE_ATTRIBUTES,
        description=None,
        type_params=None,
    ):

        self.key = check.str_param(key, 'key')
        self.name = check.opt_str_param(name, 'name')
        self.kind = check.inst_param(kind, 'kind', ConfigTypeKind)
        self._description = check.opt_str_param(description, 'description')
        self.type_attributes = check.inst_param(
            type_attributes, 'type_attributes', ConfigTypeAttributes
        )
        self.type_params = (
            check.list_param(type_params, 'type_params', of_type=ConfigType)
            if type_params
            else None
        )

    @property
    def description(self):
        return self._description

    @staticmethod
    def from_builtin_enum(builtin_enum):
        check.invariant(BuiltinEnum.contains(builtin_enum), 'param must be member of BuiltinEnum')
        return _CONFIG_MAP[builtin_enum]

    # An instantiated List, Tuple, Set, or Nullable
    # e.g. List[Int] or Tuple[Int, Str]
    @property
    def is_closed_generic(self):
        return ConfigTypeKind.is_closed_generic(self.kind)

    @property
    def is_system_config(self):
        return self.type_attributes.is_system_config

    @property
    def is_builtin(self):
        return self.type_attributes.is_builtin

    @property
    def has_fields(self):
        return ConfigTypeKind.has_fields(self.kind)

    @property
    def is_scalar(self):
        return self.kind == ConfigTypeKind.SCALAR

    @property
    def is_list(self):
        return self.kind == ConfigTypeKind.LIST

    @property
    def is_nullable(self):
        return self.kind == ConfigTypeKind.NULLABLE

    @property
    def is_dict(self):
        return self.kind == ConfigTypeKind.DICT or self.kind == ConfigTypeKind.PERMISSIVE_DICT

    @property
    def is_selector(self):
        return self.kind == ConfigTypeKind.SELECTOR

    @property
    def is_any(self):
        return self.kind == ConfigTypeKind.ANY

    @property
    def is_tuple(self):
        return self.kind == ConfigTypeKind.TUPLE

    @property
    def is_set(self):
        return self.kind == ConfigTypeKind.SET

    @property
    def inner_types(self):
        return []

    @property
    def is_enum(self):
        return self.kind == ConfigTypeKind.ENUM

    @property
    def is_permissive_dict(self):
        return self.kind == ConfigTypeKind.PERMISSIVE_DICT


# Scalars, Composites, Selectors, Lists, Optional, Any


class ConfigScalar(ConfigType):
    def __init__(self, key, name, **kwargs):
        super(ConfigScalar, self).__init__(key, name, kind=ConfigTypeKind.SCALAR, **kwargs)

    @property
    def is_scalar(self):
        return True

    def is_config_scalar_valid(self, _config_value):
        check.not_implemented('must implement')


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


class Any(ConfigType):
    def __init__(self):
        super(Any, self).__init__(
            key='Any',
            name='Any',
            kind=ConfigTypeKind.ANY,
            type_attributes=ConfigTypeAttributes(is_builtin=True),
        )


class Nullable(ConfigType):
    def __init__(self, inner_type):
        self.inner_type = check.inst_param(inner_type, 'inner_type', ConfigType)
        super(Nullable, self).__init__(
            key='Optional.{inner_type}'.format(inner_type=inner_type.key),
            name='Optional[{inner_name}]'.format(inner_name=inner_type.name),
            kind=ConfigTypeKind.NULLABLE,
            type_params=[inner_type],
            type_attributes=ConfigTypeAttributes(is_builtin=True),
        )

    @property
    def inner_types(self):
        return [self.inner_type] + self.inner_type.inner_types


class List(ConfigType):
    def __init__(self, inner_type):
        self.inner_type = check.inst_param(inner_type, 'inner_type', ConfigType)
        super(List, self).__init__(
            key='List.{inner_type}'.format(inner_type=inner_type.key),
            name='List[{inner_name}]'.format(inner_name=inner_type.name),
            type_attributes=ConfigTypeAttributes(is_builtin=True),
            type_params=[inner_type],
            kind=ConfigTypeKind.LIST,
        )

    @property
    def description(self):
        from .type_printer import print_config_type_to_string

        return 'List of {inner_type}'.format(
            inner_type=print_config_type_to_string(self, with_lines=False)
        )

    @property
    def inner_types(self):
        return [self.inner_type] + self.inner_type.inner_types


class Set(ConfigType):
    def __init__(self, inner_type):
        self.inner_type = check.inst_param(inner_type, 'inner_type', ConfigType)
        name = 'Set[{inner_type}]'.format(inner_type=inner_type)

        super(Set, self).__init__(
            key='Set.{inner_type}'.format(inner_type=inner_type.key),
            name=name,
            type_attributes=ConfigTypeAttributes(is_builtin=True),
            kind=ConfigTypeKind.SET,
            type_params=[inner_type],
            description=name,
        )

    @property
    def inner_types(self):
        return [self.inner_type] + self.inner_type.inner_types


class Tuple(ConfigType):
    def __init__(self, tuple_types):
        self.tuple_types = check.list_param(tuple_types, 'tuple_types', ConfigType)
        name = 'Tuple[{tuple_types}]'.format(
            tuple_types=', '.join([tuple_type.name for tuple_type in tuple_types])
        )

        super(Tuple, self).__init__(
            key='Tuple.{tuple_types}'.format(
                tuple_types='-'.join([tuple_type.key for tuple_type in tuple_types])
            ),
            name=name,
            type_attributes=ConfigTypeAttributes(is_builtin=True),
            type_params=tuple_types,
            kind=ConfigTypeKind.TUPLE,
            description=name,
        )

    @property
    def inner_types(self):
        return self.type_params + [
            inner_type for tuple_type in self.tuple_types for inner_type in tuple_type.inner_types
        ]


class EnumValue(object):
    '''Define an entry in a :py:func:`Enum`.

    Args:
        config_value (str):
            The string representation of the config to accept when passed.
        python_value (Optional[Any]):
            The python value to convert the enum entry in to. Defaults to the ``config_value``.
        description (Optional[str])

    '''

    def __init__(self, config_value, python_value=None, description=None):
        self.config_value = check.str_param(config_value, 'config_value')
        self.python_value = config_value if python_value is None else python_value
        self.description = check.opt_str_param(description, 'description')


class Enum(ConfigType):
    '''
    Defines a enum configuration type that allows one of a defined set of possible values.

    Args:
        name (str):
        enum_values (List[EnumValue]):

    Example:
        .. code-block:: python

            @solid(
                config_field=Field(
                    Enum(
                        'CowboyType',
                        [
                            EnumValue('good'),
                            EnumValue('bad'),
                            EnumValue('ugly'),
                        ]
                    )
                )
            )
            def resolve_standoff(context):
                # ...
    '''

    def __init__(self, name, enum_values):
        check.str_param(name, 'name')
        super(Enum, self).__init__(key=name, name=name, kind=ConfigTypeKind.ENUM)
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


ConfigAnyInstance = Any()
ConfigBoolInstance = Bool()
ConfigFloatInstance = Float()
ConfigIntInstance = Int()
ConfigPathInstance = Path()
ConfigStringInstance = String()
_CONFIG_MAP = {
    BuiltinEnum.ANY: ConfigAnyInstance,
    BuiltinEnum.BOOL: ConfigBoolInstance,
    BuiltinEnum.FLOAT: ConfigFloatInstance,
    BuiltinEnum.INT: ConfigIntInstance,
    BuiltinEnum.PATH: ConfigPathInstance,
    BuiltinEnum.STRING: ConfigStringInstance,
}

ALL_CONFIG_BUILTINS = set(_CONFIG_MAP.values())
