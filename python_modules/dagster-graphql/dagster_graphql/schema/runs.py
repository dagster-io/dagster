import logging

import yaml
from dagster import PipelineRun, check, seven
from dagster.core.definitions.events import (
    EventMetadataEntry,
    FloatMetadataEntryData,
    IntMetadataEntryData,
    JsonMetadataEntryData,
    MarkdownMetadataEntryData,
    PathMetadataEntryData,
    PythonArtifactMetadataEntryData,
    TextMetadataEntryData,
    UrlMetadataEntryData,
)
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.core.execution.plan.objects import StepFailureData
from dagster.core.execution.stats import RunStepKeyStatsSnapshot, StepEventStatus
from dagster.core.host_representation import ExternalExecutionPlan
from dagster.core.storage.compute_log_manager import ComputeIOType, ComputeLogFileData
from dagster.core.storage.pipeline_run import PipelineRunStatsSnapshot, PipelineRunStatus
from dagster.core.storage.tags import TagType, get_tag_type
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_assets import get_assets_for_run_id
from dagster_graphql.implementation.fetch_pipelines import get_pipeline_reference_or_raise
from dagster_graphql.implementation.fetch_runs import get_stats, get_step_stats

DauphinPipelineRunStatus = dauphin.Enum.from_enum(PipelineRunStatus)
DauphinStepEventStatus = dauphin.Enum.from_enum(StepEventStatus)
DauphinTagType = dauphin.Enum.from_enum(TagType)


class DauphinPipelineOrError(dauphin.Union):
    class Meta:
        name = "PipelineOrError"
        types = ("Pipeline", "PipelineNotFoundError", "InvalidSubsetError", "PythonError")


class DauphinPipelineRunStatsSnapshot(dauphin.ObjectType):
    class Meta:
        name = "PipelineRunStatsSnapshot"

    id = dauphin.NonNull(dauphin.String)
    runId = dauphin.NonNull(dauphin.String)
    stepsSucceeded = dauphin.NonNull(dauphin.Int)
    stepsFailed = dauphin.NonNull(dauphin.Int)
    materializations = dauphin.NonNull(dauphin.Int)
    expectations = dauphin.NonNull(dauphin.Int)
    startTime = dauphin.Field(dauphin.Float)
    endTime = dauphin.Field(dauphin.Float)

    def __init__(self, stats):
        super(DauphinPipelineRunStatsSnapshot, self).__init__(
            id="stats-" + stats.run_id,
            runId=stats.run_id,
            stepsSucceeded=stats.steps_succeeded,
            stepsFailed=stats.steps_failed,
            materializations=stats.materializations,
            expectations=stats.expectations,
            startTime=stats.start_time,
            endTime=stats.end_time,
        )
        self._stats = check.inst_param(stats, "stats", PipelineRunStatsSnapshot)


class DauphinPipelineRunStatsOrError(dauphin.Union):
    class Meta:
        name = "PipelineRunStatsOrError"
        types = ("PipelineRunStatsSnapshot", "PythonError")


class DauphinPipelineRunStepStats(dauphin.ObjectType):
    class Meta:
        name = "PipelineRunStepStats"

    runId = dauphin.NonNull(dauphin.String)
    stepKey = dauphin.NonNull(dauphin.String)
    status = dauphin.Field("StepEventStatus")
    startTime = dauphin.Field(dauphin.Float)
    endTime = dauphin.Field(dauphin.Float)
    materializations = dauphin.non_null_list("Materialization")
    expectationResults = dauphin.non_null_list("ExpectationResult")

    def __init__(self, stats):
        self._stats = check.inst_param(stats, "stats", RunStepKeyStatsSnapshot)
        super(DauphinPipelineRunStepStats, self).__init__(
            runId=stats.run_id,
            stepKey=stats.step_key,
            status=stats.status,
            startTime=stats.start_time,
            endTime=stats.end_time,
            materializations=stats.materializations,
            expectationResults=stats.expectation_results,
        )


