from __future__ import absolute_import

import logging

import yaml
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_pipelines import (
    get_pipeline_def_from_selector,
    get_pipeline_reference_or_raise,
)
from dagster_graphql.implementation.fetch_runs import get_stats

from dagster import RunConfig, check, seven
from dagster.core.definitions.events import (
    EventMetadataEntry,
    JsonMetadataEntryData,
    MarkdownMetadataEntryData,
    PathMetadataEntryData,
    PythonArtifactMetadataEntryData,
    TextMetadataEntryData,
    UrlMetadataEntryData,
)
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.plan.objects import StepFailureData
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.storage.compute_log_manager import ComputeIOType, ComputeLogFileData
from dagster.core.storage.pipeline_run import (
    PipelineRun,
    PipelineRunStatsSnapshot,
    PipelineRunStatus,
)

from .pipelines import DauphinPipeline

DauphinPipelineRunStatus = dauphin.Enum.from_enum(PipelineRunStatus)


class DauphinPipelineOrError(dauphin.Union):
    class Meta(object):
        name = 'PipelineOrError'
        types = ('Pipeline', 'PipelineNotFoundError', 'InvalidSubsetError', 'PythonError')


class DauphinPipelineRunStatsSnapshot(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineRunStatsSnapshot'

    runId = dauphin.NonNull(dauphin.String)
    stepsSucceeded = dauphin.NonNull(dauphin.Int)
    stepsFailed = dauphin.NonNull(dauphin.Int)
    materializations = dauphin.NonNull(dauphin.Int)
    expectations = dauphin.NonNull(dauphin.Int)
    startTime = dauphin.Field(dauphin.Float)
    endTime = dauphin.Field(dauphin.Float)

    def __init__(self, stats):
        super(DauphinPipelineRunStatsSnapshot, self).__init__(
            runId=stats.run_id,
            stepsSucceeded=stats.steps_succeeded,
            stepsFailed=stats.steps_failed,
            materializations=stats.materializations,
            expectations=stats.expectations,
            startTime=stats.start_time,
            endTime=stats.end_time,
        )
        self._stats = check.inst_param(stats, 'stats', PipelineRunStatsSnapshot)


class DauphinPipelineRunStatsOrError(dauphin.Union):
    class Meta(object):
        name = 'PipelineRunStatsOrError'
        types = ('PipelineRunStatsSnapshot', 'PythonError')


class DauphinPipelineRun(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineRun'

    runId = dauphin.NonNull(dauphin.String)
    status = dauphin.NonNull('PipelineRunStatus')
    pipeline = dauphin.NonNull('PipelineReference')
    stats = dauphin.NonNull('PipelineRunStatsOrError')
    logs = dauphin.NonNull('LogMessageConnection')
    computeLogs = dauphin.Field(
        dauphin.NonNull('ComputeLogs'),
        stepKey=dauphin.Argument(dauphin.NonNull(dauphin.String)),
        description='''
        Compute logs are the stdout/stderr logs for a given solid step computation
        ''',
    )
    executionPlan = dauphin.Field('ExecutionPlan')
    stepKeysToExecute = dauphin.List(dauphin.NonNull(dauphin.String))
    environmentConfigYaml = dauphin.NonNull(dauphin.String)
    mode = dauphin.NonNull(dauphin.String)
    tags = dauphin.non_null_list('PipelineTag')
    canCancel = dauphin.NonNull(dauphin.Boolean)
    executionSelection = dauphin.NonNull('ExecutionSelection')

    def __init__(self, pipeline_run):
        super(DauphinPipelineRun, self).__init__(
            runId=pipeline_run.run_id, status=pipeline_run.status, mode=pipeline_run.mode
        )
        self._pipeline_run = check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

    def resolve_pipeline(self, graphene_info):
        return get_pipeline_reference_or_raise(graphene_info, self._pipeline_run.selector)

    def resolve_logs(self, graphene_info):
        return graphene_info.schema.type_named('LogMessageConnection')(self._pipeline_run)

    def resolve_stats(self, graphene_info):
        return get_stats(graphene_info, self.run_id)

    def resolve_computeLogs(self, graphene_info, stepKey):
        return graphene_info.schema.type_named('ComputeLogs')(runId=self.run_id, stepKey=stepKey)

    def resolve_executionPlan(self, graphene_info):
        pipeline = self.resolve_pipeline(graphene_info)
        if isinstance(pipeline, DauphinPipeline):
            execution_plan = create_execution_plan(
                get_pipeline_def_from_selector(graphene_info, self._pipeline_run.selector),
                self._pipeline_run.environment_dict,
                RunConfig(mode=self._pipeline_run.mode),
            )
            return graphene_info.schema.type_named('ExecutionPlan')(pipeline, execution_plan)
        else:
            return None

    def resolve_stepKeysToExecute(self, _):
        return self._pipeline_run.step_keys_to_execute

    def resolve_environmentConfigYaml(self, _graphene_info):
        return yaml.dump(self._pipeline_run.environment_dict, default_flow_style=False)

    def resolve_tags(self, graphene_info):
        return [
            graphene_info.schema.type_named('PipelineTag')(key=key, value=value)
            for key, value in self._pipeline_run.tags.items()
        ]

    @property
    def run_id(self):
        return self.runId

    def resolve_canCancel(self, graphene_info):
        return graphene_info.context.execution_manager.can_terminate(self.run_id)

    def resolve_executionSelection(self, graphene_info):
        return graphene_info.schema.type_named('ExecutionSelection')(self._pipeline_run.selector)


# output version of input type DauphinExecutionSelector
class DauphinExectionSelection(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutionSelection'

    name = dauphin.NonNull(dauphin.String)
    solidSubset = dauphin.List(dauphin.NonNull(dauphin.String))

    def __init__(self, selector):
        check.inst_param(selector, 'selector', ExecutionSelector)
        self.name = selector.name
        self.solidSubset = selector.solid_subset


class DauphinLogLevel(dauphin.Enum):
    class Meta(object):
        name = 'LogLevel'

    CRITICAL = 'CRITICAL'
    ERROR = 'ERROR'
    INFO = 'INFO'
    WARNING = 'WARNING'
    DEBUG = 'DEBUG'

    @classmethod
    def from_level(cls, level):
        check.int_param(level, 'level')
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
            check.failed('Invalid log level: {level}'.format(level=level))


class DauphinComputeLogs(dauphin.ObjectType):
    class Meta(object):
        name = 'ComputeLogs'

    runId = dauphin.NonNull(dauphin.String)
    stepKey = dauphin.NonNull(dauphin.String)
    stdout = dauphin.Field('ComputeLogFile')
    stderr = dauphin.Field('ComputeLogFile')

    def _resolve_compute_log(self, graphene_info, io_type):
        return graphene_info.context.instance.compute_log_manager.read_logs_file(
            self.runId, self.stepKey, io_type, 0
        )

    def resolve_stdout(self, graphene_info):
        return self._resolve_compute_log(graphene_info, ComputeIOType.STDOUT)

    def resolve_stderr(self, graphene_info):
        return self._resolve_compute_log(graphene_info, ComputeIOType.STDERR)


class DauphinComputeLogFile(dauphin.ObjectType):
    class Meta(object):
        name = 'ComputeLogFile'

    path = dauphin.NonNull(dauphin.String)
    data = dauphin.Field(
        dauphin.String, description="The data output captured from step computation at query time"
    )
    cursor = dauphin.NonNull(dauphin.Int)
    size = dauphin.NonNull(dauphin.Int)
    download_url = dauphin.Field(dauphin.String)


class DauphinMessageEvent(dauphin.Interface):
    class Meta(object):
        name = 'MessageEvent'

    runId = dauphin.NonNull(dauphin.String)
    message = dauphin.NonNull(dauphin.String)
    timestamp = dauphin.NonNull(dauphin.String)
    level = dauphin.NonNull('LogLevel')
    step = dauphin.Field('ExecutionStep')


class DauphinEventMetadataEntry(dauphin.Interface):
    class Meta(object):
        name = 'EventMetadataEntry'

    label = dauphin.NonNull(dauphin.String)
    description = dauphin.String()


class DauphinDisplayableEvent(dauphin.Interface):
    class Meta(object):
        name = 'DisplayableEvent'

    label = dauphin.NonNull(dauphin.String)
    description = dauphin.String()
    metadataEntries = dauphin.non_null_list(DauphinEventMetadataEntry)


class DauphinLogMessageConnection(dauphin.ObjectType):
    class Meta(object):
        name = 'LogMessageConnection'

    nodes = dauphin.non_null_list('PipelineRunEvent')
    pageInfo = dauphin.NonNull('PageInfo')

    def __init__(self, pipeline_run):
        self._pipeline_run = check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

    def resolve_nodes(self, graphene_info):

        pipeline = get_pipeline_reference_or_raise(graphene_info, self._pipeline_run.selector)

        if isinstance(pipeline, DauphinPipeline):
            execution_plan = create_execution_plan(
                get_pipeline_def_from_selector(graphene_info, self._pipeline_run.selector),
                self._pipeline_run.environment_dict,
                RunConfig(mode=self._pipeline_run.mode),
            )
        else:
            pipeline = None
            execution_plan = None

        return [
            from_event_record(graphene_info, log, pipeline, execution_plan)
            for log in graphene_info.context.instance.all_logs(self._pipeline_run.run_id)
        ]

    def resolve_pageInfo(self, graphene_info):
        count = len(graphene_info.context.instance.all_logs(self._pipeline_run.run_id))
        lastCursor = None
        if count > 0:
            lastCursor = str(count - 1)
        return graphene_info.schema.type_named('PageInfo')(
            lastCursor=lastCursor,
            hasNextPage=None,
            hasPreviousPage=None,
            count=count,
            totalCount=count,
        )


class DauphinPipelineRunLogsSubscriptionSuccess(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineRunLogsSubscriptionSuccess'

    run = dauphin.NonNull('PipelineRun')
    messages = dauphin.non_null_list('PipelineRunEvent')


class DauphinPipelineRunLogsSubscriptionFailure(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineRunLogsSubscriptionFailure'

    message = dauphin.NonNull(dauphin.String)
    missingRunId = dauphin.Field(dauphin.String)


class DauphinPipelineRunLogsSubscriptionPayload(dauphin.Union):
    class Meta(object):
        name = 'PipelineRunLogsSubscriptionPayload'
        types = (
            DauphinPipelineRunLogsSubscriptionSuccess,
            DauphinPipelineRunLogsSubscriptionFailure,
        )


class DauphinMissingRunIdErrorEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'MissingRunIdErrorEvent'

    invalidRunId = dauphin.NonNull(dauphin.String)


class DauphinLogMessageEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'LogMessageEvent'
        interfaces = (DauphinMessageEvent,)


class DauphinPipelineEvent(dauphin.Interface):
    class Meta(object):
        name = 'PipelineEvent'

    pipeline = dauphin.NonNull('Pipeline')


class DauphinPipelineStartEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineStartEvent'
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineSuccessEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineSuccessEvent'
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineFailureEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineFailureEvent'
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineInitFailureEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineInitFailureEvent'
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)

    error = dauphin.NonNull('PythonError')


class DauphinStepEvent(dauphin.Interface):
    class Meta(object):
        name = 'StepEvent'

    step = dauphin.Field('ExecutionStep')


class DauphinExecutionStepStartEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutionStepStartEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)


class DauphinExecutionStepRestartEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutionStepRestartEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)


class DauphinExecutionStepUpForRetryEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutionStepUpForRetryEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    error = dauphin.NonNull('PythonError')
    secondsToWait = dauphin.Field(dauphin.Int)


class DauphinExecutionStepSkippedEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutionStepSkippedEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)


class DauphinEventPathMetadataEntry(dauphin.ObjectType):
    class Meta(object):
        name = 'EventPathMetadataEntry'
        interfaces = (DauphinEventMetadataEntry,)

    path = dauphin.NonNull(dauphin.String)


class DauphinEventJsonMetadataEntry(dauphin.ObjectType):
    class Meta(object):
        name = 'EventJsonMetadataEntry'
        interfaces = (DauphinEventMetadataEntry,)

    jsonString = dauphin.NonNull(dauphin.String)


class DauphinEventTextMetadataEntry(dauphin.ObjectType):
    class Meta(object):
        name = 'EventTextMetadataEntry'
        interfaces = (DauphinEventMetadataEntry,)

    text = dauphin.NonNull(dauphin.String)


class DauphinEventUrlMetadataEntry(dauphin.ObjectType):
    class Meta(object):
        name = 'EventUrlMetadataEntry'
        interfaces = (DauphinEventMetadataEntry,)

    url = dauphin.NonNull(dauphin.String)


class DauphinEventMarkdownMetadataEntry(dauphin.ObjectType):
    class Meta(object):
        name = 'EventMarkdownMetadataEntry'
        interfaces = (DauphinEventMetadataEntry,)

    md_str = dauphin.NonNull(dauphin.String)


class DauphinEventPythonArtifactMetadataEntry(dauphin.ObjectType):
    class Meta(object):
        name = 'EventPythonArtifactMetadataEntry'
        interfaces = (DauphinEventMetadataEntry,)

    module = dauphin.NonNull(dauphin.String)
    name = dauphin.NonNull(dauphin.String)


def iterate_metadata_entries(metadata_entries):
    check.list_param(metadata_entries, 'metadata_entries', of_type=EventMetadataEntry)
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
        else:
            # skip rest for now
            check.not_implemented(
                '{} unsupported metadata entry for now'.format(type(metadata_entry.entry_data))
            )


def _to_dauphin_metadata_entries(metadata_entries):
    return list(iterate_metadata_entries(metadata_entries) or [])


class DauphinObjectStoreOperationType(dauphin.Enum):
    class Meta(object):
        name = 'ObjectStoreOperationType'

    SET_OBJECT = 'SET_OBJECT'
    GET_OBJECT = 'GET_OBJECT'
    RM_OBJECT = 'RM_OBJECT'
    CP_OBJECT = 'CP_OBJECT'


class DauphinObjectStoreOperationResult(dauphin.ObjectType):
    class Meta(object):
        name = 'ObjectStoreOperationResult'
        interfaces = (DauphinDisplayableEvent,)

    op = dauphin.NonNull('ObjectStoreOperationType')

    def resolve_metadataEntries(self, _graphene_info):
        return _to_dauphin_metadata_entries(self.metadata_entries)


class DauphinMaterialization(dauphin.ObjectType):
    class Meta(object):
        name = 'Materialization'
        interfaces = (DauphinDisplayableEvent,)

    def resolve_metadataEntries(self, _graphene_info):
        return _to_dauphin_metadata_entries(self.metadata_entries)


class DauphinExpectationResult(dauphin.ObjectType):
    class Meta(object):
        name = 'ExpectationResult'
        interfaces = (DauphinDisplayableEvent,)

    success = dauphin.NonNull(dauphin.Boolean)

    def resolve_metadataEntries(self, _graphene_info):
        return _to_dauphin_metadata_entries(self.metadata_entries)


class DauphinTypeCheck(dauphin.ObjectType):
    class Meta(object):
        name = 'TypeCheck'
        interfaces = (DauphinDisplayableEvent,)

    success = dauphin.NonNull(dauphin.Boolean)

    def resolve_metadataEntries(self, _graphene_info):
        return _to_dauphin_metadata_entries(self.metadata_entries)


class DauphinFailureMetadata(dauphin.ObjectType):
    class Meta(object):
        name = 'FailureMetadata'
        interfaces = (DauphinDisplayableEvent,)

    def resolve_metadataEntries(self, _graphene_info):
        return _to_dauphin_metadata_entries(self.metadata_entries)


class DauphinExecutionStepInputEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutionStepInputEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    input_name = dauphin.NonNull(dauphin.String)
    type_check = dauphin.NonNull(DauphinTypeCheck)


class DauphinExecutionStepOutputEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutionStepOutputEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    output_name = dauphin.NonNull(dauphin.String)
    type_check = dauphin.NonNull(DauphinTypeCheck)


class DauphinExecutionStepSuccessEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutionStepSuccessEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)


class DauphinExecutionStepFailureEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutionStepFailureEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    error = dauphin.NonNull('PythonError')
    failureMetadata = dauphin.Field('FailureMetadata')


class DauphinStepMaterializationEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'StepMaterializationEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    materialization = dauphin.NonNull(DauphinMaterialization)


class DauphinObjectStoreOperationEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'ObjectStoreOperationEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    operation_result = dauphin.NonNull(DauphinObjectStoreOperationResult)


class DauphinEngineEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'EngineEvent'
        interfaces = (DauphinMessageEvent, DauphinDisplayableEvent, DauphinStepEvent)

    error = dauphin.Field('PythonError')
    marker_start = dauphin.Field(dauphin.String)
    marker_end = dauphin.Field(dauphin.String)


class DauphinStepExpectationResultEvent(dauphin.ObjectType):
    class Meta(object):
        name = 'StepExpectationResultEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    expectation_result = dauphin.NonNull(DauphinExpectationResult)


# Should be a union of all possible events
class DauphinPipelineRunEvent(dauphin.Union):
    class Meta(object):
        name = 'PipelineRunEvent'
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
            DauphinPipelineSuccessEvent,
            DauphinObjectStoreOperationEvent,
            DauphinStepExpectationResultEvent,
            DauphinStepMaterializationEvent,
            DauphinEngineEvent,
        )


