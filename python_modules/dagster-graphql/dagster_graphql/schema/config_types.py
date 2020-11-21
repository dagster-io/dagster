from dagster import check
from dagster.config.config_type import ConfigTypeKind
from dagster.config.snap import get_recursive_type_keys
from dagster.core.snap import ConfigFieldSnap, ConfigSchemaSnapshot, ConfigTypeSnap
from dagster_graphql import dauphin


def to_dauphin_config_type(config_schema_snapshot, config_type_key):
    check.inst_param(config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot)
    check.str_param(config_type_key, "config_type_key")

    config_type_snap = config_schema_snapshot.get_config_snap(config_type_key)
    kind = config_type_snap.kind

    if kind == ConfigTypeKind.ENUM:
        return DauphinEnumConfigType(config_schema_snapshot, config_type_snap)
    elif ConfigTypeKind.has_fields(kind):
        return DauphinCompositeConfigType(config_schema_snapshot, config_type_snap)
    elif kind == ConfigTypeKind.ARRAY:
        return DauphinArrayConfigType(config_schema_snapshot, config_type_snap)
    elif kind == ConfigTypeKind.NONEABLE:
        return DauphinNullableConfigType(config_schema_snapshot, config_type_snap)
    elif kind == ConfigTypeKind.ANY or kind == ConfigTypeKind.SCALAR:
        return DauphinRegularConfigType(config_schema_snapshot, config_type_snap)
    elif kind == ConfigTypeKind.SCALAR_UNION:
        return DauphinScalarUnionConfigType(config_schema_snapshot, config_type_snap)
    else:
        check.failed("Should never reach")


def _ctor_kwargs_for_snap(config_type_snap):
    return dict(
        key=config_type_snap.key,
        description=config_type_snap.description,
        is_selector=config_type_snap.kind == ConfigTypeKind.SELECTOR,
        type_param_keys=config_type_snap.type_param_keys or [],
    )


class DauphinConfigType(dauphin.Interface):
    class Meta:
        name = "ConfigType"

    key = dauphin.NonNull(dauphin.String)
    description = dauphin.String()

    recursive_config_types = dauphin.Field(
        dauphin.non_null_list("ConfigType"),
        description="""
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
    """,
    )
    type_param_keys = dauphin.Field(
        dauphin.non_null_list(dauphin.String),
        description="""
This returns the keys for type parameters of any closed generic type,
(e.g. List, Optional). This should be used for reconstructing and
navigating the full schema client-side and not innerTypes.
    """,
    )
    is_selector = dauphin.NonNull(dauphin.Boolean)


class ConfigTypeMixin:
    def __init__(self, config_schema_snapshot, config_type_snap):
        self._config_type_snap = check.inst_param(
            config_type_snap, "config_type_snap", ConfigTypeSnap
        )
        self._config_schema_snapshot = check.inst_param(
            config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot
        )
        super(ConfigTypeMixin, self).__init__(**_ctor_kwargs_for_snap(config_type_snap))

    def resolve_recursive_config_types(self, _graphene_info):
        return list(
            map(
                lambda key: to_dauphin_config_type(self._config_schema_snapshot, key),
                get_recursive_type_keys(self._config_type_snap, self._config_schema_snapshot),
            )
        )


class DauphinRegularConfigType(ConfigTypeMixin, dauphin.ObjectType):
    class Meta:
        name = "RegularConfigType"
        interfaces = [DauphinConfigType]
        description = "Regular is an odd name in this context. It really means Scalar or Any."

    given_name = dauphin.NonNull(dauphin.String)

    def resolve_given_name(self, _):
        return self._config_type_snap.given_name


class DauphinWrappingConfigType(dauphin.Interface):
    class Meta:
        name = "WrappingConfigType"

    of_type = dauphin.Field(dauphin.NonNull(DauphinConfigType))