class DauphinPipelineRun(dauphin.ObjectType):
    class Meta:
        name = "PipelineRun"

    id = dauphin.NonNull(dauphin.ID)
    runId = dauphin.NonNull(dauphin.String)
    # Nullable because of historical runs
    pipelineSnapshotId = dauphin.String()
    repositoryOrigin = dauphin.Field("RepositoryOrigin")
    status = dauphin.NonNull("PipelineRunStatus")
    pipeline = dauphin.NonNull("PipelineReference")
    pipelineName = dauphin.NonNull(dauphin.String)
    solidSelection = dauphin.List(dauphin.NonNull(dauphin.String))
    stats = dauphin.NonNull("PipelineRunStatsOrError")
    stepStats = dauphin.non_null_list("PipelineRunStepStats")
    computeLogs = dauphin.Field(
        dauphin.NonNull("ComputeLogs"),
        stepKey=dauphin.Argument(dauphin.NonNull(dauphin.String)),
        description="""
        Compute logs are the stdout/stderr logs for a given solid step computation
        """,
    )
    executionPlan = dauphin.Field("ExecutionPlan")
    stepKeysToExecute = dauphin.List(dauphin.NonNull(dauphin.String))
    runConfigYaml = dauphin.NonNull(dauphin.String)
    mode = dauphin.NonNull(dauphin.String)
    tags = dauphin.non_null_list("PipelineTag")
    rootRunId = dauphin.Field(dauphin.String)
    parentRunId = dauphin.Field(dauphin.String)
    canTerminate = dauphin.NonNull(dauphin.Boolean)
    assets = dauphin.non_null_list("Asset")

    def __init__(self, pipeline_run):
        super(DauphinPipelineRun, self).__init__(
            runId=pipeline_run.run_id, status=pipeline_run.status, mode=pipeline_run.mode
        )
        self._pipeline_run = check.inst_param(pipeline_run, "pipeline_run", PipelineRun)

    def resolve_id(self, _):
        return self._pipeline_run.run_id

    def resolve_repositoryOrigin(self, graphene_info):
        return (
            graphene_info.schema.type_named("RepositoryOrigin")(
                self._pipeline_run.external_pipeline_origin.external_repository_origin
            )
            if self._pipeline_run.external_pipeline_origin
            else None
        )

    def resolve_pipeline(self, graphene_info):
        return get_pipeline_reference_or_raise(graphene_info, self._pipeline_run)

    def resolve_pipelineName(self, _graphene_info):
        return self._pipeline_run.pipeline_name

    def resolve_solidSelection(self, _graphene_info):
        return self._pipeline_run.solid_selection

    def resolve_pipelineSnapshotId(self, _):
        return self._pipeline_run.pipeline_snapshot_id

    def resolve_stats(self, graphene_info):
        return get_stats(graphene_info, self.run_id)

    def resolve_stepStats(self, graphene_info):
        return get_step_stats(graphene_info, self.run_id)

    def resolve_computeLogs(self, graphene_info, stepKey):
        return graphene_info.schema.type_named("ComputeLogs")(runId=self.run_id, stepKey=stepKey)

    def resolve_executionPlan(self, graphene_info):
        if not (
            self._pipeline_run.execution_plan_snapshot_id
            and self._pipeline_run.pipeline_snapshot_id
        ):
            return None

        from .execution import DauphinExecutionPlan

        instance = graphene_info.context.instance
        historical_pipeline = instance.get_historical_pipeline(
            self._pipeline_run.pipeline_snapshot_id
        )
        execution_plan_snapshot = instance.get_execution_plan_snapshot(
            self._pipeline_run.execution_plan_snapshot_id
        )
        return (
            DauphinExecutionPlan(
                ExternalExecutionPlan(
                    execution_plan_snapshot=execution_plan_snapshot,
                    represented_pipeline=historical_pipeline,
                )
            )
            if execution_plan_snapshot and historical_pipeline
            else None
        )

    def resolve_stepKeysToExecute(self, _):
        return self._pipeline_run.step_keys_to_execute

    def resolve_runConfigYaml(self, _graphene_info):
        return yaml.dump(
            self._pipeline_run.run_config, default_flow_style=False, allow_unicode=True
        )

    def resolve_tags(self, graphene_info):
        return [
            graphene_info.schema.type_named("PipelineTag")(key=key, value=value)
            for key, value in self._pipeline_run.tags.items()
            if get_tag_type(key) != TagType.HIDDEN
        ]

    def resolve_rootRunId(self, _):
        return self._pipeline_run.root_run_id

    def resolve_parentRunId(self, _):
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


