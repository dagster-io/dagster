#
# Note: When migrate dagit to use the runtime and config types instead
# the weird type shims this entire file should be deleted -- schrockn (01/23/2019)
from dagit.schema import dauphin

from dagster import check
from dagster.core.types.config import ConfigType, DEFAULT_TYPE_ATTRIBUTES
from dagster.core.types.runtime import RuntimeType


class DauphinTypeAttributes(dauphin.ObjectType):
    class Meta:
        name = 'TypeAttributes'

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


class DauphinType(dauphin.Interface):
    class Meta:
        name = 'Type'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type_attributes = dauphin.NonNull('TypeAttributes')

    is_dict = dauphin.NonNull(dauphin.Boolean)
    is_nullable = dauphin.NonNull(dauphin.Boolean)
    is_list = dauphin.NonNull(dauphin.Boolean)
    is_selector = dauphin.NonNull(dauphin.Boolean)

    inner_types = dauphin.non_null_list('Type')

    @classmethod
    def to_dauphin_type(cls, info, config_or_runtime_type):
        if isinstance(config_or_runtime_type, ConfigType) and config_or_runtime_type.has_fields:
            return info.schema.type_named('CompositeType')(config_or_runtime_type)
        elif isinstance(config_or_runtime_type, ConfigType) and config_or_runtime_type.is_enum:
            return info.schema.type_named('EnumType')(config_or_runtime_type)
        else:
            return info.schema.type_named('RegularType')(config_or_runtime_type)


class DauphinRegularType(dauphin.ObjectType):
    class Meta:
        name = 'RegularType'
        interfaces = [DauphinType]

    def __init__(self, runtime_type):

        super(DauphinRegularType, self).__init__(**ctor_kwargs(runtime_type))
        self._runtime_type = runtime_type

    def resolve_type_attributes(self, _info):
        return type_attributes(self._runtime_type)

    def resolve_inner_types(self, info):
        return inner_types(info, self._runtime_type)


# Section: Type Reconciliation
# These are a temporary set of functions that should be eliminated
# once dagit is aware of the config vs runtime systems and the
# graphql schema updated accordingly
#
# DauphinType.to_dauphin_type also qualifies as a function that is
# aware of the two type systems
#
def all_types(pipeline):
    runtime_types = pipeline.all_runtime_types()

    all_types_dicts = {rt.name: rt for rt in runtime_types}

    for config_type in pipeline.all_config_types():
        all_types_dicts[config_type.name] = config_type
    return list(all_types_dicts.values())


def ctor_kwargs(runtime_or_config_type):
    if isinstance(runtime_or_config_type, RuntimeType):
        return dict(
            name=runtime_or_config_type.name,
            description=runtime_or_config_type.description,
            is_dict=False,
            is_selector=False,
            is_nullable=runtime_or_config_type.is_nullable,
            is_list=runtime_or_config_type.is_list,
        )
    elif isinstance(runtime_or_config_type, ConfigType):
        return dict(
            name=runtime_or_config_type.name,
            description=runtime_or_config_type.description,
            is_dict=runtime_or_config_type.has_fields,
            is_selector=runtime_or_config_type.is_selector,
            is_nullable=runtime_or_config_type.is_nullable,
            is_list=runtime_or_config_type.is_list,
        )
    else:
        check.failed('Not a valid type inst')


def type_attributes(runtime_type):
    if isinstance(runtime_type, RuntimeType):
        return DEFAULT_TYPE_ATTRIBUTES
    elif isinstance(runtime_type, ConfigType):
        return runtime_type.type_attributes
    else:
        check.failed('')


def inner_types_of_runtime(info, runtime_type):
    if runtime_type.is_list or runtime_type.is_nullable:
        return [DauphinType.to_dauphin_type(info, runtime_type.inner_type)]
    else:
        return []


def inner_types_of_config(info, config_type):
    return [DauphinType.to_dauphin_type(info, inner_type) for inner_type in config_type.inner_types]


def inner_types(info, runtime_type):
    if isinstance(runtime_type, RuntimeType):
        return inner_types_of_runtime(info, runtime_type)
    elif isinstance(runtime_type, ConfigType):
        return inner_types_of_config(info, runtime_type)
    else:
        check.failed('')


# End Type Reconciliation section


class DauphinCompositeType(dauphin.ObjectType):
    class Meta:
        name = 'CompositeType'
        interfaces = [DauphinType]

    fields = dauphin.non_null_list('TypeField')

    def __init__(self, type_with_fields):
        super(DauphinCompositeType, self).__init__(**ctor_kwargs(type_with_fields))
        self._type_with_fields = type_with_fields

    def resolve_inner_types(self, info):
        return inner_types(info, self._type_with_fields)

    def resolve_type_attributes(self, _info):
        return type_attributes(self._type_with_fields)

    def resolve_fields(self, info):
        return [
            info.schema.type_named('TypeField')(name=k, field=v)
            for k, v in self._type_with_fields.fields.items()
        ]


class DauphinEnumValue(dauphin.ObjectType):
    class Meta:
        name = 'EnumValue'

    value = dauphin.NonNull(dauphin.String)
    description = dauphin.String()


class DauphinEnumType(dauphin.ObjectType):
    class Meta:
        name = 'EnumType'
        interfaces = [DauphinType]

    values = dauphin.non_null_list('EnumValue')

    def __init__(self, enum_type):
        super(DauphinEnumType, self).__init__(**ctor_kwargs(enum_type))
        self._enum_type = enum_type

    def resolve_values(self, info):
        return [
            info.schema.type_named('EnumValue')(value=ev.config_value, description=ev.description)
            for ev in self._enum_type.enum_values
        ]

    def resolve_inner_types(self, info):
        return inner_types(info, self._enum_type)

    def resolve_type_attributes(self, _info):
        return type_attributes(self._enum_type)


class DauphinTypeField(dauphin.ObjectType):
    class Meta:
        name = 'TypeField'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    type = dauphin.NonNull('Type')
    default_value = dauphin.String()
    is_optional = dauphin.NonNull(dauphin.Boolean)

    def __init__(self, name, field):
        super(DauphinTypeField, self).__init__(
            name=name,
            description=field.description,
            default_value=field.default_value_as_str if field.default_provided else None,
            is_optional=field.is_optional,
        )
        self._field = field

    def resolve_type(self, info):
        return info.schema.type_named('Type').to_dauphin_type(info, self._field.config_type)
