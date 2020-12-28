from functools import lru_cache

import yaml
from dagster import check
from dagster.core.host_representation import (
    ExternalPipeline,
    ExternalPresetData,
    RepresentedPipeline,
)
from dagster.core.snap import ConfigSchemaSnapshot, LoggerDefSnap, ModeDefSnap, ResourceDefSnap
from dagster.core.storage.pipeline_run import PipelineRunsFilter
from dagster.core.storage.tags import TagType, get_tag_type
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_runs import get_runs
from dagster_graphql.implementation.fetch_schedules import get_schedules_for_pipeline
from dagster_graphql.implementation.fetch_sensors import get_sensors_for_pipeline
from dagster_graphql.implementation.utils import UserFacingGraphQLError, capture_dauphin_error

from .config_types import DauphinConfigTypeField
from .dagster_types import to_dauphin_dagster_type
from .solids import DauphinSolidContainer, build_dauphin_solid_handles, build_dauphin_solids


class DauphinPipelineReference(dauphin.Interface):
    """This interface supports the case where we can look up a pipeline successfully in the
    repository available to the DagsterInstance/graphql context, as well as the case where we know
    that a pipeline exists/existed thanks to materialized data such as logs and run metadata, but
    where we can't look the concrete pipeline up."""

    class Meta:
        name = "PipelineReference"

    name = dauphin.NonNull(dauphin.String)
    solidSelection = dauphin.List(dauphin.NonNull(dauphin.String))


class DauphinUnknownPipeline(dauphin.ObjectType):
    class Meta:
        name = "UnknownPipeline"
        interfaces = (DauphinPipelineReference,)

    name = dauphin.NonNull(dauphin.String)
    solidSelection = dauphin.List(dauphin.NonNull(dauphin.String))


class DauphinIPipelineSnapshotMixin:
    # Mixin this class to implement IPipelineSnapshot
    #
    # Graphene has some strange properties that make it so that you cannot
    # implement ABCs nor use properties in an overridable way. So the way
    # the mixin works is that the target classes have to have a method
    # get_represented_pipeline()
    #

    def get_represented_pipeline(self):
        raise NotImplementedError()

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    id = dauphin.NonNull(dauphin.ID)
    pipeline_snapshot_id = dauphin.NonNull(dauphin.String)
    dagster_types = dauphin.non_null_list("DagsterType")
    dagster_type_or_error = dauphin.Field(
        dauphin.NonNull("DagsterTypeOrError"),
        dagsterTypeName=dauphin.Argument(dauphin.NonNull(dauphin.String)),
    )
    solids = dauphin.non_null_list("Solid")
    modes = dauphin.non_null_list("Mode")
    solid_handles = dauphin.Field(
        dauphin.non_null_list("SolidHandle"), parentHandleID=dauphin.String()
    )
    solid_handle = dauphin.Field(
        "SolidHandle", handleID=dauphin.Argument(dauphin.NonNull(dauphin.String)),
    )
    tags = dauphin.non_null_list("PipelineTag")
    runs = dauphin.Field(
        dauphin.non_null_list("PipelineRun"), cursor=dauphin.String(), limit=dauphin.Int(),
    )
    schedules = dauphin.non_null_list("Schedule")
    sensors = dauphin.non_null_list("Sensor")
    parent_snapshot_id = dauphin.String()

    def resolve_pipeline_snapshot_id(self, _):
        return self.get_represented_pipeline().identifying_pipeline_snapshot_id

    def resolve_id(self, _):
        return self.get_represented_pipeline().identifying_pipeline_snapshot_id

    def resolve_name(self, _):
        return self.get_represented_pipeline().name

    def resolve_description(self, _):
        return self.get_represented_pipeline().description

    def resolve_dagster_types(self, _graphene_info):
        represented_pipeline = self.get_represented_pipeline()
        return sorted(
            list(
                map(
                    lambda dt: to_dauphin_dagster_type(
                        represented_pipeline.pipeline_snapshot, dt.key
                    ),
                    [t for t in represented_pipeline.dagster_type_snaps if t.name],
                )
            ),
            key=lambda dagster_type: dagster_type.name,
        )

    @capture_dauphin_error
    def resolve_dagster_type_or_error(self, _, **kwargs):
        type_name = kwargs["dagsterTypeName"]

        represented_pipeline = self.get_represented_pipeline()

        if not represented_pipeline.has_dagster_type_named(type_name):
            from .errors import DauphinDagsterTypeNotFoundError

            raise UserFacingGraphQLError(
                DauphinDagsterTypeNotFoundError(dagster_type_name=type_name)
            )

        return to_dauphin_dagster_type(
            represented_pipeline.pipeline_snapshot,
            represented_pipeline.get_dagster_type_by_name(type_name).key,
        )

    def resolve_solids(self, _graphene_info):
        represented_pipeline = self.get_represented_pipeline()
        return build_dauphin_solids(represented_pipeline, represented_pipeline.dep_structure_index,)

    def resolve_modes(self, _):
        represented_pipeline = self.get_represented_pipeline()
        return [
            DauphinMode(represented_pipeline.config_schema_snapshot, mode_def_snap)
            for mode_def_snap in sorted(
                represented_pipeline.mode_def_snaps, key=lambda item: item.name
            )
        ]

    def resolve_solid_handle(self, _graphene_info, handleID):
        return _get_solid_handles(self.get_represented_pipeline()).get(handleID)

    def resolve_solid_handles(self, _graphene_info, **kwargs):
        handles = _get_solid_handles(self.get_represented_pipeline())
        parentHandleID = kwargs.get("parentHandleID")

        if parentHandleID == "":
            handles = {key: handle for key, handle in handles.items() if not handle.parent}
        elif parentHandleID is not None:
            handles = {
                key: handle
                for key, handle in handles.items()
                if handle.parent and handle.parent.handleID.to_string() == parentHandleID
            }

        return [handles[key] for key in sorted(handles)]

    def resolve_tags(self, graphene_info):
        represented_pipeline = self.get_represented_pipeline()
        return [
            graphene_info.schema.type_named("PipelineTag")(key=key, value=value)
            for key, value in represented_pipeline.pipeline_snapshot.tags.items()
        ]

    def resolve_solidSelection(self, _graphene_info):
        return self.get_represented_pipeline().solid_selection

    def resolve_runs(self, graphene_info, **kwargs):
        runs_filter = PipelineRunsFilter(pipeline_name=self.get_represented_pipeline().name)
        return get_runs(graphene_info, runs_filter, kwargs.get("cursor"), kwargs.get("limit"))

    def resolve_schedules(self, graphene_info):
        represented_pipeline = self.get_represented_pipeline()
        if not isinstance(represented_pipeline, ExternalPipeline):
            # this is an historical pipeline snapshot, so there are not any associated running
            # schedules
            return []

        pipeline_selector = represented_pipeline.handle.to_selector()
        schedules = get_schedules_for_pipeline(graphene_info, pipeline_selector)
        return schedules

    def resolve_sensors(self, graphene_info):
        represented_pipeline = self.get_represented_pipeline()
        if not isinstance(represented_pipeline, ExternalPipeline):
            # this is an historical pipeline snapshot, so there are not any associated running
            # sensors
            return []

        pipeline_selector = represented_pipeline.handle.to_selector()
        sensors = get_sensors_for_pipeline(graphene_info, pipeline_selector)
        return sensors

    def resolve_parent_snapshot_id(self, _graphene_info):
        lineage_snapshot = self.get_represented_pipeline().pipeline_snapshot.lineage_snapshot
        if lineage_snapshot:
            return lineage_snapshot.parent_snapshot_id
        else:
            return None


