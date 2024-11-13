from typing import Callable

import dagster._check as check
import graphene
from dagster._core.snap import ConfigTypeSnap, LoggerDefSnap

from dagster_graphql.schema.config_types import GrapheneConfigTypeField
from dagster_graphql.schema.util import ResolveInfo


class GrapheneLogger(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    configField = graphene.Field(GrapheneConfigTypeField)

    class Meta:
        name = "Logger"

    def __init__(
        self,
        get_config_type: Callable[[str], ConfigTypeSnap],
        logger_def_snap: LoggerDefSnap,
    ):
        super().__init__()
        self._get_config_type = get_config_type
        self._logger_def_snap = check.inst_param(logger_def_snap, "logger_def_snap", LoggerDefSnap)
        self.name = logger_def_snap.name
        self.description = logger_def_snap.description

    def resolve_configField(self, _: ResolveInfo):
        if self._logger_def_snap.config_field_snap:
            try:
                # config type may not be present if mode config mapped, null out gracefully
                self._get_config_type(self._logger_def_snap.config_field_snap.type_key)
            except KeyError:
                return None

            return GrapheneConfigTypeField(
                self._get_config_type,
                field_snap=self._logger_def_snap.config_field_snap,
            )

        return None
