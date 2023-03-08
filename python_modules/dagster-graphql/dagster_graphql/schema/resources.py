from typing import List

import dagster._check as check
import graphene
from dagster._core.definitions.selector import ResourceSelector
from dagster._core.host_representation.external import ExternalResource
from dagster._core.host_representation.external_data import (
    ExternalResourceConfigEnvVar,
    ExternalResourceValue,
)

from dagster_graphql.schema.errors import (
    GraphenePythonError,
    GrapheneRepositoryNotFoundError,
    GrapheneResourceNotFoundError,
)
from dagster_graphql.schema.util import non_null_list

from .config_types import GrapheneConfigTypeField


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

    def __init__(self, key: str, external_resource_value: ExternalResourceValue):
        super().__init__()

        self.key = key
        if isinstance(external_resource_value, ExternalResourceConfigEnvVar):
            self.type = GrapheneConfiguredValueType.ENV_VAR
            self.value = external_resource_value.name
        else:
            self.type = GrapheneConfiguredValueType.VALUE
            self.value = external_resource_value


class GrapheneNestedResourceEntry(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    resource = graphene.NonNull(lambda: GrapheneResourceDetails)

    class Meta:
        name = "NestedResourceEntry"


class GrapheneResourceDetails(graphene.ObjectType):
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
    resourceType = graphene.NonNull(graphene.String)

    class Meta:
        name = "ResourceDetails"

    def __init__(
        self, location_name: str, repository_name: str, external_resource: ExternalResource
    ):
        super().__init__()

        self._location_name = check.str_param(location_name, "location_name")
        self._repository_name = check.str_param(repository_name, "repository_name")

        self._external_resource = check.inst_param(
            external_resource, "external_resource", ExternalResource
        )
        self.name = external_resource.name
        self.description = external_resource.description
        self._config_field_snaps = external_resource.config_field_snaps
        self._configured_values = external_resource.configured_values

        self._config_schema_snap = external_resource.config_schema_snap
        self.isTopLevel = external_resource.is_top_level
        self._nested_resources = external_resource.nested_resources
        self.resourceType = external_resource.resource_type

    def resolve_configFields(self, _graphene_info):
        return [
            GrapheneConfigTypeField(
                config_schema_snapshot=self._config_schema_snap,
                field_snap=field_snap,
            )
            for field_snap in self._config_field_snaps
        ]

    def resolve_configuredValues(self, _graphene_info):
        return [
            GrapheneConfiguredValue(key=key, external_resource_value=value)
            for key, value in self._configured_values.items()
        ]

    def resolve_nestedResources(self, graphene_info) -> List[GrapheneNestedResourceEntry]:
        from dagster_graphql.implementation.fetch_resources import get_resource_or_error

        return [
            GrapheneNestedResourceEntry(
                name=k,
                resource=get_resource_or_error(
                    graphene_info,
                    ResourceSelector(
                        location_name=self._location_name,
                        repository_name=self._repository_name,
                        resource_name=v,
                    ),
                ),
            )
            for k, v in self._nested_resources.items()
        ]


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
        name = "ResourcesOrError"
