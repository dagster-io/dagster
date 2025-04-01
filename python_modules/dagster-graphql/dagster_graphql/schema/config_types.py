from typing import AbstractSet, Callable, Optional, Union  # noqa: UP035

import dagster._check as check
import graphene
from dagster._config import ConfigTypeKind
from dagster._core.snap import ConfigFieldSnap, ConfigTypeSnap

from dagster_graphql.schema.util import ResolveInfo, non_null_list

GrapheneConfigTypeUnion = Union[
    "GrapheneEnumConfigType",
    "GrapheneCompositeConfigType",
    "GrapheneArrayConfigType",
    "GrapheneMapConfigType",
    "GrapheneNullableConfigType",
    "GrapheneRegularConfigType",
    "GrapheneScalarUnionConfigType",
]


def to_config_type(
    get_config_type: Callable[[str], ConfigTypeSnap],
    config_type_key: str,
) -> GrapheneConfigTypeUnion:
    config_type_snap = get_config_type(config_type_key)
    kind = config_type_snap.kind

    if kind == ConfigTypeKind.ENUM:
        return GrapheneEnumConfigType(get_config_type, config_type_snap)
    elif ConfigTypeKind.has_fields(kind):
        return GrapheneCompositeConfigType(get_config_type, config_type_snap)
    elif kind == ConfigTypeKind.ARRAY:
        return GrapheneArrayConfigType(get_config_type, config_type_snap)
    elif kind == ConfigTypeKind.MAP:
        return GrapheneMapConfigType(get_config_type, config_type_snap)
    elif kind == ConfigTypeKind.NONEABLE:
        return GrapheneNullableConfigType(get_config_type, config_type_snap)
    elif kind == ConfigTypeKind.ANY or kind == ConfigTypeKind.SCALAR:
        return GrapheneRegularConfigType(get_config_type, config_type_snap)
    elif kind == ConfigTypeKind.SCALAR_UNION:
        return GrapheneScalarUnionConfigType(get_config_type, config_type_snap)
    else:
        check.failed("Should never reach")


def _ctor_kwargs_for_snap(config_type_snap):
    return dict(
        key=config_type_snap.key,
        description=config_type_snap.description,
        is_selector=config_type_snap.kind == ConfigTypeKind.SELECTOR,
        type_param_keys=config_type_snap.type_param_keys or [],
    )


