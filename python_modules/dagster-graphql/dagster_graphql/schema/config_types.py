from dagster_graphql import dauphin

from dagster import check
from dagster.core.types.config import ConfigType
from dagster.core.types.field import Field


def to_dauphin_config_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)

    if config_type.is_enum:
        return DauphinEnumConfigType(config_type)
    elif config_type.has_fields:
        return DauphinCompositeConfigType(config_type)
    elif config_type.is_list:
        return DauphinListConfigType(config_type)
    elif config_type.is_nullable:
        return DauphinNullableConfigType(config_type)
    else:
        return DauphinRegularConfigType(config_type)


def _ctor_kwargs(config_type):
    return dict(
        key=config_type.key,
        name=config_type.name,
        description=config_type.description,
        is_builtin=config_type.type_attributes.is_builtin,
        is_list=config_type.is_list,
        is_nullable=config_type.is_nullable,
        is_selector=config_type.is_selector,
        is_system_generated=config_type.type_attributes.is_system_config,
        type_param_keys=[tp.key for tp in config_type.type_params]
        if config_type.type_params
        else [],
    )


class DauphinConfigType(dauphin.Interface):
    class Meta(object):
        name = 'ConfigType'

    key = dauphin.NonNull(dauphin.String)
    name = dauphin.String()
    description = dauphin.String()

    inner_types = dauphin.Field(
        dauphin.non_null_list('ConfigType'),
        description='''
This is an odd and problematic field. It recursively goes down to
get all the types contained within a type. The case where it is horrible
are dictionaries and it recurses all the way down to the leaves. This means
that in a case where one is fetching all the types and then all the inner
types keys for those types, we are returning O(N^2) type keys, which
can cause awful performance for large schemas. When you have access
to *all* the types, you should instead only use the type_param_keys
field for closed generic types and manually navigate down the to
field types client-side.

Where it is useful is when you are fetching types independently and
want to be able to render them, but without fetching the entire schema.

We use this capability when rendering the sidebar.

https://github.com/dagster-io/dagster/issues/1959
    ''',
    )
    type_param_keys = dauphin.Field(
        dauphin.non_null_list(dauphin.String),
        description='''
This returns the keys for type parameters of any closed generic type,
(e.g. List, Optional). This should be used for reconstructing and
navigating the full schema client-side and not innerTypes.

https://github.com/dagster-io/dagster/issues/1959
    ''',
    )
    is_nullable = dauphin.NonNull(dauphin.Boolean)
    is_list = dauphin.NonNull(dauphin.Boolean)
    is_selector = dauphin.NonNull(dauphin.Boolean)

    is_builtin = dauphin.NonNull(
        dauphin.Boolean,
        description='''
True if the system defines it and it is the same type across pipelines.
Examples include "Int" and "String."''',
    )

    is_system_generated = dauphin.NonNull(
        dauphin.Boolean,
        description='''
Dagster generates types for base elements of the config system (e.g. the solids and
context field of the base environment). These types are always present
and are typically not relevant to an end user. This flag allows tool authors to
filter out those types by default.
''',
    )


def _resolve_inner_types(config_type):
    return list(map(to_dauphin_config_type, config_type.inner_types))


class DauphinRegularConfigType(dauphin.ObjectType):
    def __init__(self, config_type):
        self._config_type = check.inst_param(config_type, 'config_type', ConfigType)
        super(DauphinRegularConfigType, self).__init__(**_ctor_kwargs(config_type))

    class Meta(object):
        name = 'RegularConfigType'
        interfaces = [DauphinConfigType]

    def resolve_inner_types(self, _graphene_info):
        return _resolve_inner_types(self._config_type)


class DauphinWrappingConfigType(dauphin.Interface):
    class Meta(object):
        name = 'WrappingConfigType'

    of_type = dauphin.Field(dauphin.NonNull(DauphinConfigType))


