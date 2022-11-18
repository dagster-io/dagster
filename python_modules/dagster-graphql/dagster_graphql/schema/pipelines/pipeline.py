from typing import List

import graphene
from dagster_graphql.implementation.events import iterate_metadata_entries
from dagster_graphql.schema.metadata import GrapheneMetadataEntry

import dagster._check as check
from dagster._core.events import DagsterEventType
from dagster._core.host_representation.external import ExternalExecutionPlan, ExternalPipeline
from dagster._core.host_representation.external_data import ExternalPresetData
from dagster._core.storage.pipeline_run import PipelineRunStatus, RunRecord, RunsFilter
from dagster._core.storage.tags import REPOSITORY_LABEL_TAG, TagType, get_tag_type
from dagster._utils import datetime_as_float
from dagster._utils.yaml_utils import dump_run_config_yaml

from ...implementation.events import from_event_record
from ...implementation.fetch_assets import get_assets_for_run_id, get_unique_asset_id
from ...implementation.fetch_pipelines import get_pipeline_reference_or_raise
from ...implementation.fetch_runs import get_runs, get_stats, get_step_stats
from ...implementation.fetch_schedules import get_schedules_for_pipeline
from ...implementation.fetch_sensors import get_sensors_for_pipeline
from ...implementation.loader import BatchRunLoader, RepositoryScopedBatchLoader
from ...implementation.utils import UserFacingGraphQLError, capture_error
from ..asset_key import GrapheneAssetKey
from ..dagster_types import GrapheneDagsterType, GrapheneDagsterTypeOrError, to_dagster_type
from ..errors import GrapheneDagsterTypeNotFoundError, GraphenePythonError, GrapheneRunNotFoundError
from ..execution import GrapheneExecutionPlan
from ..inputs import GrapheneInputTag
from ..logs.compute_logs import GrapheneCapturedLogs, GrapheneComputeLogs, from_captured_log_data
from ..logs.events import (
    GrapheneDagsterRunEvent,
    GrapheneMaterializationEvent,
    GrapheneObservationEvent,
    GrapheneRunStepStats,
)
from ..repository_origin import GrapheneRepositoryOrigin
from ..runs import GrapheneRunConfigData
from ..schedules.schedules import GrapheneSchedule
from ..sensors import GrapheneSensor
from ..solids import (
    GrapheneSolid,
    GrapheneSolidContainer,
    GrapheneSolidHandle,
    build_solid_handles,
    build_solids,
)
from ..tags import GraphenePipelineTag
from ..util import non_null_list
from .mode import GrapheneMode
from .pipeline_ref import GraphenePipelineReference
from .pipeline_run_stats import GrapheneRunStatsSnapshotOrError
from .status import GrapheneRunStatus

STARTED_STATUSES = {
    PipelineRunStatus.STARTED,
    PipelineRunStatus.SUCCESS,
    PipelineRunStatus.FAILURE,
    PipelineRunStatus.CANCELED,
}

COMPLETED_STATUSES = {
    PipelineRunStatus.FAILURE,
    PipelineRunStatus.SUCCESS,
    PipelineRunStatus.CANCELED,
}


def parse_time_range_args(args):
    try:
        before_timestamp = (
            int(args.get("beforeTimestampMillis")) / 1000.0
            if args.get("beforeTimestampMillis")
            else None
        )
    except ValueError:
        before_timestamp = None

    try:
        after_timestamp = (
            int(args.get("afterTimestampMillis")) / 1000.0
            if args.get("afterTimestampMillis")
            else None
        )
    except ValueError:
        after_timestamp = None

    return before_timestamp, after_timestamp


class GrapheneMaterializationCountSingleDimension(graphene.ObjectType):
    materializationCounts = non_null_list(graphene.Int)

    class Meta:
        name = "MaterializationCountSingleDimension"