class DauphinRunGroup(dauphin.ObjectType):
    class Meta:
        name = "RunGroup"

    rootRunId = dauphin.NonNull(dauphin.String)
    runs = dauphin.List(DauphinPipelineRun)

    def __init__(self, root_run_id, runs):
        check.str_param(root_run_id, "root_run_id")
        check.list_param(runs, "runs", DauphinPipelineRun)

        super(DauphinRunGroup, self).__init__(rootRunId=root_run_id, runs=runs)


class DauphinLogLevel(dauphin.Enum):
    class Meta:
        name = "LogLevel"

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    INFO = "INFO"
    WARNING = "WARNING"
    DEBUG = "DEBUG"

    @classmethod
    def from_level(cls, level):
        check.int_param(level, "level")
        if level == logging.CRITICAL:
            return DauphinLogLevel.CRITICAL
        elif level == logging.ERROR:
            return DauphinLogLevel.ERROR
        elif level == logging.INFO:
            return DauphinLogLevel.INFO
        elif level == logging.WARNING:
            return DauphinLogLevel.WARNING
        elif level == logging.DEBUG:
            return DauphinLogLevel.DEBUG
        else:
            check.failed("Invalid log level: {level}".format(level=level))


class DauphinComputeLogs(dauphin.ObjectType):
    class Meta:
        name = "ComputeLogs"

    runId = dauphin.NonNull(dauphin.String)
    stepKey = dauphin.NonNull(dauphin.String)
    stdout = dauphin.Field("ComputeLogFile")
    stderr = dauphin.Field("ComputeLogFile")

    def _resolve_compute_log(self, graphene_info, io_type):
        return graphene_info.context.instance.compute_log_manager.read_logs_file(
            self.runId, self.stepKey, io_type, 0
        )

    def resolve_stdout(self, graphene_info):
        return self._resolve_compute_log(graphene_info, ComputeIOType.STDOUT)

    def resolve_stderr(self, graphene_info):
        return self._resolve_compute_log(graphene_info, ComputeIOType.STDERR)


class DauphinComputeLogFile(dauphin.ObjectType):
    class Meta:
        name = "ComputeLogFile"

    path = dauphin.NonNull(dauphin.String)
    data = dauphin.Field(
        dauphin.String, description="The data output captured from step computation at query time"
    )
    cursor = dauphin.NonNull(dauphin.Int)
    size = dauphin.NonNull(dauphin.Int)
    download_url = dauphin.Field(dauphin.String)


class DauphinMessageEvent(dauphin.Interface):
    class Meta:
        name = "MessageEvent"

    runId = dauphin.NonNull(dauphin.String)
    message = dauphin.NonNull(dauphin.String)
    timestamp = dauphin.NonNull(dauphin.String)
    level = dauphin.NonNull("LogLevel")
    stepKey = dauphin.Field(dauphin.String)
    solidHandleID = dauphin.Field(dauphin.String)


class DauphinEventMetadataEntry(dauphin.Interface):
    class Meta:
        name = "EventMetadataEntry"

    label = dauphin.NonNull(dauphin.String)
    description = dauphin.String()


class DauphinDisplayableEvent(dauphin.Interface):
    class Meta:
        name = "DisplayableEvent"

    label = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    metadataEntries = dauphin.non_null_list(DauphinEventMetadataEntry)


class DauphinPipelineRunLogsSubscriptionSuccess(dauphin.ObjectType):
    class Meta:
        name = "PipelineRunLogsSubscriptionSuccess"

    run = dauphin.NonNull("PipelineRun")
    messages = dauphin.non_null_list("PipelineRunEvent")


class DauphinPipelineRunLogsSubscriptionFailure(dauphin.ObjectType):
    class Meta:
        name = "PipelineRunLogsSubscriptionFailure"

    message = dauphin.NonNull(dauphin.String)
    missingRunId = dauphin.Field(dauphin.String)


