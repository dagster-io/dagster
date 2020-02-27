from enum import Enum as PythonEnum

import six

from dagster import check
from dagster.builtins import BuiltinEnum
from dagster.core.serdes import whitelist_for_serdes


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


class ConfigType(object):
    '''
    The class backing DagsterTypes as they are used processing configuration data.
    '''

    def __init__(
        self, key, kind, given_name=None, description=None, type_params=None,
    ):

        self.key = check.str_param(key, 'key')
        self.kind = check.inst_param(kind, 'kind', ConfigTypeKind)
        self.given_name = check.opt_str_param(given_name, 'given_name')
        self._description = check.opt_str_param(description, 'description')
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

    @property
    def recursive_config_types(self):
        return []

    def post_process(self, value):
        return value


# Scalars, Composites, Selectors, Lists, Optional, Any


class ConfigScalar(ConfigType):
    def __init__(self, key, given_name, **kwargs):
        super(ConfigScalar, self).__init__(
            key, given_name=given_name, kind=ConfigTypeKind.SCALAR, **kwargs
        )

    def is_config_scalar_valid(self, _config_value):
        check.not_implemented('must implement')


class BuiltinConfigScalar(ConfigScalar):
    def __init__(self, description=None):
        super(BuiltinConfigScalar, self).__init__(
            key=type(self).__name__, given_name=type(self).__name__, description=description,
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
            key='Any', given_name='Any', kind=ConfigTypeKind.ANY,
        )


class Noneable(ConfigType):
    def __init__(self, inner_type):
        from .field import resolve_to_config_type

        self.inner_type = resolve_to_config_type(inner_type)
        super(Noneable, self).__init__(
            key='Noneable.{inner_type}'.format(inner_type=self.inner_type.key),
            kind=ConfigTypeKind.NONEABLE,
            type_params=[self.inner_type],
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
        super(Enum, self).__init__(key=name, given_name=name, kind=ConfigTypeKind.ENUM)
        self.enum_values = check.list_param(enum_values, 'enum_values', of_type=EnumValue)
        self._valid_python_values = {ev.python_value for ev in enum_values}
        check.invariant(len(self._valid_python_values) == len(enum_values))
        self._valid_config_values = {ev.config_value for ev in enum_values}
        check.invariant(len(self._valid_config_values) == len(enum_values))

    @property
    def config_values(self):
        return [ev.config_value for ev in self.enum_values]

    def is_valid_config_enum_value(self, config_value):
        return config_value in self._valid_config_values

    def post_process(self, value):
        if isinstance(value, PythonEnum):
            value = value.name

        for ev in self.enum_values:
            if ev.config_value == value:
                return ev.python_value

        check.failed(
            (
                'Should never reach this. config_value should be pre-validated. '
                'Got {config_value}'
            ).format(config_value=value)
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
    def __init__(
        self, scalar_type, non_scalar_type, _key=None,
    ):
        self.scalar_type = check.inst_param(scalar_type, 'scalar_type', ConfigType)
        self.non_scalar_type = check.inst_param(non_scalar_type, 'non_scalar_type', ConfigType)

        check.param_invariant(scalar_type.kind == ConfigTypeKind.SCALAR, 'scalar_type')
        check.param_invariant(
            non_scalar_type.kind
            in {ConfigTypeKind.STRICT_SHAPE, ConfigTypeKind.SELECTOR, ConfigTypeKind.ARRAY},
            'non_scalar_type',
        )

        # https://github.com/dagster-io/dagster/issues/2133
        key = check.opt_str_param(
            _key, '_key', 'ScalarUnion.{}-{}'.format(scalar_type.key, non_scalar_type.key)
        )

        super(ScalarUnion, self).__init__(
            key=key, kind=ConfigTypeKind.SCALAR_UNION, type_params=[scalar_type, non_scalar_type],
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
