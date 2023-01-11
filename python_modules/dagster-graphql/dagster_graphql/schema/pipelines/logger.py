import dagster._check as check
import graphene
from dagster._core.snap import ConfigSchemaSnapshot, LoggerDefSnap

from ..config_types import GrapheneConfigTypeField


class GrapheneLogger(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    configField = graphene.Field(GrapheneConfigTypeField)

    class Meta:
        name = "Logger"

    def __init__(self, config_schema_snapshot, logger_def_snap):
        super().__init__()
        self._config_schema_snapshot = check.inst_param(
            config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot
        )
        self._logger_def_snap = check.inst_param(logger_def_snap, "logger_def_snap", LoggerDefSnap)
        self.name = logger_def_snap.name
        self.description = logger_def_snap.description

    def resolve_configField(self, _):
        if (
            self._logger_def_snap.config_field_snap
            # config type may not be present if mode config mapped
            and self._config_schema_snapshot.has_config_snap(
                self._logger_def_snap.config_field_snap.type_key
            )
        ):
            return GrapheneConfigTypeField(
                config_schema_snapshot=self._config_schema_snapshot,
                field_snap=self._logger_def_snap.config_field_snap,
            )

        return None
