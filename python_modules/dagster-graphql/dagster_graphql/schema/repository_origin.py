from collections.abc import Sequence

import dagster._check as check
import graphene
from dagster._core.remote_representation import RemoteRepositoryOrigin

from dagster_graphql.schema.util import ResolveInfo, non_null_list


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

    def __init__(self, origin: RemoteRepositoryOrigin):
        super().__init__()
        self._origin = check.inst_param(origin, "origin", RemoteRepositoryOrigin)

    def resolve_id(self, _graphene_info: ResolveInfo) -> str:
        return self._origin.get_id()

    def resolve_repository_location_name(self, _graphene_info: ResolveInfo) -> str:
        return self._origin.code_location_origin.location_name

    def resolve_repository_name(self, _graphene_info: ResolveInfo) -> str:
        return self._origin.repository_name

    def resolve_repository_location_metadata(
        self, _graphene_info: ResolveInfo
    ) -> Sequence[GrapheneRepositoryMetadata]:
        metadata = self._origin.code_location_origin.get_display_metadata()
        return [
            GrapheneRepositoryMetadata(key=key, value=value)
            for key, value in metadata.items()
            if value is not None
        ]
