import graphene
import yaml
from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.events import StepMaterializationData
from dagster.core.events.log import EventLogEntry
from dagster.core.host_representation.external import ExternalExecutionPlan, ExternalPipeline
from dagster.core.host_representation.external_data import ExternalPresetData
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from dagster.core.storage.tags import TagType, get_tag_type

from ...implementation.events import construct_basic_params, from_event_record
from ...implementation.fetch_assets import get_assets_for_run_id
from ...implementation.fetch_pipelines import get_pipeline_reference_or_raise
from ...implementation.fetch_runs import get_run_by_id, get_runs, get_stats, get_step_stats
from ...implementation.fetch_schedules import get_schedules_for_pipeline
from ...implementation.fetch_sensors import get_sensors_for_pipeline
from ...implementation.utils import UserFacingGraphQLError, capture_error
from ..asset_key import GrapheneAssetKey
from ..dagster_types import GrapheneDagsterType, GrapheneDagsterTypeOrError, to_dagster_type
from ..errors import GrapheneDagsterTypeNotFoundError, GraphenePythonError, GrapheneRunNotFoundError
from ..execution import GrapheneExecutionPlan
from ..inputs import GrapheneAssetKeyInput
from ..logs.compute_logs import GrapheneComputeLogs
from ..logs.events import (
    GrapheneDagsterRunEvent,
    GrapheneRunStepStats,
    GrapheneStepMaterializationEvent,
)
from ..paging import GrapheneCursor
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
from ..tags import GrapheneAssetTag, GraphenePipelineTag
from ..util import non_null_list
from .mode import GrapheneMode
from .pipeline_ref import GraphenePipelineReference
from .pipeline_run_stats import GrapheneRunStatsSnapshotOrError
from .status import GrapheneRunStatus


class GrapheneAssetMaterialization(graphene.ObjectType):
    materializationEvent = graphene.NonNull(GrapheneStepMaterializationEvent)
    runOrError = graphene.NonNull(lambda: GrapheneRunOrError)
    partition = graphene.Field(graphene.String)

    class Meta:
        name = "AssetMaterialization"

    def __init__(self, event):
        super().__init__()
        self._event = check.inst_param(event, "event", EventLogEntry)
        check.invariant(
            isinstance(event.dagster_event.step_materialization_data, StepMaterializationData)
        )

    def resolve_materializationEvent(self, _graphene_info):
        return GrapheneStepMaterializationEvent(
            materialization=self._event.dagster_event.step_materialization_data.materialization,
            assetLineage=self._event.dagster_event.step_materialization_data.asset_lineage,
            **construct_basic_params(self._event),
        )

    def resolve_runOrError(self, graphene_info):
        return get_run_by_id(graphene_info, self._event.run_id)

    def resolve_partition(self, _graphene_info):
        return self._event.dagster_event.step_materialization_data.materialization.partition


