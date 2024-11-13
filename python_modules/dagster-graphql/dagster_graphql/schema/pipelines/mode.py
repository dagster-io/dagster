from typing import Callable

import dagster._check as check
import graphene
from dagster._config.snap import ConfigTypeSnap
from dagster._core.snap import ModeDefSnap

from dagster_graphql.schema.pipelines.logger import GrapheneLogger
from dagster_graphql.schema.pipelines.resource import GrapheneResource
from dagster_graphql.schema.util import ResolveInfo, non_null_list


class GrapheneMode(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    resources = non_null_list(GrapheneResource)
    loggers = non_null_list(GrapheneLogger)

    class Meta:
        name = "Mode"

    def __init__(
        self,
        get_config_type: Callable[[str], ConfigTypeSnap],
        job_graphql_id: str,
        mode_def_snap: ModeDefSnap,
    ):
        super().__init__()
        self._mode_def_snap = check.inst_param(mode_def_snap, "mode_def_snap", ModeDefSnap)
        self._get_config_type = get_config_type
        self._job_graphql_id = job_graphql_id

    def resolve_id(self, _graphene_info: ResolveInfo):
        return f"{self._job_graphql_id}-{self._mode_def_snap.name}"

    def resolve_name(self, _graphene_info: ResolveInfo):
        return self._mode_def_snap.name

    def resolve_description(self, _graphene_info: ResolveInfo):
        return self._mode_def_snap.description

    def resolve_resources(self, _graphene_info: ResolveInfo):
        return [
            GrapheneResource(self._get_config_type, resource_def_snap)
            for resource_def_snap in sorted(self._mode_def_snap.resource_def_snaps)
        ]

    def resolve_loggers(self, _graphene_info: ResolveInfo):
        return [
            GrapheneLogger(self._get_config_type, logger_def_snap)
            for logger_def_snap in sorted(self._mode_def_snap.logger_def_snaps)
        ]