class GrapheneConfigType(graphene.Interface):
    key = graphene.NonNull(graphene.String)
    description = graphene.String()

    recursive_config_types = graphene.Field(
        non_null_list(lambda: GrapheneConfigType),
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
    type_param_keys = graphene.Field(
        non_null_list(graphene.String),
        description="""
This returns the keys for type parameters of any closed generic type,
(e.g. List, Optional). This should be used for reconstructing and
navigating the full schema client-side and not innerTypes.
    """,
    )
    is_selector = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "ConfigType"


def _recursive_config_type_keys(
    get_config_type: Callable[[str], ConfigTypeSnap],
    config_type_snap: ConfigTypeSnap,
) -> AbstractSet[str]:
    keys = set()
    for type_key in config_type_snap.get_child_type_keys():
        keys.add(type_key)
        child_config_type = get_config_type(type_key)
        child_keys = _recursive_config_type_keys(get_config_type, child_config_type)
        keys.update(child_keys)
    return keys


class GrapheneRegularConfigType(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneConfigType,)
        description = "Regular is an odd name in this context. It really means Scalar or Any."
        name = "RegularConfigType"

    given_name = graphene.NonNull(graphene.String)

    def __init__(
        self,
        get_config_type: Callable[[str], ConfigTypeSnap],
        config_type_snap: ConfigTypeSnap,
    ):
        self._config_type_snap = check.inst_param(
            config_type_snap, "config_type_snap", ConfigTypeSnap
        )
        self._get_config_type = get_config_type
        super().__init__(**_ctor_kwargs_for_snap(config_type_snap))

    def resolve_recursive_config_types(
        self, graphene_info: ResolveInfo
    ) -> list[GrapheneConfigTypeUnion]:
        return [
            to_config_type(self._get_config_type, config_type_key)
            for config_type_key in _recursive_config_type_keys(
                self._get_config_type, self._config_type_snap
            )
        ]

    def resolve_given_name(self, _):
        return self._config_type_snap.given_name


class GrapheneMapConfigType(graphene.ObjectType):
    key_type = graphene.Field(graphene.NonNull(GrapheneConfigType))
    value_type = graphene.Field(graphene.NonNull(GrapheneConfigType))
    key_label_name = graphene.Field(graphene.String)

    class Meta:
        interfaces = (GrapheneConfigType,)
        name = "MapConfigType"

    def __init__(
        self,
        get_config_type: Callable[[str], ConfigTypeSnap],
        config_type_snap: ConfigTypeSnap,
    ):
        self._config_type_snap = check.inst_param(
            config_type_snap, "config_type_snap", ConfigTypeSnap
        )
        self._get_config_type = get_config_type
        super().__init__(**_ctor_kwargs_for_snap(config_type_snap))

    def resolve_recursive_config_types(
        self, graphene_info: ResolveInfo
    ) -> list[GrapheneConfigTypeUnion]:
        return [
            to_config_type(self._get_config_type, config_type_key)
            for config_type_key in _recursive_config_type_keys(
                self._get_config_type, self._config_type_snap
            )
        ]

    def resolve_key_type(self, graphene_info: ResolveInfo) -> GrapheneConfigTypeUnion:
        return to_config_type(
            self._get_config_type,
            self._config_type_snap.key_type_key,
        )

    def resolve_value_type(self, graphene_info: ResolveInfo) -> GrapheneConfigTypeUnion:
        return to_config_type(
            self._get_config_type,
            self._config_type_snap.inner_type_key,
        )

    def resolve_key_label_name(self, _graphene_info: ResolveInfo) -> Optional[str]:
        return self._config_type_snap.given_name


class GrapheneWrappingConfigType(graphene.Interface):
    of_type = graphene.Field(graphene.NonNull(GrapheneConfigType))

    class Meta:
        name = "WrappingConfigType"


class GrapheneArrayConfigType(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneConfigType, GrapheneWrappingConfigType)
        name = "ArrayConfigType"

    def __init__(
        self,
        get_config_type: Callable[[str], ConfigTypeSnap],
        config_type_snap: ConfigTypeSnap,
    ):
        self._config_type_snap = check.inst_param(
            config_type_snap, "config_type_snap", ConfigTypeSnap
        )
        self._get_config_type = get_config_type
        super().__init__(**_ctor_kwargs_for_snap(config_type_snap))

    def resolve_recursive_config_types(
        self, graphene_info: ResolveInfo
    ) -> list[GrapheneConfigTypeUnion]:
        return [
            to_config_type(self._get_config_type, config_type_key)
            for config_type_key in _recursive_config_type_keys(
                self._get_config_type, self._config_type_snap
            )
        ]

    def resolve_of_type(self, graphene_info: ResolveInfo) -> GrapheneConfigTypeUnion:
        return to_config_type(
            self._get_config_type,
            self._config_type_snap.inner_type_key,
        )


class GrapheneScalarUnionConfigType(graphene.ObjectType):
    scalar_type = graphene.NonNull(GrapheneConfigType)
    non_scalar_type = graphene.NonNull(GrapheneConfigType)
    scalar_type_key = graphene.NonNull(graphene.String)
    non_scalar_type_key = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneConfigType,)
        name = "ScalarUnionConfigType"

    def __init__(
        self,
        get_config_type: Callable[[str], ConfigTypeSnap],
        config_type_snap: ConfigTypeSnap,
    ):
        self._config_type_snap = check.inst_param(
            config_type_snap, "config_type_snap", ConfigTypeSnap
        )
        self._get_config_type = get_config_type
        super().__init__(**_ctor_kwargs_for_snap(config_type_snap))

    def resolve_recursive_config_types(
        self, graphene_info: ResolveInfo
    ) -> list[GrapheneConfigTypeUnion]:
        return [
            to_config_type(self._get_config_type, config_type_key)
            for config_type_key in _recursive_config_type_keys(
                self._get_config_type, self._config_type_snap
            )
        ]

    def get_scalar_type_key(self) -> str:
        return self._config_type_snap.scalar_type_key

    def get_non_scalar_type_key(self) -> str:
        return self._config_type_snap.non_scalar_type_key

    def resolve_scalar_type_key(self, _) -> str:
        return self.get_scalar_type_key()

    def resolve_non_scalar_type_key(self, _) -> str:
        return self.get_non_scalar_type_key()

    def resolve_scalar_type(self, graphene_info) -> GrapheneConfigTypeUnion:
        return to_config_type(self._get_config_type, self.get_scalar_type_key())

    def resolve_non_scalar_type(self, graphene_info) -> GrapheneConfigTypeUnion:
        return to_config_type(self._get_config_type, self.get_non_scalar_type_key())


class GrapheneNullableConfigType(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneConfigType, GrapheneWrappingConfigType)
        name = "NullableConfigType"

    def __init__(
        self,
        get_config_type: Callable[[str], ConfigTypeSnap],
        config_type_snap: ConfigTypeSnap,
    ):
        self._config_type_snap = check.inst_param(
            config_type_snap, "config_type_snap", ConfigTypeSnap
        )
        self._get_config_type = get_config_type
        super().__init__(**_ctor_kwargs_for_snap(config_type_snap))

    def resolve_recursive_config_types(
        self, graphene_info: ResolveInfo
    ) -> list[GrapheneConfigTypeUnion]:
        return [
            to_config_type(self._get_config_type, config_type_key)
            for config_type_key in _recursive_config_type_keys(
                self._get_config_type, self._config_type_snap
            )
        ]

    def resolve_of_type(self, graphene_info: ResolveInfo) -> GrapheneConfigTypeUnion:
        return to_config_type(
            self._get_config_type,
            self._config_type_snap.inner_type_key,
        )