class DauphinPipelineRunLogsSubscriptionPayload(dauphin.Union):
    class Meta:
        name = "PipelineRunLogsSubscriptionPayload"
        types = (
            DauphinPipelineRunLogsSubscriptionSuccess,
            DauphinPipelineRunLogsSubscriptionFailure,
        )


class DauphinMissingRunIdErrorEvent(dauphin.ObjectType):
    class Meta:
        name = "MissingRunIdErrorEvent"

    invalidRunId = dauphin.NonNull(dauphin.String)


class DauphinLogMessageEvent(dauphin.ObjectType):
    class Meta:
        name = "LogMessageEvent"
        interfaces = (DauphinMessageEvent,)


class DauphinPipelineEvent(dauphin.Interface):
    class Meta:
        name = "PipelineEvent"

    pipelineName = dauphin.NonNull(dauphin.String)


class DauphinPipelineEnqueuedEvent(dauphin.ObjectType):
    class Meta:
        name = "PipelineEnqueuedEvent"
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineDequeuedEvent(dauphin.ObjectType):
    class Meta:
        name = "PipelineDequeuedEvent"
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineStartingEvent(dauphin.ObjectType):
    class Meta:
        name = "PipelineStartingEvent"
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineCancelingEvent(dauphin.ObjectType):
    class Meta:
        name = "PipelineCancelingEvent"
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineCanceledEvent(dauphin.ObjectType):
    class Meta:
        name = "PipelineCanceledEvent"
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineStartEvent(dauphin.ObjectType):
    class Meta:
        name = "PipelineStartEvent"
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineSuccessEvent(dauphin.ObjectType):
    class Meta:
        name = "PipelineSuccessEvent"
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineFailureEvent(dauphin.ObjectType):
    class Meta:
        name = "PipelineFailureEvent"
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)

    error = dauphin.Field("PythonError")


class DauphinPipelineInitFailureEvent(dauphin.ObjectType):
    class Meta:
        name = "PipelineInitFailureEvent"
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)

    error = dauphin.NonNull("PythonError")


class DauphinStepEvent(dauphin.Interface):
    class Meta:
        name = "StepEvent"

    stepKey = dauphin.Field(dauphin.String)
    solidHandleID = dauphin.Field(dauphin.String)


class DauphinExecutionStepStartEvent(dauphin.ObjectType):
    class Meta:
        name = "ExecutionStepStartEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)


class DauphinExecutionStepRestartEvent(dauphin.ObjectType):
    class Meta:
        name = "ExecutionStepRestartEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)


class DauphinExecutionStepUpForRetryEvent(dauphin.ObjectType):
    class Meta:
        name = "ExecutionStepUpForRetryEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    error = dauphin.NonNull("PythonError")
    secondsToWait = dauphin.Field(dauphin.Int)


class DauphinExecutionStepSkippedEvent(dauphin.ObjectType):
    class Meta:
        name = "ExecutionStepSkippedEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)


class DauphinEventPathMetadataEntry(dauphin.ObjectType):
    class Meta:
        name = "EventPathMetadataEntry"
        interfaces = (DauphinEventMetadataEntry,)

    path = dauphin.NonNull(dauphin.String)


class DauphinEventJsonMetadataEntry(dauphin.ObjectType):
    class Meta:
        name = "EventJsonMetadataEntry"
        interfaces = (DauphinEventMetadataEntry,)

    jsonString = dauphin.NonNull(dauphin.String)


class DauphinEventTextMetadataEntry(dauphin.ObjectType):
    class Meta:
        name = "EventTextMetadataEntry"
        interfaces = (DauphinEventMetadataEntry,)

    text = dauphin.NonNull(dauphin.String)


class DauphinEventUrlMetadataEntry(dauphin.ObjectType):
    class Meta:
        name = "EventUrlMetadataEntry"
        interfaces = (DauphinEventMetadataEntry,)

    url = dauphin.NonNull(dauphin.String)


