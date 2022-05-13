# pylint: disable=missing-graphene-docstring
import graphene

import dagster._check as check
from dagster.core.host_representation import ExternalRepositoryOrigin

from .util import non_null_list


class GrapheneRepositoryMetadata(graphene.ObjectType):
    key = graphene.NonNull(graphene.String)
    value = graphene.NonNull(graphene.String)

    class Meta:
        name = "RepositoryMetadata"


class GrapheneRepositoryOrigin(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    repository_location_name = graphene.NonNull(graphene.String)
    repository_name = graphene.NonNull(graphene.String)
    repository_location_metadata = non_null_list(GrapheneRepositoryMetadata)

    class Meta:
        name = "RepositoryOrigin"

    def __init__(self, origin):
        super().__init__()
        self._origin = check.inst_param(origin, "origin", ExternalRepositoryOrigin)

    def resolve_id(self, _graphene_info):
        return self._origin.get_id()

    def resolve_repository_location_name(self, _graphene_info):
        return self._origin.repository_location_origin.location_name

    def resolve_repository_name(self, _graphene_info):
        return self._origin.repository_name

    def resolve_repository_location_metadata(self, _graphene_info):
        metadata = self._origin.repository_location_origin.get_display_metadata()
        return [
            GrapheneRepositoryMetadata(key=key, value=value)
            for key, value in metadata.items()
            if value is not None
        ]
