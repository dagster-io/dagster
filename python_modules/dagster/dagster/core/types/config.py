from collections import namedtuple

import six

from dagster import check

from .builtin_enum import BuiltinEnum

# from .dagster_type import check_dagster_type_param
from .wrapping import WrappingListType, WrappingNullableType


class ConfigTypeAttributes(
    namedtuple('_ConfigTypeAttributes', 'is_builtin is_system_config is_named')
):
    def __new__(cls, is_builtin=False, is_system_config=False, is_named=True):
        return super(ConfigTypeAttributes, cls).__new__(
            cls,
            is_builtin=check.bool_param(is_builtin, 'is_builtin'),
            is_system_config=check.bool_param(is_system_config, 'is_system_config'),
            is_named=check.bool_param(is_named, 'is_named'),
        )


DEFAULT_TYPE_ATTRIBUTES = ConfigTypeAttributes()


class ConfigType(object):
    def __init__(self, name=None, type_attributes=DEFAULT_TYPE_ATTRIBUTES, description=None):

        type_obj = type(self)
        if type_obj in ConfigType.__cache:
            check.failed(
                (
                    '{type_obj} already in cache. You **must** use the inst() class method '
                    'to construct ConfigTypes and not the ctor'.format(type_obj=type_obj)
                )
            )

        self.name = check.opt_str_param(name, 'name', type(self).__name__)
        self.description = check.opt_str_param(description, 'description')
        self.type_attributes = check.inst_param(
            type_attributes, 'type_attributes', ConfigTypeAttributes
        )

    __cache = {}

    @classmethod
    def inst(cls):
        if cls not in ConfigType.__cache:
            ConfigType.__cache[cls] = cls()
        return ConfigType.__cache[cls]

    @staticmethod
    def from_builtin_enum(builtin_enum):
        check.inst_param(builtin_enum, 'builtin_enum', BuiltinEnum)
        return _CONFIG_MAP[builtin_enum]

    @property
    def is_system_config(self):
        return self.type_attributes.is_system_config

    @property
    def is_builtin(self):
        return self.type_attributes.is_builtin

    @property
    def is_named(self):
        return self.type_attributes.is_named

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


# Scalars, Composites, Selectors, Lists, Nullable, Any


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
    def __init__(self, name=None, description=None):
        super(BuiltinConfigScalar, self).__init__(
            name=name,
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
        super(Any, self).__init__(type_attributes=ConfigTypeAttributes(is_builtin=True))


def Nullable(inner_type):
    check.inst_param(inner_type, 'inner_type', ConfigType)

    class _Nullable(ConfigNullable):
        def __init__(self):
            super(_Nullable, self).__init__(
                name='Nullable.{inner_type}'.format(inner_type=inner_type.name),
                type_attributes=ConfigTypeAttributes(is_builtin=True, is_named=False),
                inner_type=inner_type,
            )

    return _Nullable


def List(inner_type):
    check.inst_param(inner_type, 'inner_type', ConfigType)

    class _List(ConfigList):
        def __init__(self):
            super(_List, self).__init__(
                name='List.{inner_type}'.format(inner_type=inner_type.name),
                description='List of {inner_type}'.format(inner_type=inner_type.name),
                type_attributes=ConfigTypeAttributes(is_builtin=True, is_named=False),
                inner_type=inner_type,
            )

    return _List


def resolve_to_config_list(list_type):
    check.inst_param(list_type, 'list_type', WrappingListType)
    return List(resolve_to_config_type(list_type.inner_type))


def resolve_to_config_nullable(nullable_type):
    check.inst_param(nullable_type, 'nullable_type', WrappingNullableType)
    return Nullable(resolve_to_config_type(nullable_type.inner_type))


def resolve_to_config_type(dagster_type):
    if dagster_type is None:
        return ConfigAny.inst()
    if isinstance(dagster_type, BuiltinEnum):
        return ConfigType.from_builtin_enum(dagster_type)
    if isinstance(dagster_type, WrappingListType):
        return resolve_to_config_list(dagster_type).inst()
    if isinstance(dagster_type, WrappingNullableType):
        return resolve_to_config_nullable(dagster_type).inst()
    if issubclass(dagster_type, ConfigType):
        return dagster_type.inst()

    check.failed('should not reach')


_CONFIG_MAP = {
    BuiltinEnum.ANY: Any.inst(),
    BuiltinEnum.STRING: String.inst(),
    BuiltinEnum.INT: Int.inst(),
    BuiltinEnum.BOOL: Bool.inst(),
    BuiltinEnum.PATH: Path.inst(),
}