class DauphinEventMarkdownMetadataEntry(dauphin.ObjectType):
    class Meta:
        name = "EventMarkdownMetadataEntry"
        interfaces = (DauphinEventMetadataEntry,)

    md_str = dauphin.NonNull(dauphin.String)


class DauphinEventPythonArtifactMetadataEntry(dauphin.ObjectType):
    class Meta:
        name = "EventPythonArtifactMetadataEntry"
        interfaces = (DauphinEventMetadataEntry,)

    module = dauphin.NonNull(dauphin.String)
    name = dauphin.NonNull(dauphin.String)


class DauphinEventFloatMetadataEntry(dauphin.ObjectType):
    class Meta:
        name = "EventFloatMetadataEntry"
        interfaces = (DauphinEventMetadataEntry,)

    floatValue = dauphin.NonNull(dauphin.Float)


class DauphinEventIntMetadataEntry(dauphin.ObjectType):
    class Meta:
        name = "EventIntMetadataEntry"
        interfaces = (DauphinEventMetadataEntry,)

    intValue = dauphin.NonNull(dauphin.Int)


def iterate_metadata_entries(metadata_entries):
    check.list_param(metadata_entries, "metadata_entries", of_type=EventMetadataEntry)
    for metadata_entry in metadata_entries:
        if isinstance(metadata_entry.entry_data, PathMetadataEntryData):
            yield DauphinEventPathMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                path=metadata_entry.entry_data.path,
            )
        elif isinstance(metadata_entry.entry_data, JsonMetadataEntryData):
            yield DauphinEventJsonMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                jsonString=seven.json.dumps(metadata_entry.entry_data.data),
            )
        elif isinstance(metadata_entry.entry_data, TextMetadataEntryData):
            yield DauphinEventTextMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                text=metadata_entry.entry_data.text,
            )
        elif isinstance(metadata_entry.entry_data, UrlMetadataEntryData):
            yield DauphinEventUrlMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                url=metadata_entry.entry_data.url,
            )
        elif isinstance(metadata_entry.entry_data, MarkdownMetadataEntryData):
            yield DauphinEventMarkdownMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                md_str=metadata_entry.entry_data.md_str,
            )
        elif isinstance(metadata_entry.entry_data, PythonArtifactMetadataEntryData):
            yield DauphinEventPythonArtifactMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                module=metadata_entry.entry_data.module,
                name=metadata_entry.entry_data.name,
            )
        elif isinstance(metadata_entry.entry_data, FloatMetadataEntryData):
            yield DauphinEventFloatMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                floatValue=metadata_entry.entry_data.value,
            )
        elif isinstance(metadata_entry.entry_data, IntMetadataEntryData):
            yield DauphinEventIntMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                intValue=metadata_entry.entry_data.value,
            )
        else:
            # skip rest for now
            check.not_implemented(
                "{} unsupported metadata entry for now".format(type(metadata_entry.entry_data))
            )


def _to_dauphin_metadata_entries(metadata_entries):
    return list(iterate_metadata_entries(metadata_entries) or [])


class DauphinObjectStoreOperationType(dauphin.Enum):
    class Meta:
        name = "ObjectStoreOperationType"

    SET_OBJECT = "SET_OBJECT"
    GET_OBJECT = "GET_OBJECT"
    RM_OBJECT = "RM_OBJECT"
    CP_OBJECT = "CP_OBJECT"


class DauphinObjectStoreOperationResult(dauphin.ObjectType):
    class Meta:
        name = "ObjectStoreOperationResult"
        interfaces = (DauphinDisplayableEvent,)

    op = dauphin.NonNull("ObjectStoreOperationType")

    def resolve_metadataEntries(self, _graphene_info):
        return _to_dauphin_metadata_entries(self.metadata_entries)  # pylint: disable=no-member


class DauphinMaterialization(dauphin.ObjectType):
    class Meta:
        name = "Materialization"
        interfaces = (DauphinDisplayableEvent,)

    assetKey = dauphin.Field("AssetKey")

    def resolve_metadataEntries(self, _graphene_info):
        return _to_dauphin_metadata_entries(self.metadata_entries)  # pylint: disable=no-member

    def resolve_assetKey(self, graphene_info):
        asset_key = self.asset_key  # pylint: disable=no-member

        if not asset_key:
            return None

        return graphene_info.schema.type_named("AssetKey")(path=asset_key.path)


