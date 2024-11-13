from typing import Callable

import dagster._check as check
import graphene
from dagster._config.snap import ConfigTypeSnap
from dagster._core.snap import ResourceDefSnap

from dagster_graphql.schema.config_types import GrapheneConfigTypeField
from dagster_graphql.schema.errors import (
    GrapheneInvalidSubsetError,
    GraphenePipelineNotFoundError,
    GraphenePythonError,
)
from dagster_graphql.schema.util import ResolveInfo, non_null_list


class GrapheneResource(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    configField = graphene.Field(GrapheneConfigTypeField)

    class Meta:
        name = "Resource"

    def __init__(
        self,
        get_config_type: Callable[[str], ConfigTypeSnap],
        resource_def_snap: ResourceDefSnap,
    ):
        super().__init__()
        self._get_config_type = get_config_type
        self._resource_def_snap = check.inst_param(
            resource_def_snap, "resource_def_snap", ResourceDefSnap
        )
        self.name = resource_def_snap.name
        self.description = resource_def_snap.description

    def resolve_configField(self, _graphene_info: ResolveInfo):
        if self._resource_def_snap.config_field_snap:
            try:
                # config type may not be present if mode config mapped, null out gracefully
                self._get_config_type(self._resource_def_snap.config_field_snap.type_key)
            except KeyError:
                return None

            return GrapheneConfigTypeField(
                get_config_type=self._get_config_type,
                field_snap=self._resource_def_snap.config_field_snap,
            )

        return None


class GrapheneResourceConnection(graphene.ObjectType):
    class Meta:
        name = "ResourceConnection"

    resources = non_null_list(GrapheneResource)


class GrapheneResourcesOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneResourceConnection,
            GraphenePipelineNotFoundError,
            GrapheneInvalidSubsetError,
            GraphenePythonError,
        )
        name = "ResourcesOrError"
