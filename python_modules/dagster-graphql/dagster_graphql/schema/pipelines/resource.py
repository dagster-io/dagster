import graphene

from dagster import check
from dagster.core.snap import ConfigSchemaSnapshot, ResourceDefSnap

from ..config_types import GrapheneConfigTypeField


class GrapheneResourceOrigin(graphene.Enum):
    FROM_REPO_DEFAULT = "FROM_REPO_DEFAULT"
    FROM_SYSTEM_DEFAULT = "FROM_SYSTEM_DEFAULT"

    class Meta:
        name = "ResourceOrigin"


class GrapheneResource(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    configField = graphene.Field(GrapheneConfigTypeField)
    origin = graphene.Field(GrapheneResourceOrigin)

    class Meta:
        name = "Resource"

    def __init__(self, config_schema_snapshot, resource_def_snap):
        super().__init__()
        self._config_schema_snapshot = check.opt_inst_param(
            config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot
        )
        self._resource_def_snap = check.inst_param(
            resource_def_snap, "resource_def_snap", ResourceDefSnap
        )
        self.name = resource_def_snap.name
        self.description = resource_def_snap.description

    def resolve_configField(self, _graphene_info):
        if (
            self._resource_def_snap.config_field_snap
            # config type may not be present if mode config mapped
            and self._config_schema_snapshot.has_config_snap(
                self._resource_def_snap.config_field_snap.type_key
            )
        ):
            return GrapheneConfigTypeField(
                config_schema_snapshot=self._config_schema_snapshot,
                field_snap=self._resource_def_snap.config_field_snap,
            )

        return None

    def resolve_origin(self, _graphene_info):
        return self._resource_def_snap.origin