class DauphinExpectationResult(dauphin.ObjectType):
    class Meta:
        name = "ExpectationResult"
        interfaces = (DauphinDisplayableEvent,)

    success = dauphin.NonNull(dauphin.Boolean)

    def resolve_metadataEntries(self, _graphene_info):
        return _to_dauphin_metadata_entries(self.metadata_entries)  # pylint: disable=no-member


class DauphinTypeCheck(dauphin.ObjectType):
    class Meta:
        name = "TypeCheck"
        interfaces = (DauphinDisplayableEvent,)

    success = dauphin.NonNull(dauphin.Boolean)

    def resolve_metadataEntries(self, _graphene_info):
        return _to_dauphin_metadata_entries(self.metadata_entries)  # pylint: disable=no-member


class DauphinFailureMetadata(dauphin.ObjectType):
    class Meta:
        name = "FailureMetadata"
        interfaces = (DauphinDisplayableEvent,)

    def resolve_metadataEntries(self, _graphene_info):
        return _to_dauphin_metadata_entries(self.metadata_entries)  # pylint: disable=no-member


class DauphinExecutionStepInputEvent(dauphin.ObjectType):
    class Meta:
        name = "ExecutionStepInputEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    input_name = dauphin.NonNull(dauphin.String)
    type_check = dauphin.NonNull(DauphinTypeCheck)


class DauphinExecutionStepOutputEvent(dauphin.ObjectType):
    class Meta:
        name = "ExecutionStepOutputEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    output_name = dauphin.NonNull(dauphin.String)
    type_check = dauphin.NonNull(DauphinTypeCheck)


class DauphinExecutionStepSuccessEvent(dauphin.ObjectType):
    class Meta:
        name = "ExecutionStepSuccessEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)


class DauphinExecutionStepFailureEvent(dauphin.ObjectType):
    class Meta:
        name = "ExecutionStepFailureEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    error = dauphin.NonNull("PythonError")
    failureMetadata = dauphin.Field("FailureMetadata")


class DauphinHookCompletedEvent(dauphin.ObjectType):
    class Meta:
        name = "HookCompletedEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)


class DauphinHookSkippedEvent(dauphin.ObjectType):
    class Meta:
        name = "HookSkippedEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)


class DauphinHookErroredEvent(dauphin.ObjectType):
    class Meta:
        name = "HookErroredEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    error = dauphin.NonNull("PythonError")


class DauphinStepMaterializationEvent(dauphin.ObjectType):
    class Meta:
        name = "StepMaterializationEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    materialization = dauphin.NonNull(DauphinMaterialization)
    stepStats = dauphin.NonNull("PipelineRunStepStats")

    def resolve_stepStats(self, graphene_info):
        run_id = self.runId  # pylint: disable=no-member
        step_key = self.stepKey  # pylint: disable=no-member
        stats = get_step_stats(graphene_info, run_id, step_keys=[step_key])
        return stats[0]


class DauphinHandledOutputEvent(dauphin.ObjectType):
    class Meta:
        name = "HandledOutputEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    output_name = dauphin.NonNull(dauphin.String)
    manager_key = dauphin.NonNull(dauphin.String)


class DauphinLoadedInputEvent(dauphin.ObjectType):
    class Meta:
        name = "LoadedInputEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    input_name = dauphin.NonNull(dauphin.String)
    manager_key = dauphin.NonNull(dauphin.String)
    upstream_output_name = dauphin.Field(dauphin.String)
    upstream_step_key = dauphin.Field(dauphin.String)


class DauphinObjectStoreOperationEvent(dauphin.ObjectType):
    class Meta:
        name = "ObjectStoreOperationEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    operation_result = dauphin.NonNull(DauphinObjectStoreOperationResult)


