from dagster import check
from dagster.core.types.config import ConfigType

from dagit.schema import dauphin


def to_dauphin_config_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)

    if config_type.is_enum:
        pass
    elif config_type.has_fields:
        pass
    else:
        pass


class DauphinConfigType(dauphin.Interface):
    class Meta:
        name = 'ConfigType'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()

    inner_types = dauphin.non_null_list('ConfigType')

    is_dict = dauphin.NonNull(dauphin.Boolean)
    is_nullable = dauphin.NonNull(dauphin.Boolean)
    is_list = dauphin.NonNull(dauphin.Boolean)
    is_selector = dauphin.NonNull(dauphin.Boolean)

    is_builtin = dauphin.NonNull(
        dauphin.Boolean,
        description='''
True if the system defines it and it is the same type across pipelines.
Examples include "Int" and "String."''',
    )
    is_system_config = dauphin.NonNull(
        dauphin.Boolean,
        description='''
Dagster generates types for base elements of the config system (e.g. the solids and
context field of the base environment). These types are always present
and are typically not relevant to an end user. This flag allows tool authors to
filter out those types by default.
''',
    )

    is_named = dauphin.NonNull(dauphin.Boolean)


class DauphinRegularConfigType(dauphin.ObjectType):
    class Meta:
        name = 'RegularConfigType'
        interfaces = [DauphinConfigType]


class DauphinEnumConfigType(dauphin.ObjectType):
    def __init__(self, enum_type):
        check.inst_param(enum_type, 'enum_type', ConfigType)
        check.param_invariant(enum_type.is_enum, 'enum_type')
        self._enum_type = enum_type

    class Meta:
        name = 'EnumConfigType'
        interfaces = [DauphinConfigType]

    values = dauphin.non_null_list('EnumConfigValue')


class DauphinEnumConfigValue(dauphin.ObjectType):
    class Meta:
        name = 'EnumConfigValue'

    value = dauphin.NonNull(dauphin.String)
    description = dauphin.String()


class DauphinCompositeConfigType(dauphin.ObjectType):
    def __init__(self, composite_type):
        check.inst_param(composite_type, 'composite_type', ConfigType)
        check.param_invariant(composite_type.has_fields, 'composite_type')
        self._composite_type = composite_type

    class Meta:
        name = 'CompositeConfigType'
        interfaces = [DauphinConfigType]

    fields = dauphin.non_null_list('TypeField')


class DauphinConfigTypeField(dauphin.ObjectType):
    class Meta:
        name = 'ConfigTypeField'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    config_type = dauphin.NonNull('ConfigType')
    default_value = dauphin.String()
    is_optional = dauphin.NonNull(dauphin.Boolean)

    def __init__(self, name, field):
        super(DauphinConfigTypeField, self).__init__(
            name=name,
            description=field.description,
            default_value=field.default_value_as_str if field.default_provided else None,
            is_optional=field.is_optional,
        )
        self._field = field

    def resolve_type(self, info):
        return info.schema.type_named('ConfigType')(self._field.config_type)
