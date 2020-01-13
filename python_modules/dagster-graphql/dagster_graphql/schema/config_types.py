from dagster_graphql import dauphin

from dagster import check
from dagster.config.config_type import ConfigType, ConfigTypeKind
from dagster.config.field import Field


def to_dauphin_config_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)

    kind = config_type.kind

    if kind == ConfigTypeKind.ENUM:
        return DauphinEnumConfigType(config_type)
    elif ConfigTypeKind.has_fields(kind):
        return DauphinCompositeConfigType(config_type)
    elif kind == ConfigTypeKind.ARRAY:
        return DauphinArrayConfigType(config_type)
    elif kind == ConfigTypeKind.NONEABLE:
        return DauphinNullableConfigType(config_type)
    elif kind == ConfigTypeKind.ANY or kind == ConfigTypeKind.SCALAR:
        return DauphinRegularConfigType(config_type)
    elif kind == ConfigTypeKind.SCALAR_UNION:
        return DauphinScalarUnionConfigType(config_type)
    else:
        check.failed('Should never reach')


def _ctor_kwargs(config_type):
    return dict(
        key=config_type.key,
        description=config_type.description,
        is_selector=config_type.kind == ConfigTypeKind.SELECTOR,
        type_param_keys=[tp.key for tp in config_type.type_params]
        if config_type.type_params
        else [],
    )


class DauphinConfigType(dauphin.Interface):
    class Meta(object):
        name = 'ConfigType'

    key = dauphin.NonNull(dauphin.String)
    description = dauphin.String()

    recursive_config_types = dauphin.Field(
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
    ''',
    )
    type_param_keys = dauphin.Field(
        dauphin.non_null_list(dauphin.String),
        description='''
This returns the keys for type parameters of any closed generic type,
(e.g. List, Optional). This should be used for reconstructing and
navigating the full schema client-side and not innerTypes.
    ''',
    )
    is_selector = dauphin.NonNull(dauphin.Boolean)


def _resolve_recursive_config_types(config_type):
    return list(map(to_dauphin_config_type, config_type.recursive_config_types))


class DauphinRegularConfigType(dauphin.ObjectType):
    def __init__(self, config_type):
        self._config_type = check.inst_param(config_type, 'config_type', ConfigType)
        super(DauphinRegularConfigType, self).__init__(**_ctor_kwargs(config_type))

    class Meta(object):
        name = 'RegularConfigType'
        interfaces = [DauphinConfigType]
        description = 'Regular is an odd name in this context. It really means Scalar or Any.'

    given_name = dauphin.NonNull(dauphin.String)

    def resolve_given_name(self, _):
        return self._config_type.given_name

    def resolve_recursive_config_types(self, _graphene_info):
        return _resolve_recursive_config_types(self._config_type)


class DauphinWrappingConfigType(dauphin.Interface):
    class Meta(object):
        name = 'WrappingConfigType'

    of_type = dauphin.Field(dauphin.NonNull(DauphinConfigType))


class DauphinArrayConfigType(dauphin.ObjectType):
    def __init__(self, config_type):
        self._config_type = check.inst_param(config_type, 'config_type', ConfigType)
        super(DauphinArrayConfigType, self).__init__(**_ctor_kwargs(config_type))

    class Meta(object):
        name = 'ArrayConfigType'
        interfaces = [DauphinConfigType, DauphinWrappingConfigType]

    def resolve_of_type(self, _graphene_info):
        return to_dauphin_config_type(self._config_type.inner_type)

    def resolve_recursive_config_types(self, _graphene_info):
        return _resolve_recursive_config_types(self._config_type)


class DauphinScalarUnionConfigType(dauphin.ObjectType):
    def __init__(self, config_type):
        self._config_type = check.inst_param(config_type, 'config_type', ConfigType)
        check.param_invariant(config_type.kind == ConfigTypeKind.SCALAR_UNION, 'config_type')

        super(DauphinScalarUnionConfigType, self).__init__(**_ctor_kwargs(config_type))

    class Meta(object):
        name = 'ScalarUnionConfigType'
        interfaces = [DauphinConfigType]

    scalar_type = dauphin.NonNull(DauphinConfigType)
    non_scalar_type = dauphin.NonNull(DauphinConfigType)

    scalar_type_key = dauphin.NonNull(dauphin.String)
    non_scalar_type_key = dauphin.NonNull(dauphin.String)

    def resolve_scalar_type_key(self, _):
        return self._config_type.scalar_type.key

    def resolve_non_scalar_type_key(self, _):
        return self._config_type.non_scalar_type.key

    def resolve_scalar_type(self, _):
        return to_dauphin_config_type(self._config_type.scalar_type)

    def resolve_non_scalar_type(self, _):
        return to_dauphin_config_type(self._config_type.non_scalar_type)

    def resolve_recursive_config_types(self, _graphene_info):
        return _resolve_recursive_config_types(self._config_type)


class DauphinNullableConfigType(dauphin.ObjectType):
    def __init__(self, config_type):
        self._config_type = check.inst_param(config_type, 'config_type', ConfigType)
        super(DauphinNullableConfigType, self).__init__(**_ctor_kwargs(config_type))

    class Meta(object):
        name = 'NullableConfigType'
        interfaces = [DauphinConfigType, DauphinWrappingConfigType]

    def resolve_of_type(self, _graphene_info):
        return to_dauphin_config_type(self._config_type.inner_type)

    def resolve_recursive_config_types(self, _graphene_info):
        return _resolve_recursive_config_types(self._config_type)


class DauphinEnumConfigType(dauphin.ObjectType):
    def __init__(self, config_type):
        check.inst_param(config_type, 'config_type', ConfigType)
        check.param_invariant(config_type.kind == ConfigTypeKind.ENUM, 'config_type')
        self._config_type = config_type
        super(DauphinEnumConfigType, self).__init__(**_ctor_kwargs(config_type))

    class Meta(object):
        name = 'EnumConfigType'
        interfaces = [DauphinConfigType]

    values = dauphin.non_null_list('EnumConfigValue')
    given_name = dauphin.NonNull(dauphin.String)

    def resolve_values(self, _graphene_info):
        return [
            DauphinEnumConfigValue(value=ev.config_value, description=ev.description)
            for ev in self._config_type.enum_values
        ]

    def resolve_given_name(self, _):
        return self._config_type.given_name

    def resolve_recursive_config_types(self, _graphene_info):
        return _resolve_recursive_config_types(self._config_type)


class DauphinEnumConfigValue(dauphin.ObjectType):
    class Meta(object):
        name = 'EnumConfigValue'

    value = dauphin.NonNull(dauphin.String)
    description = dauphin.String()


class DauphinCompositeConfigType(dauphin.ObjectType):
    def __init__(self, config_type):
        check.inst_param(config_type, 'config_type', ConfigType)
        check.param_invariant(ConfigTypeKind.has_fields(config_type.kind), 'config_type')
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

    def resolve_recursive_config_types(self, _graphene_info):
        return _resolve_recursive_config_types(self._config_type)


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
