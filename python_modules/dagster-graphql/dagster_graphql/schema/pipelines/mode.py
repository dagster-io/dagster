import dagster._check as check
import graphene
from dagster._core.snap import ConfigSchemaSnapshot, ModeDefSnap

from ..util import ResolveInfo, non_null_list
from .logger import GrapheneLogger
from .resource import GrapheneResource


class GrapheneMode(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    resources = non_null_list(GrapheneResource)
    loggers = non_null_list(GrapheneLogger)

    class Meta:
        name = "Mode"

    def __init__(self, config_schema_snapshot, pipeline_snapshot_id, mode_def_snap):
        super().__init__()
        self._mode_def_snap = check.inst_param(mode_def_snap, "mode_def_snap", ModeDefSnap)
        self._config_schema_snapshot = check.inst_param(
            config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot
        )
        self._job_snapshot_id = pipeline_snapshot_id

    def resolve_id(self, _graphene_info: ResolveInfo):
        return f"{self._job_snapshot_id}-{self._mode_def_snap.name}"

    def resolve_name(self, _graphene_info: ResolveInfo):
        return self._mode_def_snap.name

    def resolve_description(self, _graphene_info: ResolveInfo):
        return self._mode_def_snap.description

    def resolve_resources(self, _graphene_info: ResolveInfo):
        return [
            GrapheneResource(self._config_schema_snapshot, resource_def_snap)
            for resource_def_snap in sorted(self._mode_def_snap.resource_def_snaps)
        ]

    def resolve_loggers(self, _graphene_info: ResolveInfo):
        return [
            GrapheneLogger(self._config_schema_snapshot, logger_def_snap)
            for logger_def_snap in sorted(self._mode_def_snap.logger_def_snaps)
        ]