class GrapheneMaterializationCountGroupedByDimension(graphene.ObjectType):
    materializationCountsGrouped = graphene.NonNull(graphene.List(non_null_list(graphene.Int)))

    class Meta:
        name = "MaterializationCountGroupedByDimension"


class GraphenePartitionMaterializationCounts(graphene.Union):
    class Meta:
        types = (
            GrapheneMaterializationCountSingleDimension,
            GrapheneMaterializationCountGroupedByDimension,
        )
        name = "PartitionMaterializationCounts"


class GrapheneAsset(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    key = graphene.NonNull(GrapheneAssetKey)
    assetMaterializations = graphene.Field(
        non_null_list(GrapheneMaterializationEvent),
        partitions=graphene.List(graphene.String),
        partitionInLast=graphene.Int(),
        beforeTimestampMillis=graphene.String(),
        afterTimestampMillis=graphene.String(),
        limit=graphene.Int(),
        tags=graphene.Argument(graphene.List(graphene.NonNull(GrapheneInputTag))),
    )
    assetObservations = graphene.Field(
        non_null_list(GrapheneObservationEvent),
        partitions=graphene.List(graphene.String),
        partitionInLast=graphene.Int(),
        beforeTimestampMillis=graphene.String(),
        afterTimestampMillis=graphene.String(),
        limit=graphene.Int(),
    )
    definition = graphene.Field("dagster_graphql.schema.asset_graph.GrapheneAssetNode")

    class Meta:
        name = "Asset"

    def __init__(self, key, definition=None):
        super().__init__(key=key, definition=definition)
        self._definition = definition

    def resolve_id(self, _):
        # If the asset is not a SDA asset (has no definition), the id is the asset key
        # Else, return a unique idenitifer containing the repository location and name
        if self._definition:
            return get_unique_asset_id(
                self.key,
                self._definition.repository_location.name,
                self._definition.external_repository.name,
            )
        return get_unique_asset_id(self.key)

    def resolve_assetMaterializations(self, graphene_info, **kwargs):
        from ...implementation.fetch_assets import get_asset_materializations

        before_timestamp, after_timestamp = parse_time_range_args(kwargs)
        limit = kwargs.get("limit")
        partitions = kwargs.get("partitions")
        partitionInLast = kwargs.get("partitionInLast")
        if partitionInLast and self._definition:
            partitions = self._definition.get_partition_keys()[-int(partitionInLast) :]
        tags = kwargs.get("tags")

        events = get_asset_materializations(
            graphene_info,
            self.key,
            partitions=partitions,
            before_timestamp=before_timestamp,
            after_timestamp=after_timestamp,
            tags={tag["name"]: tag["value"] for tag in tags} if tags else None,
            limit=limit,
        )
        run_ids = [event.run_id for event in events]
        loader = BatchRunLoader(graphene_info.context.instance, run_ids) if run_ids else None
        return [GrapheneMaterializationEvent(event=event, loader=loader) for event in events]

    def resolve_assetObservations(self, graphene_info, **kwargs):
        from ...implementation.fetch_assets import get_asset_observations

        before_timestamp, after_timestamp = parse_time_range_args(kwargs)
        limit = kwargs.get("limit")
        partitions = kwargs.get("partitions")
        partitionInLast = kwargs.get("partitionInLast")
        if partitionInLast and self._definition:
            partitions = self._definition.get_partition_keys()[-int(partitionInLast) :]

        return [
            GrapheneObservationEvent(event=event)
            for event in get_asset_observations(
                graphene_info,
                self.key,
                partitions=partitions,
                before_timestamp=before_timestamp,
                after_timestamp=after_timestamp,
                limit=limit,
            )
        ]


class GrapheneEventConnection(graphene.ObjectType):
    class Meta:
        name = "EventConnection"

    events = non_null_list(GrapheneDagsterRunEvent)
    cursor = graphene.NonNull(graphene.String)
    hasMore = graphene.NonNull(graphene.Boolean)


class GrapheneEventConnectionOrError(graphene.Union):
    class Meta:
        types = (GrapheneEventConnection, GrapheneRunNotFoundError, GraphenePythonError)
        name = "EventConnectionOrError"


class GraphenePipelineRun(graphene.Interface):
    id = graphene.NonNull(graphene.ID)
    runId = graphene.NonNull(graphene.String)
    # Nullable because of historical runs
    pipelineSnapshotId = graphene.String()
    repositoryOrigin = graphene.Field(GrapheneRepositoryOrigin)
    status = graphene.NonNull(GrapheneRunStatus)
    pipeline = graphene.NonNull(GraphenePipelineReference)
    pipelineName = graphene.NonNull(graphene.String)
    jobName = graphene.NonNull(graphene.String)
    solidSelection = graphene.List(graphene.NonNull(graphene.String))
    stats = graphene.NonNull(GrapheneRunStatsSnapshotOrError)
    stepStats = non_null_list(GrapheneRunStepStats)
    computeLogs = graphene.Field(
        graphene.NonNull(GrapheneComputeLogs),
        stepKey=graphene.Argument(graphene.NonNull(graphene.String)),
        description="""
        Compute logs are the stdout/stderr logs for a given solid step computation
        """,
    )
    capturedLogs = graphene.Field(
        graphene.NonNull(GrapheneCapturedLogs),
        fileKey=graphene.Argument(graphene.NonNull(graphene.String)),
        description="""
        Captured logs are the stdout/stderr logs for a given file key within the run
        """,
    )
    executionPlan = graphene.Field(GrapheneExecutionPlan)
    stepKeysToExecute = graphene.List(graphene.NonNull(graphene.String))
    runConfigYaml = graphene.NonNull(graphene.String)
    runConfig = graphene.NonNull(GrapheneRunConfigData)
    mode = graphene.NonNull(graphene.String)
    tags = non_null_list(GraphenePipelineTag)
    rootRunId = graphene.Field(graphene.String)
    parentRunId = graphene.Field(graphene.String)
    canTerminate = graphene.NonNull(graphene.Boolean)
    assets = non_null_list(GrapheneAsset)
    eventConnection = graphene.Field(
        graphene.NonNull(GrapheneEventConnection),
        afterCursor=graphene.Argument(graphene.String),
    )

    class Meta:
        name = "PipelineRun"


class GrapheneRun(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    runId = graphene.NonNull(graphene.String)
    # Nullable because of historical runs
    pipelineSnapshotId = graphene.String()
    repositoryOrigin = graphene.Field(GrapheneRepositoryOrigin)
    status = graphene.NonNull(GrapheneRunStatus)
    pipeline = graphene.NonNull(GraphenePipelineReference)
    pipelineName = graphene.NonNull(graphene.String)
    jobName = graphene.NonNull(graphene.String)
    solidSelection = graphene.List(graphene.NonNull(graphene.String))
    assetSelection = graphene.List(graphene.NonNull(GrapheneAssetKey))
    resolvedOpSelection = graphene.List(graphene.NonNull(graphene.String))
    stats = graphene.NonNull(GrapheneRunStatsSnapshotOrError)
    stepStats = non_null_list(GrapheneRunStepStats)
    computeLogs = graphene.Field(
        graphene.NonNull(GrapheneComputeLogs),
        stepKey=graphene.Argument(graphene.NonNull(graphene.String)),
        description="""
        Compute logs are the stdout/stderr logs for a given solid step computation
        """,
    )
    executionPlan = graphene.Field(GrapheneExecutionPlan)
    stepKeysToExecute = graphene.List(graphene.NonNull(graphene.String))
    runConfigYaml = graphene.NonNull(graphene.String)
    runConfig = graphene.NonNull(GrapheneRunConfigData)
    mode = graphene.NonNull(graphene.String)
    tags = non_null_list(GraphenePipelineTag)
    rootRunId = graphene.Field(graphene.String)
    parentRunId = graphene.Field(graphene.String)
    canTerminate = graphene.NonNull(graphene.Boolean)
    assetMaterializations = non_null_list(GrapheneMaterializationEvent)
    assets = non_null_list(GrapheneAsset)
    eventConnection = graphene.Field(
        graphene.NonNull(GrapheneEventConnection),
        afterCursor=graphene.Argument(graphene.String),
    )
    startTime = graphene.Float()
    endTime = graphene.Float()
    updateTime = graphene.Float()

    class Meta:
        interfaces = (GraphenePipelineRun,)
        name = "Run"

    def __init__(self, record: RunRecord):
        check.inst_param(record, "record", RunRecord)
        pipeline_run = record.pipeline_run
        super().__init__(
            runId=pipeline_run.run_id,
            status=pipeline_run.status.value,
            mode=pipeline_run.mode,
        )
        self._pipeline_run = pipeline_run
        self._run_record = record
        self._run_stats = None

    def resolve_id(self, _graphene_info):
        return self._pipeline_run.run_id

    def resolve_repositoryOrigin(self, _graphene_info):
        return (
            GrapheneRepositoryOrigin(
                self._pipeline_run.external_pipeline_origin.external_repository_origin
            )
            if self._pipeline_run.external_pipeline_origin
            else None
        )

    def resolve_pipeline(self, graphene_info):
        return get_pipeline_reference_or_raise(graphene_info, self._pipeline_run)

    def resolve_pipelineName(self, _graphene_info):
        return self._pipeline_run.pipeline_name

    def resolve_jobName(self, _graphene_info):
        return self._pipeline_run.pipeline_name

    def resolve_solidSelection(self, _graphene_info):
        return self._pipeline_run.solid_selection

    def resolve_assetSelection(self, _graphene_info):
        return self._pipeline_run.asset_selection

    def resolve_resolvedOpSelection(self, _graphene_info):
        return self._pipeline_run.solids_to_execute

    def resolve_pipelineSnapshotId(self, _graphene_info):
        return self._pipeline_run.pipeline_snapshot_id

    def resolve_stats(self, graphene_info):
        return get_stats(graphene_info, self.run_id)

    def resolve_stepStats(self, graphene_info):
        return get_step_stats(graphene_info, self.run_id)

    def resolve_computeLogs(self, _graphene_info, stepKey):
        return GrapheneComputeLogs(runId=self.run_id, stepKey=stepKey)

    def resolve_capturedLogs(self, graphene_info, fileKey):
        log_key = graphene_info.context.instance.compute_log_manager.build_log_key_for_run(
            self.run_id, fileKey
        )
        log_data = graphene_info.context.instance.compute_log_manager.get_log_data(log_key)
        return from_captured_log_data(log_data)

    def resolve_executionPlan(self, graphene_info):
        if not (
            self._pipeline_run.execution_plan_snapshot_id
            and self._pipeline_run.pipeline_snapshot_id
        ):
            return None

        instance = graphene_info.context.instance

        execution_plan_snapshot = instance.get_execution_plan_snapshot(
            self._pipeline_run.execution_plan_snapshot_id
        )
        return (
            GrapheneExecutionPlan(
                ExternalExecutionPlan(execution_plan_snapshot=execution_plan_snapshot)
            )
            if execution_plan_snapshot
            else None
        )

    def resolve_stepKeysToExecute(self, _graphene_info):
        return self._pipeline_run.step_keys_to_execute

    def resolve_runConfigYaml(self, _graphene_info):
        return dump_run_config_yaml(self._pipeline_run.run_config)

    def resolve_runConfig(self, _graphene_info):
        return self._pipeline_run.run_config

    def resolve_tags(self, _graphene_info):
        return [
            GraphenePipelineTag(key=key, value=value)
            for key, value in self._pipeline_run.tags.items()
            if get_tag_type(key) != TagType.HIDDEN
        ]

    def resolve_rootRunId(self, _graphene_info):
        return self._pipeline_run.root_run_id

    def resolve_parentRunId(self, _graphene_info):
        return self._pipeline_run.parent_run_id

    @property
    def run_id(self):
        return self.runId

    def resolve_canTerminate(self, _graphene_info):
        # short circuit if the pipeline run is in a terminal state
        if self._pipeline_run.is_finished:
            return False
        return (
            self._pipeline_run.status == PipelineRunStatus.QUEUED
            or self._pipeline_run.status == PipelineRunStatus.STARTED
        )

    def resolve_assets(self, graphene_info):
        return get_assets_for_run_id(graphene_info, self.run_id)

    def resolve_assetMaterializations(self, graphene_info):
        # convenience field added for users querying directly via GraphQL
        return [
            GrapheneMaterializationEvent(event=event)
            for event in graphene_info.context.instance.all_logs(
                self.run_id, of_type=DagsterEventType.ASSET_MATERIALIZATION
            )
        ]

    def resolve_eventConnection(self, graphene_info, afterCursor=None):
        conn = graphene_info.context.instance.get_records_for_run(self.run_id, cursor=afterCursor)
        return GrapheneEventConnection(
            events=[
                from_event_record(record.event_log_entry, self._pipeline_run.pipeline_name)
                for record in conn.records
            ],
            cursor=conn.cursor,
            hasMore=conn.has_more,
        )

    def _get_run_record(self, instance):
        if not self._run_record:
            self._run_record = instance.get_run_records(RunsFilter(run_ids=[self.run_id]))[0]
        return self._run_record

    def resolve_startTime(self, graphene_info):
        run_record = self._get_run_record(graphene_info.context.instance)
        # If a user has not migrated in 0.13.15, then run_record will not have start_time and end_time. So it will be necessary to fill this data using the run_stats. Since we potentially make this call multiple times, we cache the result.
        if run_record.start_time is None and self._pipeline_run.status in STARTED_STATUSES:
            # Short-circuit if pipeline failed to start, so it has an end time but no start time
            if run_record.end_time is not None:
                return run_record.end_time

            if self._run_stats is None or self._run_stats.start_time is None:
                self._run_stats = graphene_info.context.instance.get_run_stats(self.runId)

            if self._run_stats.start_time is None and self._run_stats.end_time:
                return self._run_stats.end_time

            return self._run_stats.start_time
        return run_record.start_time

    def resolve_endTime(self, graphene_info):
        run_record = self._get_run_record(graphene_info.context.instance)
        if run_record.end_time is None and self._pipeline_run.status in COMPLETED_STATUSES:
            if self._run_stats is None or self._run_stats.end_time is None:
                self._run_stats = graphene_info.context.instance.get_run_stats(self.runId)
            return self._run_stats.end_time
        return run_record.end_time

    def resolve_updateTime(self, graphene_info):
        run_record = self._get_run_record(graphene_info.context.instance)
        return datetime_as_float(run_record.update_timestamp)


class GrapheneIPipelineSnapshotMixin:
    # Mixin this class to implement IPipelineSnapshot
    #
    # Graphene has some strange properties that make it so that you cannot
    # implement ABCs nor use properties in an overridable way. So the way
    # the mixin works is that the target classes have to have a method
    # get_represented_pipeline()
    #
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    id = graphene.NonNull(graphene.ID)
    pipeline_snapshot_id = graphene.NonNull(graphene.String)
    dagster_types = non_null_list(GrapheneDagsterType)
    dagster_type_or_error = graphene.Field(
        graphene.NonNull(GrapheneDagsterTypeOrError),
        dagsterTypeName=graphene.Argument(graphene.NonNull(graphene.String)),
    )
    solids = non_null_list(GrapheneSolid)
    modes = non_null_list(GrapheneMode)
    solid_handles = graphene.Field(
        non_null_list(GrapheneSolidHandle), parentHandleID=graphene.String()
    )
    solid_handle = graphene.Field(
        GrapheneSolidHandle,
        handleID=graphene.Argument(graphene.NonNull(graphene.String)),
    )
    tags = non_null_list(GraphenePipelineTag)
    metadata_entries = non_null_list(GrapheneMetadataEntry)
    runs = graphene.Field(
        non_null_list(GrapheneRun),
        cursor=graphene.String(),
        limit=graphene.Int(),
    )
    schedules = non_null_list(GrapheneSchedule)
    sensors = non_null_list(GrapheneSensor)
    parent_snapshot_id = graphene.String()
    graph_name = graphene.NonNull(graphene.String)

    class Meta:
        name = "IPipelineSnapshotMixin"

    def get_represented_pipeline(self):
        raise NotImplementedError()

    def resolve_pipeline_snapshot_id(self, _graphene_info):
        return self.get_represented_pipeline().identifying_pipeline_snapshot_id

    def resolve_id(self, _graphene_info):
        return self.get_represented_pipeline().identifying_pipeline_snapshot_id

    def resolve_name(self, _graphene_info):
        return self.get_represented_pipeline().name

    def resolve_description(self, _graphene_info):
        return self.get_represented_pipeline().description

    def resolve_dagster_types(self, _graphene_info):
        represented_pipeline = self.get_represented_pipeline()
        return sorted(
            list(
                map(
                    lambda dt: to_dagster_type(represented_pipeline.pipeline_snapshot, dt.key),
                    [t for t in represented_pipeline.dagster_type_snaps if t.name],
                )
            ),
            key=lambda dagster_type: dagster_type.name,
        )

    @capture_error
    def resolve_dagster_type_or_error(self, _graphene_info, **kwargs):
        type_name = kwargs["dagsterTypeName"]

        represented_pipeline = self.get_represented_pipeline()

        if not represented_pipeline.has_dagster_type_named(type_name):
            raise UserFacingGraphQLError(
                GrapheneDagsterTypeNotFoundError(dagster_type_name=type_name)
            )

        return to_dagster_type(
            represented_pipeline.pipeline_snapshot,
            represented_pipeline.get_dagster_type_by_name(type_name).key,
        )

    def resolve_solids(self, _graphene_info):
        represented_pipeline = self.get_represented_pipeline()
        return build_solids(
            represented_pipeline,
            represented_pipeline.dep_structure_index,
        )

    def resolve_modes(self, _graphene_info):
        represented_pipeline = self.get_represented_pipeline()
        return [
            GrapheneMode(
                represented_pipeline.config_schema_snapshot,
                represented_pipeline.identifying_pipeline_snapshot_id,
                mode_def_snap,
            )
            for mode_def_snap in sorted(
                represented_pipeline.mode_def_snaps, key=lambda item: item.name
            )
        ]

    def resolve_solid_handle(self, _graphene_info, handleID):
        return build_solid_handles(self.get_represented_pipeline()).get(handleID)

    def resolve_solid_handles(self, _graphene_info, **kwargs):
        handles = build_solid_handles(self.get_represented_pipeline())
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

    def resolve_tags(self, _graphene_info):
        represented_pipeline = self.get_represented_pipeline()
        return [
            GraphenePipelineTag(key=key, value=value)
            for key, value in represented_pipeline.pipeline_snapshot.tags.items()
        ]

    def resolve_metadata_entries(self, _graphene_info) -> List[GrapheneMetadataEntry]:
        represented_pipeline = self.get_represented_pipeline()
        return list(iterate_metadata_entries(represented_pipeline.pipeline_snapshot.metadata))

    def resolve_solidSelection(self, _graphene_info):
        return self.get_represented_pipeline().solid_selection

    def resolve_runs(self, graphene_info, **kwargs):
        pipeline = self.get_represented_pipeline()
        if isinstance(pipeline, ExternalPipeline):
            runs_filter = RunsFilter(
                pipeline_name=pipeline.name,
                tags={
                    REPOSITORY_LABEL_TAG: pipeline.get_external_origin().external_repository_origin.get_label()
                },
            )
        else:
            runs_filter = RunsFilter(pipeline_name=pipeline.name)
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

    def resolve_graph_name(self, _graphene_info):
        return self.get_represented_pipeline().get_graph_name()


class GrapheneIPipelineSnapshot(graphene.Interface):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    pipeline_snapshot_id = graphene.NonNull(graphene.String)
    dagster_types = non_null_list(GrapheneDagsterType)
    dagster_type_or_error = graphene.Field(
        graphene.NonNull(GrapheneDagsterTypeOrError),
        dagsterTypeName=graphene.Argument(graphene.NonNull(graphene.String)),
    )
    solids = non_null_list(GrapheneSolid)
    modes = non_null_list(GrapheneMode)
    solid_handles = graphene.Field(
        non_null_list(GrapheneSolidHandle), parentHandleID=graphene.String()
    )
    solid_handle = graphene.Field(
        GrapheneSolidHandle,
        handleID=graphene.Argument(graphene.NonNull(graphene.String)),
    )
    tags = non_null_list(GraphenePipelineTag)
    metadata_entries = non_null_list(GrapheneMetadataEntry)
    runs = graphene.Field(
        non_null_list(GrapheneRun),
        cursor=graphene.String(),
        limit=graphene.Int(),
    )
    schedules = non_null_list(GrapheneSchedule)
    sensors = non_null_list(GrapheneSensor)
    parent_snapshot_id = graphene.String()
    graph_name = graphene.NonNull(graphene.String)

    class Meta:
        name = "IPipelineSnapshot"


class GraphenePipelinePreset(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    solidSelection = graphene.List(graphene.NonNull(graphene.String))
    runConfigYaml = graphene.NonNull(graphene.String)
    mode = graphene.NonNull(graphene.String)
    tags = non_null_list(GraphenePipelineTag)

    class Meta:
        name = "PipelinePreset"

    def __init__(self, active_preset_data, pipeline_name):
        super().__init__()
        self._active_preset_data = check.inst_param(
            active_preset_data, "active_preset_data", ExternalPresetData
        )
        self._pipeline_name = check.str_param(pipeline_name, "pipeline_name")

    def resolve_name(self, _graphene_info):
        return self._active_preset_data.name

    def resolve_solidSelection(self, _graphene_info):
        return self._active_preset_data.solid_selection

    def resolve_runConfigYaml(self, _graphene_info):
        return dump_run_config_yaml(self._active_preset_data.run_config) or ""

    def resolve_mode(self, _graphene_info):
        return self._active_preset_data.mode

    def resolve_tags(self, _graphene_info):
        return [
            GraphenePipelineTag(key=key, value=value)
            for key, value in self._active_preset_data.tags.items()
            if get_tag_type(key) != TagType.HIDDEN
        ]


class GraphenePipeline(GrapheneIPipelineSnapshotMixin, graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    presets = non_null_list(GraphenePipelinePreset)
    isJob = graphene.NonNull(graphene.Boolean)
    isAssetJob = graphene.NonNull(graphene.Boolean)
    repository = graphene.NonNull("dagster_graphql.schema.external.GrapheneRepository")

    class Meta:
        interfaces = (GrapheneSolidContainer, GrapheneIPipelineSnapshot)
        name = "Pipeline"

    def __init__(self, external_pipeline, batch_loader=None):
        super().__init__()
        self._external_pipeline = check.inst_param(
            external_pipeline, "external_pipeline", ExternalPipeline
        )
        # optional run loader, provided by a parent GrapheneRepository object that instantiates
        # multiple pipelines
        self._batch_loader = check.opt_inst_param(
            batch_loader, "batch_loader", RepositoryScopedBatchLoader
        )

    def resolve_id(self, _graphene_info):
        return self._external_pipeline.get_external_origin_id()

    def get_represented_pipeline(self):
        return self._external_pipeline

    def resolve_presets(self, _graphene_info):
        return [
            GraphenePipelinePreset(preset, self._external_pipeline.name)
            for preset in sorted(self._external_pipeline.active_presets, key=lambda item: item.name)
        ]

    def resolve_isJob(self, _graphene_info):
        return self._external_pipeline.is_job

    def resolve_isAssetJob(self, graphene_info):
        handle = self._external_pipeline.repository_handle
        location = graphene_info.context.get_repository_location(handle.location_name)
        repository = location.get_repository(handle.repository_name)
        return bool(repository.get_external_asset_nodes(self._external_pipeline.name))

    def resolve_repository(self, graphene_info):
        from ..external import GrapheneRepository

        handle = self._external_pipeline.repository_handle
        location = graphene_info.context.get_repository_location(handle.location_name)
        return GrapheneRepository(
            graphene_info.context.instance,
            location.get_repository(handle.repository_name),
            location,
        )

    def resolve_runs(self, graphene_info, **kwargs):
        # override the implementation to use the batch run loader
        if not kwargs.get("cursor") and kwargs.get("limit") and self._batch_loader:
            records = self._batch_loader.get_run_records_for_job(
                self._external_pipeline.name, kwargs.get("limit")
            )
            return [GrapheneRun(record) for record in records]

        # otherwise, fall back to the default implementation
        return super().resolve_runs(graphene_info, **kwargs)


class GrapheneJob(GraphenePipeline):
    class Meta:
        interfaces = (GrapheneSolidContainer, GrapheneIPipelineSnapshot)
        name = "Job"

    # doesn't inherit from base class
    def __init__(self, external_pipeline, batch_loader=None):
        super().__init__()
        self._external_pipeline = check.inst_param(
            external_pipeline, "external_pipeline", ExternalPipeline
        )
        # optional run loader, provided by a parent GrapheneRepository object that instantiates
        # multiple pipelines
        self._batch_loader = check.opt_inst_param(
            batch_loader, "batch_loader", RepositoryScopedBatchLoader
        )


class GrapheneGraph(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneSolidContainer,)
        name = "Graph"

    id = graphene.NonNull(graphene.ID)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    solid_handle = graphene.Field(
        GrapheneSolidHandle,
        handleID=graphene.Argument(graphene.NonNull(graphene.String)),
    )
    solid_handles = graphene.Field(
        non_null_list(GrapheneSolidHandle), parentHandleID=graphene.String()
    )
    modes = non_null_list(GrapheneMode)

    def __init__(self, external_pipeline, solid_handle_id=None):
        self._external_pipeline = check.inst_param(
            external_pipeline, "external_pipeline", ExternalPipeline
        )
        self._solid_handle_id = check.opt_str_param(solid_handle_id, "solid_handle_id")
        super().__init__()

    def resolve_id(self, _graphene_info):
        if self._solid_handle_id:
            return (
                f"{self._external_pipeline.get_external_origin_id()}:solid:{self._solid_handle_id}"
            )
        return f"graph:{self._external_pipeline.get_external_origin_id()}"

    def resolve_name(self, _graphene_info):
        return self._external_pipeline.get_graph_name()

    def resolve_description(self, _graphene_info):
        return self._external_pipeline.description

    def resolve_solid_handle(self, _graphene_info, handleID):
        return build_solid_handles(self._external_pipeline).get(handleID)

    def resolve_solid_handles(self, _graphene_info, **kwargs):
        handles = build_solid_handles(self._external_pipeline)
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

    def resolve_modes(self, _graphene_info):
        # returns empty list... graphs don't have modes, this is a vestige of the old
        # pipeline explorer, which expected all solid containers to be pipelines
        return []


class GrapheneRunOrError(graphene.Union):
    class Meta:
        types = (GrapheneRun, GrapheneRunNotFoundError, GraphenePythonError)
        name = "RunOrError"