class DauphinArrayConfigType(ConfigTypeMixin, dauphin.ObjectType):
    class Meta:
        name = "ArrayConfigType"
        interfaces = [DauphinConfigType, DauphinWrappingConfigType]

    def resolve_of_type(self, _graphene_info):
        return to_dauphin_config_type(
            self._config_schema_snapshot, self._config_type_snap.inner_type_key,
        )


class DauphinScalarUnionConfigType(ConfigTypeMixin, dauphin.ObjectType):
    class Meta:
        name = "ScalarUnionConfigType"
        interfaces = [DauphinConfigType]

    scalar_type = dauphin.NonNull(DauphinConfigType)
    non_scalar_type = dauphin.NonNull(DauphinConfigType)

    scalar_type_key = dauphin.NonNull(dauphin.String)
    non_scalar_type_key = dauphin.NonNull(dauphin.String)

    def get_scalar_type_key(self):
        return self._config_type_snap.scalar_type_key

    def get_non_scalar_type_key(self):
        return self._config_type_snap.non_scalar_type_key

    def resolve_scalar_type_key(self, _):
        return self.get_scalar_type_key()

    def resolve_non_scalar_type_key(self, _):
        return self.get_non_scalar_type_key()

    def resolve_scalar_type(self, _):
        return to_dauphin_config_type(self._config_schema_snapshot, self.get_scalar_type_key())

    def resolve_non_scalar_type(self, _):
        return to_dauphin_config_type(self._config_schema_snapshot, self.get_non_scalar_type_key())


class DauphinNullableConfigType(ConfigTypeMixin, dauphin.ObjectType):
    class Meta:
        name = "NullableConfigType"
        interfaces = [DauphinConfigType, DauphinWrappingConfigType]

    def resolve_of_type(self, _graphene_info):
        return to_dauphin_config_type(
            self._config_schema_snapshot, self._config_type_snap.inner_type_key
        )


class DauphinEnumConfigType(ConfigTypeMixin, dauphin.ObjectType):
    class Meta:
        name = "EnumConfigType"
        interfaces = [DauphinConfigType]

    values = dauphin.non_null_list("EnumConfigValue")
    given_name = dauphin.NonNull(dauphin.String)

    def resolve_values(self, _graphene_info):
        return [
            DauphinEnumConfigValue(value=ev.value, description=ev.description)
            for ev in self._config_type_snap.enum_values
        ]

    def resolve_given_name(self, _):
        return self._config_type_snap.given_name


class DauphinEnumConfigValue(dauphin.ObjectType):
    class Meta:
        name = "EnumConfigValue"

    value = dauphin.NonNull(dauphin.String)
    description = dauphin.String()


class DauphinCompositeConfigType(ConfigTypeMixin, dauphin.ObjectType):
    class Meta:
        name = "CompositeConfigType"
        interfaces = [DauphinConfigType]

    fields = dauphin.non_null_list("ConfigTypeField")

    def resolve_fields(self, _graphene_info):
        return sorted(
            [
                DauphinConfigTypeField(
                    config_schema_snapshot=self._config_schema_snapshot, field_snap=field_snap,
                )
                for field_snap in self._config_type_snap.fields
            ],
            key=lambda field: field.name,
        )


class DauphinConfigTypeField(dauphin.ObjectType):
    class Meta:
        name = "ConfigTypeField"

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    config_type = dauphin.NonNull("ConfigType")
    config_type_key = dauphin.NonNull(dauphin.String)
    is_required = dauphin.NonNull(dauphin.Boolean)

    def resolve_config_type_key(self, _):
        return self._field_snap.type_key

    def __init__(self, config_schema_snapshot, field_snap):
        self._config_schema_snapshot = check.inst_param(
            config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot
        )
        self._field_snap = check.inst_param(field_snap, "field_snap", ConfigFieldSnap)
        super(DauphinConfigTypeField, self).__init__(
            name=field_snap.name,
            description=field_snap.description,
            is_required=field_snap.is_required,
        )

    def resolve_config_type(self, _graphene_info):
        return to_dauphin_config_type(self._config_schema_snapshot, self._field_snap.type_key)