class DauphinEngineEvent(dauphin.ObjectType):
    class Meta:
        name = "EngineEvent"
        interfaces = (DauphinMessageEvent, DauphinDisplayableEvent, DauphinStepEvent)

    error = dauphin.Field("PythonError")
    marker_start = dauphin.Field(dauphin.String)
    marker_end = dauphin.Field(dauphin.String)


class DauphinStepExpectationResultEvent(dauphin.ObjectType):
    class Meta:
        name = "StepExpectationResultEvent"
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    expectation_result = dauphin.NonNull(DauphinExpectationResult)


# Should be a union of all possible events
class DauphinPipelineRunEvent(dauphin.Union):
    class Meta:
        name = "PipelineRunEvent"
        types = (
            DauphinExecutionStepFailureEvent,
            DauphinExecutionStepInputEvent,
            DauphinExecutionStepOutputEvent,
            DauphinExecutionStepSkippedEvent,
            DauphinExecutionStepStartEvent,
            DauphinExecutionStepSuccessEvent,
            DauphinExecutionStepUpForRetryEvent,
            DauphinExecutionStepRestartEvent,
            DauphinLogMessageEvent,
            DauphinPipelineFailureEvent,
            DauphinPipelineInitFailureEvent,
            DauphinPipelineStartEvent,
            DauphinPipelineEnqueuedEvent,
            DauphinPipelineDequeuedEvent,
            DauphinPipelineStartingEvent,
            DauphinPipelineCancelingEvent,
            DauphinPipelineCanceledEvent,
            DauphinPipelineSuccessEvent,
            DauphinHandledOutputEvent,
            DauphinLoadedInputEvent,
            DauphinObjectStoreOperationEvent,
            DauphinStepExpectationResultEvent,
            DauphinStepMaterializationEvent,
            DauphinEngineEvent,
            DauphinHookCompletedEvent,
            DauphinHookSkippedEvent,
            DauphinHookErroredEvent,
        )


class DauphinPipelineTag(dauphin.ObjectType):
    class Meta:
        name = "PipelineTag"

    key = dauphin.NonNull(dauphin.String)
    value = dauphin.NonNull(dauphin.String)

    def __init__(self, key, value):
        super(DauphinPipelineTag, self).__init__(key=key, value=value)