class DauphinIPipelineSnapshot(dauphin.Interface):
    class Meta:
        name = "IPipelineSnapshot"

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    pipeline_snapshot_id = dauphin.NonNull(dauphin.String)
    dagster_types = dauphin.non_null_list("DagsterType")
    dagster_type_or_error = dauphin.Field(
        dauphin.NonNull("DagsterTypeOrError"),
        dagsterTypeName=dauphin.Argument(dauphin.NonNull(dauphin.String)),
    )
    solids = dauphin.non_null_list("Solid")
    modes = dauphin.non_null_list("Mode")
    solid_handles = dauphin.Field(
        dauphin.non_null_list("SolidHandle"), parentHandleID=dauphin.String()
    )
    solid_handle = dauphin.Field(
        "SolidHandle", handleID=dauphin.Argument(dauphin.NonNull(dauphin.String)),
    )
    tags = dauphin.non_null_list("PipelineTag")


class DauphinPipeline(DauphinIPipelineSnapshotMixin, dauphin.ObjectType):
    class Meta:
        name = "Pipeline"
        interfaces = (DauphinSolidContainer, DauphinIPipelineSnapshot)

    id = dauphin.NonNull(dauphin.ID)
    presets = dauphin.non_null_list("PipelinePreset")
    runs = dauphin.Field(
        dauphin.non_null_list("PipelineRun"), cursor=dauphin.String(), limit=dauphin.Int(),
    )

    def __init__(self, external_pipeline):
        self._external_pipeline = check.inst_param(
            external_pipeline, "external_pipeline", ExternalPipeline
        )

    def resolve_id(self, _graphene_info):
        return self._external_pipeline.get_external_origin_id()

    def get_represented_pipeline(self):
        return self._external_pipeline

    def resolve_presets(self, _graphene_info):
        return [
            DauphinPipelinePreset(preset, self._external_pipeline.name)
            for preset in sorted(self._external_pipeline.active_presets, key=lambda item: item.name)
        ]


@lru_cache(maxsize=32)
def _get_solid_handles(represented_pipeline):
    check.inst_param(represented_pipeline, "represented_pipeline", RepresentedPipeline)
    return {
        str(item.handleID): item
        for item in build_dauphin_solid_handles(
            represented_pipeline, represented_pipeline.dep_structure_index
        )
    }


