import dagster._check as check
import graphene
from dagster._core.definitions.selector import ResourceSelector
from dagster._core.remote_representation.external import RemoteResource
from dagster._core.remote_representation.external_data import (
    NestedResourceType,
    ResourceConfigEnvVarSnap,
    ResourceJobUsageEntry,
    ResourceValueSnap,
)

from dagster_graphql.schema.config_types import GrapheneConfigTypeField
from dagster_graphql.schema.entity_key import GrapheneAssetKey
from dagster_graphql.schema.errors import (
    GraphenePythonError,
    GrapheneRepositoryNotFoundError,
    GrapheneResourceNotFoundError,
)
from dagster_graphql.schema.util import ResolveInfo, non_null_list


class GrapheneConfiguredValueType(graphene.Enum):
    VALUE = "VALUE"
    ENV_VAR = "ENV_VAR"

    class Meta:
        name = "ConfiguredValueType"


class GrapheneConfiguredValue(graphene.ObjectType):
    key = graphene.NonNull(graphene.String)
    value = graphene.NonNull(graphene.String)
    type = graphene.NonNull(GrapheneConfiguredValueType)

    class Meta:
        name = "ConfiguredValue"

    def __init__(self, key: str, resource_value_snap: ResourceValueSnap):
        super().__init__()

        self.key = key
        if isinstance(resource_value_snap, ResourceConfigEnvVarSnap):
            self.type = GrapheneConfiguredValueType.ENV_VAR
            self.value = resource_value_snap.name
        else:
            self.type = GrapheneConfiguredValueType.VALUE
            self.value = resource_value_snap


GrapheneNestedResourceType = graphene.Enum.from_enum(NestedResourceType)