class DauphinPipelineTag(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineTag'

    key = dauphin.NonNull(dauphin.String)
    value = dauphin.NonNull(dauphin.String)

    def __init__(self, key, value):
        super(DauphinPipelineTag, self).__init__(key=key, value=value)


def from_dagster_event_record(graphene_info, event_record, dauphin_pipeline, execution_plan):
    # Lots of event types. Pylint thinks there are too many branches
    # pylint: disable=too-many-branches
    check.inst_param(event_record, 'event_record', EventRecord)
    check.param_invariant(event_record.is_dagster_event, 'event_record')
    check.opt_inst_param(
        dauphin_pipeline,
        'dauphin_pipeline',
        (
            graphene_info.schema.type_named('Pipeline'),
            graphene_info.schema.type_named('UnknownPipeline'),
        ),
    )
    check.opt_inst_param(execution_plan, 'execution_plan', ExecutionPlan)

    dagster_event = event_record.dagster_event
    basic_params = construct_basic_params(graphene_info, event_record, execution_plan)
    if dagster_event.event_type == DagsterEventType.STEP_START:
        return graphene_info.schema.type_named('ExecutionStepStartEvent')(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_SKIPPED:
        return graphene_info.schema.type_named('ExecutionStepSkippedEvent')(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_UP_FOR_RETRY:
        return graphene_info.schema.type_named('ExecutionStepUpForRetryEvent')(
            error=dagster_event.step_retry_data.error,
            secondsToWait=dagster_event.step_retry_data.seconds_to_wait,
            **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.STEP_RESTARTED:
        return graphene_info.schema.type_named('ExecutionStepRestartEvent')(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_SUCCESS:
        return graphene_info.schema.type_named('ExecutionStepSuccessEvent')(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_INPUT:
        input_data = dagster_event.event_specific_data
        return graphene_info.schema.type_named('ExecutionStepInputEvent')(
            input_name=input_data.input_name, type_check=input_data.type_check_data, **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.STEP_OUTPUT:
        output_data = dagster_event.step_output_data
        return graphene_info.schema.type_named('ExecutionStepOutputEvent')(
            output_name=output_data.output_name,
            type_check=output_data.type_check_data,
            **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.STEP_MATERIALIZATION:
        materialization = dagster_event.step_materialization_data.materialization
        return graphene_info.schema.type_named('StepMaterializationEvent')(
            materialization=materialization, **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
        expectation_result = dagster_event.event_specific_data.expectation_result
        return graphene_info.schema.type_named('StepExpectationResultEvent')(
            expectation_result=expectation_result, **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.STEP_FAILURE:
        check.inst(dagster_event.step_failure_data, StepFailureData)
        return graphene_info.schema.type_named('ExecutionStepFailureEvent')(
            error=graphene_info.schema.type_named('PythonError')(
                dagster_event.step_failure_data.error
            ),
            failureMetadata=dagster_event.step_failure_data.user_failure_data,
            **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.PIPELINE_START:
        return graphene_info.schema.type_named('PipelineStartEvent')(
            pipeline=dauphin_pipeline, **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.PIPELINE_SUCCESS:
        return graphene_info.schema.type_named('PipelineSuccessEvent')(
            pipeline=dauphin_pipeline, **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.PIPELINE_FAILURE:
        return graphene_info.schema.type_named('PipelineFailureEvent')(
            pipeline=dauphin_pipeline, **basic_params
        )

    elif dagster_event.event_type == DagsterEventType.PIPELINE_INIT_FAILURE:
        return graphene_info.schema.type_named('PipelineInitFailureEvent')(
            pipeline=dauphin_pipeline,
            error=graphene_info.schema.type_named('PythonError')(
                dagster_event.pipeline_init_failure_data.error
            ),
            **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.OBJECT_STORE_OPERATION:
        operation_result = dagster_event.event_specific_data
        return graphene_info.schema.type_named('ObjectStoreOperationEvent')(
            operation_result=operation_result, **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.ENGINE_EVENT:
        return graphene_info.schema.type_named('EngineEvent')(
            metadataEntries=_to_dauphin_metadata_entries(
                dagster_event.engine_event_data.metadata_entries
            ),
            error=graphene_info.schema.type_named('PythonError')(
                dagster_event.engine_event_data.error
            )
            if dagster_event.engine_event_data.error
            else None,
            marker_start=dagster_event.engine_event_data.marker_start,
            marker_end=dagster_event.engine_event_data.marker_end,
            **basic_params
        )
    else:
        raise Exception(
            'Unknown DAGSTER_EVENT type {inner_type} found in logs'.format(
                inner_type=dagster_event.event_type
            )
        )


def from_compute_log_file(graphene_info, file):
    check.opt_inst_param(file, 'file', ComputeLogFileData)
    if not file:
        return None
    return graphene_info.schema.type_named('ComputeLogFile')(
        path=file.path,
        data=file.data,
        cursor=file.cursor,
        size=file.size,
        download_url=file.download_url,
    )


def from_event_record(graphene_info, event_record, dauphin_pipeline, execution_plan):
    check.inst_param(event_record, 'event_record', EventRecord)
    check.opt_inst_param(
        dauphin_pipeline,
        'dauphin_pipeline',
        (
            graphene_info.schema.type_named('Pipeline'),
            graphene_info.schema.type_named('UnknownPipeline'),
        ),
    )
    check.opt_inst_param(execution_plan, 'execution_plan', ExecutionPlan)

    if event_record.is_dagster_event:
        return from_dagster_event_record(
            graphene_info, event_record, dauphin_pipeline, execution_plan
        )
    else:
        return graphene_info.schema.type_named('LogMessageEvent')(
            **construct_basic_params(graphene_info, event_record, execution_plan)
        )


def create_dauphin_step(graphene_info, event_record, execution_plan):
    check.inst_param(event_record, 'event_record', EventRecord)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    return (
        graphene_info.schema.type_named('ExecutionStep')(
            execution_plan, execution_plan.get_step_by_key(event_record.step_key)
        )
        if event_record.step_key
        else None
    )


def construct_basic_params(graphene_info, event_record, execution_plan):
    check.inst_param(event_record, 'event_record', EventRecord)
    check.opt_inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    return {
        'runId': event_record.run_id,
        'message': event_record.dagster_event.message
        if (event_record.dagster_event and event_record.dagster_event.message)
        else event_record.user_message,
        'timestamp': int(event_record.timestamp * 1000),
        'level': DauphinLogLevel.from_level(event_record.level),
        'step': create_dauphin_step(graphene_info, event_record, execution_plan)
        if execution_plan
        else None,
    }