def from_dagster_event_record(event_record, pipeline_name):
    # Lots of event types. Pylint thinks there are too many branches
    # pylint: disable=too-many-branches
    check.inst_param(event_record, "event_record", EventRecord)
    check.param_invariant(event_record.is_dagster_event, "event_record")
    check.str_param(pipeline_name, "pipeline_name")

    # circular ref at module scope
    from .errors import DauphinPythonError

    dagster_event = event_record.dagster_event
    basic_params = construct_basic_params(event_record)
    if dagster_event.event_type == DagsterEventType.STEP_START:
        return DauphinExecutionStepStartEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_SKIPPED:
        return DauphinExecutionStepSkippedEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_UP_FOR_RETRY:
        return DauphinExecutionStepUpForRetryEvent(
            error=dagster_event.step_retry_data.error,
            secondsToWait=dagster_event.step_retry_data.seconds_to_wait,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.STEP_RESTARTED:
        return DauphinExecutionStepRestartEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_SUCCESS:
        return DauphinExecutionStepSuccessEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_INPUT:
        input_data = dagster_event.event_specific_data
        return DauphinExecutionStepInputEvent(
            input_name=input_data.input_name, type_check=input_data.type_check_data, **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.STEP_OUTPUT:
        output_data = dagster_event.step_output_data
        return DauphinExecutionStepOutputEvent(
            output_name=output_data.output_name,
            type_check=output_data.type_check_data,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.STEP_MATERIALIZATION:
        materialization = dagster_event.step_materialization_data.materialization
        return DauphinStepMaterializationEvent(materialization=materialization, **basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
        expectation_result = dagster_event.event_specific_data.expectation_result
        return DauphinStepExpectationResultEvent(
            expectation_result=expectation_result, **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.STEP_FAILURE:
        check.inst(dagster_event.step_failure_data, StepFailureData)
        return DauphinExecutionStepFailureEvent(
            error=DauphinPythonError(dagster_event.step_failure_data.error),
            failureMetadata=dagster_event.step_failure_data.user_failure_data,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.PIPELINE_ENQUEUED:
        return DauphinPipelineEnqueuedEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_DEQUEUED:
        return DauphinPipelineDequeuedEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_STARTING:
        return DauphinPipelineStartingEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_CANCELING:
        return DauphinPipelineCancelingEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_CANCELED:
        return DauphinPipelineCanceledEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_START:
        return DauphinPipelineStartEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_SUCCESS:
        return DauphinPipelineSuccessEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_FAILURE:
        return DauphinPipelineFailureEvent(
            pipelineName=pipeline_name,
            error=DauphinPythonError(dagster_event.pipeline_failure_data.error)
            if (dagster_event.pipeline_failure_data and dagster_event.pipeline_failure_data.error)
            else None,
            **basic_params,
        )

    elif dagster_event.event_type == DagsterEventType.PIPELINE_INIT_FAILURE:
        return DauphinPipelineInitFailureEvent(
            pipelineName=pipeline_name,
            error=DauphinPythonError(dagster_event.pipeline_init_failure_data.error),
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.HANDLED_OUTPUT:
        return DauphinHandledOutputEvent(
            output_name=dagster_event.event_specific_data.output_name,
            manager_key=dagster_event.event_specific_data.manager_key,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.LOADED_INPUT:
        return DauphinLoadedInputEvent(
            input_name=dagster_event.event_specific_data.input_name,
            manager_key=dagster_event.event_specific_data.manager_key,
            upstream_output_name=dagster_event.event_specific_data.upstream_output_name,
            upstream_step_key=dagster_event.event_specific_data.upstream_step_key,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.OBJECT_STORE_OPERATION:
        operation_result = dagster_event.event_specific_data
        return DauphinObjectStoreOperationEvent(operation_result=operation_result, **basic_params)
    elif dagster_event.event_type == DagsterEventType.ENGINE_EVENT:
        return DauphinEngineEvent(
            metadataEntries=_to_dauphin_metadata_entries(
                dagster_event.engine_event_data.metadata_entries
            ),
            error=DauphinPythonError(dagster_event.engine_event_data.error)
            if dagster_event.engine_event_data.error
            else None,
            marker_start=dagster_event.engine_event_data.marker_start,
            marker_end=dagster_event.engine_event_data.marker_end,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.HOOK_COMPLETED:
        return DauphinHookCompletedEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.HOOK_SKIPPED:
        return DauphinHookSkippedEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.HOOK_ERRORED:
        return DauphinHookErroredEvent(
            error=DauphinPythonError(dagster_event.hook_errored_data.error), **basic_params
        )
    else:
        raise Exception(
            "Unknown DAGSTER_EVENT type {inner_type} found in logs".format(
                inner_type=dagster_event.event_type
            )
        )


def from_compute_log_file(graphene_info, file):
    check.opt_inst_param(file, "file", ComputeLogFileData)
    if not file:
        return None
    return graphene_info.schema.type_named("ComputeLogFile")(
        path=file.path,
        data=file.data,
        cursor=file.cursor,
        size=file.size,
        download_url=file.download_url,
    )


def from_event_record(event_record, pipeline_name):
    check.inst_param(event_record, "event_record", EventRecord)
    check.str_param(pipeline_name, "pipeline_name")

    if event_record.is_dagster_event:
        return from_dagster_event_record(event_record, pipeline_name)
    else:
        return DauphinLogMessageEvent(**construct_basic_params(event_record))


def construct_basic_params(event_record):
    check.inst_param(event_record, "event_record", EventRecord)
    return {
        "runId": event_record.run_id,
        "message": event_record.dagster_event.message
        if (event_record.dagster_event and event_record.dagster_event.message)
        else event_record.user_message,
        "timestamp": int(event_record.timestamp * 1000),
        "level": DauphinLogLevel.from_level(event_record.level),
        "stepKey": event_record.step_key,
        "solidHandleID": event_record.dagster_event.solid_handle.to_string()
        if event_record.is_dagster_event and event_record.dagster_event.solid_handle
        else None,
    }