class DauphinListConfigType(dauphin.ObjectType):
    def __init__(self, config_type):
        self._config_type = check.inst_param(config_type, 'config_type', ConfigType)
        super(DauphinListConfigType, self).__init__(**_ctor_kwargs(config_type))

    class Meta(object):
        name = 'ListConfigType'
        interfaces = [DauphinConfigType, DauphinWrappingConfigType]

    def resolve_of_type(self, _graphene_info):
        return to_dauphin_config_type(self._config_type.inner_type)

    def resolve_inner_types(self, _graphene_info):
        return _resolve_inner_types(self._config_type)


class DauphinNullableConfigType(dauphin.ObjectType):
    def __init__(self, config_type):
        self._config_type = check.inst_param(config_type, 'config_type', ConfigType)
        super(DauphinNullableConfigType, self).__init__(**_ctor_kwargs(config_type))

    class Meta(object):
        name = 'NullableConfigType'
        interfaces = [DauphinConfigType, DauphinWrappingConfigType]

    def resolve_of_type(self, _graphene_info):
        return to_dauphin_config_type(self._config_type.inner_type)

    def resolve_inner_types(self, _graphene_info):
        return _resolve_inner_types(self._config_type)


class DauphinEnumConfigType(dauphin.ObjectType):
    def __init__(self, config_type):
        check.inst_param(config_type, 'config_type', ConfigType)
        check.param_invariant(config_type.is_enum, 'config_type')
        self._config_type = config_type
        super(DauphinEnumConfigType, self).__init__(**_ctor_kwargs(config_type))

    class Meta(object):
        name = 'EnumConfigType'
        interfaces = [DauphinConfigType]

    values = dauphin.non_null_list('EnumConfigValue')

    def resolve_values(self, _graphene_info):
        return [
            DauphinEnumConfigValue(value=ev.config_value, description=ev.description)
            for ev in self._config_type.enum_values
        ]

    def resolve_inner_types(self, _graphene_info):
        return _resolve_inner_types(self._config_type)


class DauphinEnumConfigValue(dauphin.ObjectType):
    class Meta(object):
        name = 'EnumConfigValue'

    value = dauphin.NonNull(dauphin.String)
    description = dauphin.String()


class DauphinCompositeConfigType(dauphin.ObjectType):
    def __init__(self, config_type):
        check.inst_param(config_type, 'config_type', ConfigType)
        check.param_invariant(config_type.has_fields, 'config_type')
        self._config_type = config_type
        super(DauphinCompositeConfigType, self).__init__(**_ctor_kwargs(config_type))

    class Meta(object):
        name = 'CompositeConfigType'
        interfaces = [DauphinConfigType]

    fields = dauphin.non_null_list('ConfigTypeField')

    def resolve_fields(self, _graphene_info):
        return sorted(
            [
                DauphinConfigTypeField(name=name, field=field)
                for name, field in self._config_type.fields.items()
            ],
            key=lambda field: field.name,
        )

    def resolve_inner_types(self, _graphene_info):
        return _resolve_inner_types(self._config_type)


class DauphinConfigTypeField(dauphin.ObjectType):
    class Meta(object):
        name = 'ConfigTypeField'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    config_type = dauphin.NonNull('ConfigType')
    config_type_key = dauphin.NonNull(dauphin.String)
    default_value = dauphin.String()
    is_optional = dauphin.NonNull(dauphin.Boolean)

    def resolve_config_type_key(self, _):
        return self._field.config_type.key

    def __init__(self, name, field):
        check.str_param(name, 'name')
        check.inst_param(field, 'field', Field)

        super(DauphinConfigTypeField, self).__init__(
            name=name,
            description=field.description,
            default_value=field.default_value_as_str if field.default_provided else None,
            is_optional=field.is_optional,
        )
        self._field = field

    def resolve_config_type(self, _graphene_info):
        return to_dauphin_config_type(self._field.config_type)