class GrapheneEnumConfigValue(graphene.ObjectType):
    value = graphene.NonNull(graphene.String)
    description = graphene.String()

    class Meta:
        name = "EnumConfigValue"


class GrapheneEnumConfigType(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneConfigType,)
        name = "EnumConfigType"

    values = non_null_list(GrapheneEnumConfigValue)
    given_name = graphene.NonNull(graphene.String)

    def __init__(
        self,
        get_config_type: Callable[[str], ConfigTypeSnap],
        config_type_snap: ConfigTypeSnap,
    ):
        self._config_type_snap = check.inst_param(
            config_type_snap, "config_type_snap", ConfigTypeSnap
        )
        self._get_config_type = get_config_type
        super().__init__(**_ctor_kwargs_for_snap(config_type_snap))

    def resolve_recursive_config_types(
        self, graphene_info: ResolveInfo
    ) -> list[GrapheneConfigTypeUnion]:
        return [
            to_config_type(self._get_config_type, config_type_key)
            for config_type_key in _recursive_config_type_keys(
                self._get_config_type, self._config_type_snap
            )
        ]

    def resolve_values(self, _graphene_info: ResolveInfo) -> list[GrapheneEnumConfigValue]:
        return [
            GrapheneEnumConfigValue(value=ev.value, description=ev.description)
            for ev in check.not_none(self._config_type_snap.enum_values)
        ]

    def resolve_given_name(self, _):
        return self._config_type_snap.given_name


class GrapheneConfigTypeField(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    config_type = graphene.NonNull(GrapheneConfigType)
    config_type_key = graphene.NonNull(graphene.String)
    is_required = graphene.NonNull(graphene.Boolean)
    default_value_as_json = graphene.String()

    class Meta:
        name = "ConfigTypeField"

    def resolve_config_type_key(self, _) -> str:
        return self._field_snap.type_key

    def __init__(
        self,
        get_config_type: Callable[[str], ConfigTypeSnap],
        field_snap: ConfigFieldSnap,
    ):
        self._get_config_type = get_config_type
        self._field_snap: ConfigFieldSnap = check.inst_param(
            field_snap, "field_snap", ConfigFieldSnap
        )
        super().__init__(
            name=field_snap.name,
            description=field_snap.description,
            is_required=field_snap.is_required,
        )

    def resolve_config_type(self, graphene_info: ResolveInfo) -> GrapheneConfigTypeUnion:
        return to_config_type(self._get_config_type, self._field_snap.type_key)

    def resolve_default_value_as_json(self, _graphene_info: ResolveInfo) -> Optional[str]:
        return self._field_snap.default_value_as_json_str


class GrapheneCompositeConfigType(graphene.ObjectType):
    fields = non_null_list(GrapheneConfigTypeField)

    class Meta:
        interfaces = (GrapheneConfigType,)
        name = "CompositeConfigType"

    def __init__(
        self,
        get_config_type: Callable[[str], ConfigTypeSnap],
        config_type_snap: ConfigTypeSnap,
    ):
        self._config_type_snap = check.inst_param(
            config_type_snap, "config_type_snap", ConfigTypeSnap
        )
        self._get_config_type = get_config_type
        super().__init__(**_ctor_kwargs_for_snap(config_type_snap))

    def resolve_recursive_config_types(
        self, graphene_info: ResolveInfo
    ) -> list[GrapheneConfigTypeUnion]:
        return [
            to_config_type(self._get_config_type, config_type_key)
            for config_type_key in _recursive_config_type_keys(
                self._get_config_type, self._config_type_snap
            )
        ]

    def resolve_fields(self, graphene_info: ResolveInfo) -> list[GrapheneConfigTypeField]:
        return sorted(
            [
                GrapheneConfigTypeField(
                    get_config_type=self._get_config_type,
                    field_snap=field_snap,
                )
                for field_snap in (self._config_type_snap.fields or [])
            ],
            key=lambda field: field.name,
        )


types = [
    GrapheneArrayConfigType,
    GrapheneCompositeConfigType,
    GrapheneConfigType,
    GrapheneConfigTypeField,
    GrapheneEnumConfigType,
    GrapheneEnumConfigValue,
    GrapheneNullableConfigType,
    GrapheneRegularConfigType,
    GrapheneScalarUnionConfigType,
    GrapheneWrappingConfigType,
    GrapheneMapConfigType,
]