class GrapheneAsset(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    key = graphene.NonNull(GrapheneAssetKey)
    assetMaterializations = graphene.Field(
        non_null_list(GrapheneAssetMaterialization),
        partitions=graphene.List(graphene.String),
        beforeTimestampMillis=graphene.String(),
        limit=graphene.Int(),
    )
    tags = non_null_list(GrapheneAssetTag)
    definition = graphene.Field("dagster_graphql.schema.asset_graph.GrapheneAssetNode")

    class Meta:
        name = "Asset"

    def __init__(self, key, definition=None, tags=None):
        super().__init__(key=key, definition=definition)
        check.opt_dict_param(tags, "tags", key_type=str, value_type=str)
        self._tags = tags

    def resolve_id(self, _):
        return self.key

    def resolve_assetMaterializations(self, graphene_info, **kwargs):
        from ...implementation.fetch_assets import get_asset_events

        try:
            before_timestamp = (
                int(kwargs.get("beforeTimestampMillis")) / 1000.0
                if kwargs.get("beforeTimestampMillis")
                else None
            )
        except ValueError:
            before_timestamp = None

        return [
            GrapheneAssetMaterialization(event=event)
            for event in get_asset_events(
                graphene_info,
                self.key,
                kwargs.get("partitions"),
                before_timestamp=before_timestamp,
                limit=kwargs.get("limit"),
            )
        ]

    def resolve_tags(self, graphene_info):
        if self._tags is not None:
            tags = self._tags
        else:
            tags = graphene_info.context.instance.get_asset_tags(self.key)
        return [GrapheneAssetTag(key=key, value=value) for key, value in tags.items()]


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
    events = graphene.Field(
        non_null_list(GrapheneDagsterRunEvent),
        after=graphene.Argument(GrapheneCursor),
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
    assets = non_null_list(GrapheneAsset)
    events = graphene.Field(
        non_null_list(GrapheneDagsterRunEvent),
        after=graphene.Argument(GrapheneCursor),
    )

    class Meta:
        interfaces = (GraphenePipelineRun,)
        name = "Run"

    def __init__(self, pipeline_run):
        super().__init__(
            runId=pipeline_run.run_id,
            status=PipelineRunStatus(pipeline_run.status),
            mode=pipeline_run.mode,
        )
        self._pipeline_run = check.inst_param(pipeline_run, "pipeline_run", PipelineRun)

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

    def resolve_executionPlan(self, graphene_info):
        if not (
            self._pipeline_run.execution_plan_snapshot_id
            and self._pipeline_run.pipeline_snapshot_id
        ):
            return None

        instance = graphene_info.context.instance
        historical_pipeline = instance.get_historical_pipeline(
            self._pipeline_run.pipeline_snapshot_id
        )
        execution_plan_snapshot = instance.get_execution_plan_snapshot(
            self._pipeline_run.execution_plan_snapshot_id
        )
        return (
            GrapheneExecutionPlan(
                ExternalExecutionPlan(
                    execution_plan_snapshot=execution_plan_snapshot,
                    represented_pipeline=historical_pipeline,
                )
            )
            if execution_plan_snapshot and historical_pipeline
            else None
        )

    def resolve_stepKeysToExecute(self, _graphene_info):
        return self._pipeline_run.step_keys_to_execute

    def resolve_runConfigYaml(self, _graphene_info):
        return yaml.dump(
            self._pipeline_run.run_config, default_flow_style=False, allow_unicode=True
        )

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

    def resolve_canTerminate(self, graphene_info):
        # short circuit if the pipeline run is in a terminal state
        if self._pipeline_run.is_finished:
            return False
        return graphene_info.context.instance.run_coordinator.can_cancel_run(self.run_id)

    def resolve_assets(self, graphene_info):
        return get_assets_for_run_id(graphene_info, self.run_id)

    def resolve_events(self, graphene_info, after=-1):
        events = graphene_info.context.instance.logs_after(self.run_id, cursor=after)
        return [from_event_record(event, self._pipeline_run.pipeline_name) for event in events]


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
        yaml_str = yaml.safe_dump(
            self._active_preset_data.run_config, default_flow_style=False, allow_unicode=True
        )
        return yaml_str if yaml_str else ""

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
    assetNodes = graphene.Field(
        non_null_list("dagster_graphql.schema.asset_graph.GrapheneAssetNode"),
        assetKeys=graphene.Argument(graphene.List(graphene.NonNull(GrapheneAssetKeyInput))),
    )

    class Meta:
        interfaces = (GrapheneSolidContainer, GrapheneIPipelineSnapshot)
        name = "Pipeline"

    def __init__(self, external_pipeline):
        super().__init__()
        self._external_pipeline = check.inst_param(
            external_pipeline, "external_pipeline", ExternalPipeline
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
        return GrapheneRepository(location.get_repository(handle.repository_name), location)

    def resolve_assetNodes(self, graphene_info, **kwargs):
        from ..asset_graph import GrapheneAssetNode

        handle = self._external_pipeline.repository_handle
        location = graphene_info.context.get_repository_location(handle.location_name)
        repository = location.get_repository(handle.repository_name)
        asset_nodes = repository.get_external_asset_nodes(self._external_pipeline.name)

        asset_keys = set(
            AssetKey.from_graphql_input(asset_key) for asset_key in kwargs.get("assetKeys", [])
        )
        return [
            GrapheneAssetNode(repository, asset_node)
            for asset_node in asset_nodes or []
            if not asset_keys or asset_node.asset_key in asset_keys
        ]


class GrapheneJob(GraphenePipeline):
    class Meta:
        interfaces = (GrapheneSolidContainer, GrapheneIPipelineSnapshot)
        name = "Job"


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


class GrapheneInProgressRunsByStep(graphene.ObjectType):
    stepKey = graphene.NonNull(graphene.String)
    unstartedRuns = non_null_list(GrapheneRun)
    inProgressRuns = non_null_list(GrapheneRun)

    class Meta:
        name = "InProgressRunsByStep"
