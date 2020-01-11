from collections import namedtuple
from enum import Enum as PythonEnum

import six

from dagster import check
from dagster.core.serdes import whitelist_for_serdes
from dagster.core.types.builtins import BuiltinEnum


@whitelist_for_serdes
class ConfigTypeKind(PythonEnum):
    ANY = 'ANY'
    SCALAR = 'SCALAR'
    ENUM = 'ENUM'

    SELECTOR = 'SELECTOR'
    STRICT_SHAPE = 'STRICT_SHAPE'
    PERMISSIVE_SHAPE = 'PERMISSIVE_SHAPE'
    SCALAR_UNION = 'SCALAR_UNION'

    @staticmethod
    def has_fields(kind):
        check.inst_param(kind, 'kind', ConfigTypeKind)
        return kind == ConfigTypeKind.SELECTOR or ConfigTypeKind.is_shape(kind)

    # Closed generic types
    ARRAY = 'ARRAY'
    NONEABLE = 'NONEABLE'

    @staticmethod
    def is_closed_generic(kind):
        check.inst_param(kind, 'kind', ConfigTypeKind)
        return kind == ConfigTypeKind.ARRAY or kind == ConfigTypeKind.NONEABLE

    @staticmethod
    def is_shape(kind):
        check.inst_param(kind, 'kind', ConfigTypeKind)
        return kind == ConfigTypeKind.STRICT_SHAPE or kind == ConfigTypeKind.PERMISSIVE_SHAPE


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

    # An instantiated List, Tuple, Set, or Noneable
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
    def recursive_config_types(self):
        return []


# Scalars, Composites, Selectors, Lists, Optional, Any


class ConfigScalar(ConfigType):
    def __init__(self, key, name, **kwargs):
        super(ConfigScalar, self).__init__(key, name, kind=ConfigTypeKind.SCALAR, **kwargs)

    # @property
    # def is_scalar(self):
    #     return True

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


class Noneable(ConfigType):
    def __init__(self, inner_type):
        from .field import resolve_to_config_type

        self.inner_type = resolve_to_config_type(inner_type)
        super(Noneable, self).__init__(
            key='Noneable.{inner_type}'.format(inner_type=self.inner_type.key),
            name='Noneable[{inner_name}]'.format(inner_name=self.inner_type.name),
            kind=ConfigTypeKind.NONEABLE,
            type_params=[self.inner_type],
            type_attributes=ConfigTypeAttributes(is_builtin=True),
        )

    @property
    def recursive_config_types(self):
        return [self.inner_type] + self.inner_type.recursive_config_types


class Array(ConfigType):
    def __init__(self, inner_type):
        from .field import resolve_to_config_type

        self.inner_type = resolve_to_config_type(inner_type)
        super(Array, self).__init__(
            key='Array.{inner_type}'.format(inner_type=self.inner_type.key),
            name='Array[{inner_name}]'.format(inner_name=self.inner_type.name),
            type_attributes=ConfigTypeAttributes(is_builtin=True),
            type_params=[self.inner_type],
            kind=ConfigTypeKind.ARRAY,
        )

    @property
    def description(self):
        from .type_printer import print_config_type_to_string

        return 'List of {inner_type}'.format(
            inner_type=print_config_type_to_string(self, with_lines=False)
        )

    @property
    def recursive_config_types(self):
        return [self.inner_type] + self.inner_type.recursive_config_types


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
                config=Field(
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

        check.failed(
            (
                'Should never reach this. config_value should be pre-validated. '
                'Got {config_value}'
            ).format(config_value=config_value)
        )

    @classmethod
    def from_python_enum(cls, enum, name=None):
        '''
        Create a Dagster enum corresponding to an existing Python enum.

        Args:
            enum (enum.EnumMeta):
                The class representing the enum.
            name (Optional[str]):
                The name for the enum. If not present, `enum.__name__` will be used.

        Example:
            .. code-block:: python
                class Color(enum.Enum):
                    RED = enum.auto()
                    GREEN = enum.auto()
                    BLUE = enum.auto()

                @solid(
                    config={"color": Field(Enum.from_python_enum(Color))}
                )
                def select_color(context):
                    # ...
        '''
        if name is None:
            name = enum.__name__
        return cls(name, [EnumValue(v.name, python_value=v) for v in enum])


class ScalarUnion(ConfigType):
    def __init__(self, scalar_type, non_scalar_type):
        self.scalar_type = check.inst_param(scalar_type, 'scalar_type', ConfigType)
        self.non_scalar_type = check.inst_param(non_scalar_type, 'non_scalar_type', ConfigType)
        key = 'ScalarUnion.{}-{}'.format(scalar_type.key, non_scalar_type.key)
        name = 'ScalarUnion[{},{}]'.format(scalar_type.name, non_scalar_type.name)
        super(ScalarUnion, self).__init__(
            key=key,
            name=name,
            kind=ConfigTypeKind.SCALAR_UNION,
            type_params=[scalar_type, non_scalar_type],
        )


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