class DauphinResource(dauphin.ObjectType):
    class Meta:
        name = "Resource"

    def __init__(self, config_schema_snapshot, resource_def_snap):
        self._config_schema_snapshot = check.inst_param(
            config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot
        )
        self._resource_dep_snap = check.inst_param(
            resource_def_snap, "resource_def_snap", ResourceDefSnap
        )
        self.name = resource_def_snap.name
        self.description = resource_def_snap.description

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    configField = dauphin.Field("ConfigTypeField")

    def resolve_configField(self, _):
        return (
            DauphinConfigTypeField(
                config_schema_snapshot=self._config_schema_snapshot,
                field_snap=self._resource_dep_snap.config_field_snap,
            )
            if self._resource_dep_snap.config_field_snap
            else None
        )


class DauphinLogger(dauphin.ObjectType):
    class Meta:
        name = "Logger"

    def __init__(self, config_schema_snapshot, logger_def_snap):
        self._config_schema_snapshot = check.inst_param(
            config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot
        )
        self._logger_def_snap = check.inst_param(logger_def_snap, "logger_def_snap", LoggerDefSnap)
        self.name = logger_def_snap.name
        self.description = logger_def_snap.description

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    configField = dauphin.Field("ConfigTypeField")

    def resolve_configField(self, _):
        return (
            DauphinConfigTypeField(
                config_schema_snapshot=self._config_schema_snapshot,
                field_snap=self._logger_def_snap.config_field_snap,
            )
            if self._logger_def_snap.config_field_snap
            else None
        )


class DauphinMode(dauphin.ObjectType):
    def __init__(self, config_schema_snapshot, mode_def_snap):
        self._mode_def_snap = check.inst_param(mode_def_snap, "mode_def_snap", ModeDefSnap)
        self._config_schema_snapshot = check.inst_param(
            config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot
        )

    class Meta:
        name = "Mode"

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    resources = dauphin.non_null_list("Resource")
    loggers = dauphin.non_null_list("Logger")

    def resolve_name(self, _graphene_info):
        return self._mode_def_snap.name

    def resolve_description(self, _graphene_info):
        return self._mode_def_snap.description

    def resolve_resources(self, _graphene_info):
        return [
            DauphinResource(self._config_schema_snapshot, resource_def_snap)
            for resource_def_snap in sorted(self._mode_def_snap.resource_def_snaps)
        ]

    def resolve_loggers(self, _graphene_info):
        return [
            DauphinLogger(self._config_schema_snapshot, logger_def_snap)
            for logger_def_snap in sorted(self._mode_def_snap.logger_def_snaps)
        ]


class DauphinMetadataItemDefinition(dauphin.ObjectType):
    class Meta:
        name = "MetadataItemDefinition"

    key = dauphin.NonNull(dauphin.String)
    value = dauphin.NonNull(dauphin.String)


class DauphinPipelinePreset(dauphin.ObjectType):
    class Meta:
        name = "PipelinePreset"

    name = dauphin.NonNull(dauphin.String)
    solidSelection = dauphin.List(dauphin.NonNull(dauphin.String))
    runConfigYaml = dauphin.NonNull(dauphin.String)
    mode = dauphin.NonNull(dauphin.String)
    tags = dauphin.non_null_list("PipelineTag")

    def __init__(self, active_preset_data, pipeline_name):
        self._active_preset_data = check.inst_param(
            active_preset_data, "active_preset_data", ExternalPresetData
        )
        self._pipeline_name = check.str_param(pipeline_name, "pipeline_name")

    def resolve_name(self, _graphene_info):
        return self._active_preset_data.name

    def resolve_solidSelection(self, _graphene_info):
        return self._active_preset_data.solid_selection

    def resolve_runConfigYaml(self, _graphene_info):
        yaml_str = yaml.safe_dump(
            self._active_preset_data.run_config, default_flow_style=False, allow_unicode=True
        )
        return yaml_str if yaml_str else ""

    def resolve_mode(self, _graphene_info):
        return self._active_preset_data.mode

    def resolve_tags(self, graphene_info):
        return [
            graphene_info.schema.type_named("PipelineTag")(key=key, value=value)
            for key, value in self._active_preset_data.tags.items()
            if get_tag_type(key) != TagType.HIDDEN
        ]


class DauphinPipelineSnapshot(DauphinIPipelineSnapshotMixin, dauphin.ObjectType):
    def __init__(self, represented_pipeline):
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )

    class Meta:
        name = "PipelineSnapshot"
        interfaces = (DauphinIPipelineSnapshot, DauphinPipelineReference)

    def get_represented_pipeline(self):
        return self._represented_pipeline


class DauphinPipelineSnapshotOrError(dauphin.Union):
    class Meta:
        name = "PipelineSnapshotOrError"
        types = (
            "PipelineSnapshot",
            "PipelineSnapshotNotFoundError",
            "PipelineNotFoundError",
            "PythonError",
        )