class GrapheneNestedResourceEntry(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    type = graphene.NonNull(GrapheneNestedResourceType)
    resource = graphene.Field(lambda: GrapheneResourceDetails)

    class Meta:
        name = "NestedResourceEntry"


class GrapheneJobAndSpecificOps(graphene.ObjectType):
    jobName = graphene.NonNull(graphene.String)
    opHandleIDs = graphene.Field(non_null_list(graphene.String))

    class Meta:
        name = "JobWithOps"

    def __init__(
        self,
        entry: ResourceJobUsageEntry,
        location_name: str,
        repository_name: str,
    ):
        self._entry = entry
        self._location_name = location_name
        self._repository_name = repository_name

        self._cached = None

    def resolve_jobName(self, _) -> str:
        return self._entry.job_name

    def resolve_opHandleIDs(self, _) -> list[str]:
        return [str(handle) for handle in self._entry.node_handles]


class GrapheneResourceDetails(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    configFields = graphene.Field(
        non_null_list(GrapheneConfigTypeField),
        description="Snapshots of all the fields for the given resource",
    )
    configuredValues = graphene.Field(
        non_null_list(GrapheneConfiguredValue),
        description=(
            "List of K/V pairs of user-configured values for each of the top-level fields on the"
            " resource"
        ),
    )
    isTopLevel = graphene.NonNull(graphene.Boolean)
    nestedResources = graphene.Field(
        non_null_list(GrapheneNestedResourceEntry),
        description="List of nested resources for the given resource",
    )
    parentResources = graphene.Field(
        non_null_list(GrapheneNestedResourceEntry),
        description="List of parent resources for the given resource",
    )
    resourceType = graphene.NonNull(graphene.String)
    assetKeysUsing = graphene.Field(non_null_list(GrapheneAssetKey))
    jobsOpsUsing = graphene.Field(non_null_list(GrapheneJobAndSpecificOps))
    schedulesUsing = graphene.Field(non_null_list(graphene.String))
    sensorsUsing = graphene.Field(non_null_list(graphene.String))

    class Meta:
        name = "ResourceDetails"

    def __init__(
        self,
        location_name: str,
        repository_name: str,
        remote_resource: RemoteResource,
    ):
        super().__init__()

        self.id = f"{location_name}-{repository_name}-{remote_resource.name}"

        self._location_name = check.str_param(location_name, "location_name")
        self._repository_name = check.str_param(repository_name, "repository_name")

        self._remote_resource = check.inst_param(remote_resource, "remote_resource", RemoteResource)
        self.name = remote_resource.name
        self.description = remote_resource.description
        self._config_field_snaps = remote_resource.config_field_snaps
        self._configured_values = remote_resource.configured_values

        self._config_schema_snap = remote_resource.config_schema_snap
        self.isTopLevel = remote_resource.is_top_level
        self._nested_resources = remote_resource.nested_resources
        self._parent_resources = remote_resource.parent_resources
        self.resourceType = remote_resource.resource_type
        self._asset_keys_using = remote_resource.asset_keys_using
        self._job_ops_using = remote_resource.job_ops_using
        self._schedules_using = remote_resource.schedules_using
        self._sensors_using = remote_resource.sensors_using

    def resolve_configFields(self, _graphene_info: ResolveInfo):
        return [
            GrapheneConfigTypeField(
                get_config_type=self._config_schema_snap.get_config_snap,
                field_snap=field_snap,
            )
            for field_snap in self._config_field_snaps
        ]

    def resolve_configuredValues(self, _graphene_info):
        return [
            GrapheneConfiguredValue(key=key, resource_value_snap=value)
            for key, value in self._configured_values.items()
        ]

    def resolve_nestedResources(self, graphene_info) -> list[GrapheneNestedResourceEntry]:
        from dagster_graphql.implementation.fetch_resources import get_resource_or_error

        return [
            GrapheneNestedResourceEntry(
                name=k,
                type=v.type,
                resource=(
                    get_resource_or_error(
                        graphene_info,
                        ResourceSelector(
                            location_name=self._location_name,
                            repository_name=self._repository_name,
                            resource_name=v.name,
                        ),
                    )
                    if v.type == NestedResourceType.TOP_LEVEL
                    else None
                ),
            )
            for k, v in self._nested_resources.items()
        ]

    def resolve_parentResources(self, graphene_info) -> list[GrapheneNestedResourceEntry]:
        from dagster_graphql.implementation.fetch_resources import get_resource_or_error

        return [
            GrapheneNestedResourceEntry(
                name=attribute,
                type=NestedResourceType.TOP_LEVEL,
                resource=get_resource_or_error(
                    graphene_info,
                    ResourceSelector(
                        location_name=self._location_name,
                        repository_name=self._repository_name,
                        resource_name=name,
                    ),
                ),
            )
            for name, attribute in self._parent_resources.items()
        ]

    def resolve_assetKeysUsing(self, _graphene_info) -> list[GrapheneAssetKey]:
        return [GrapheneAssetKey(path=asset_key.path) for asset_key in self._asset_keys_using]

    def resolve_jobsOpsUsing(self, graphene_info: ResolveInfo) -> list[GrapheneJobAndSpecificOps]:
        return [
            GrapheneJobAndSpecificOps(
                entry=entry,
                location_name=self._location_name,
                repository_name=self._repository_name,
            )
            for entry in self._job_ops_using
        ]

    def resolve_schedulesUsing(self, _graphene_info) -> list[str]:
        return self._schedules_using

    def resolve_sensorsUsing(self, _graphene_info) -> list[str]:
        return self._sensors_using


class GrapheneResourceDetailsOrError(graphene.Union):
    class Meta:
        types = (GrapheneResourceDetails, GrapheneResourceNotFoundError, GraphenePythonError)
        name = "ResourceDetailsOrError"


class GrapheneResourceDetailsList(graphene.ObjectType):
    results = non_null_list(GrapheneResourceDetails)

    class Meta:
        name = "ResourceDetailsList"


class GrapheneResourceDetailsListOrError(graphene.Union):
    class Meta:
        types = (GrapheneResourceDetailsList, GrapheneRepositoryNotFoundError, GraphenePythonError)
        name = "ResourceDetailsListOrError"
