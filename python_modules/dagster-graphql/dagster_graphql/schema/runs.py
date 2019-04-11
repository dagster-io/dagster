from __future__ import absolute_import
import yaml

from dagster import check
from dagster.core.events.logging import EventRecord
from dagster.core.events import DagsterEventType

from dagster.utils.logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, check_valid_level_param
from dagster.core.execution_plan.objects import ExecutionPlan, StepFailureData

from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_pipelines import get_pipeline_or_raise
from dagster_graphql.implementation.pipeline_run_storage import PipelineRunStatus, PipelineRun

DauphinPipelineRunStatus = dauphin.Enum.from_enum(PipelineRunStatus)


class DauphinPipelineRun(dauphin.ObjectType):
    class Meta:
        name = 'PipelineRun'

    runId = dauphin.NonNull(dauphin.String)
    status = dauphin.NonNull('PipelineRunStatus')
    pipeline = dauphin.NonNull('Pipeline')
    logs = dauphin.NonNull('LogMessageConnection')
    executionPlan = dauphin.NonNull('ExecutionPlan')
    config = dauphin.NonNull(dauphin.String)

    def __init__(self, pipeline_run):
        super(DauphinPipelineRun, self).__init__(
            runId=pipeline_run.run_id, status=pipeline_run.status
        )
        self._pipeline_run = check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

    def resolve_pipeline(self, graphene_info):
        return get_pipeline_or_raise(graphene_info, self._pipeline_run.selector)

    def resolve_logs(self, graphene_info):
        return graphene_info.schema.type_named('LogMessageConnection')(self._pipeline_run)

    def resolve_executionPlan(self, graphene_info):
        pipeline = self.resolve_pipeline(graphene_info)
        return graphene_info.schema.type_named('ExecutionPlan')(
            pipeline, self._pipeline_run.execution_plan
        )

    def resolve_config(self, _graphene_info):
        return yaml.dump(self._pipeline_run.config, default_flow_style=False)


class DauphinLogLevel(dauphin.Enum):
    class Meta:
        name = 'LogLevel'

    CRITICAL = 'CRITICAL'
    ERROR = 'ERROR'
    INFO = 'INFO'
    WARNING = 'WARNING'
    DEBUG = 'DEBUG'

    @staticmethod
    def from_level(level):
        check_valid_level_param(level)
        if level == CRITICAL:
            return DauphinLogLevel.CRITICAL
        elif level == ERROR:
            return DauphinLogLevel.ERROR
        elif level == INFO:
            return DauphinLogLevel.INFO
        elif level == WARNING:
            return DauphinLogLevel.WARNING
        elif level == DEBUG:
            return DauphinLogLevel.DEBUG
        else:
            check.failed('unknown log level')


class DauphinMessageEvent(dauphin.Interface):
    class Meta:
        name = 'MessageEvent'

    run = dauphin.NonNull('PipelineRun')
    message = dauphin.NonNull(dauphin.String)
    timestamp = dauphin.NonNull(dauphin.String)
    level = dauphin.NonNull('LogLevel')
    step = dauphin.Field('ExecutionStep')


class DauphinLogMessageConnection(dauphin.ObjectType):
    class Meta:
        name = 'LogMessageConnection'

    nodes = dauphin.non_null_list('PipelineRunEvent')
    pageInfo = dauphin.NonNull('PageInfo')

    def __init__(self, pipeline_run):
        self._pipeline_run = check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        self._logs = self._pipeline_run.all_logs()

    def resolve_nodes(self, graphene_info):
        pipeline = get_pipeline_or_raise(graphene_info, self._pipeline_run.selector)
        return [
            graphene_info.schema.type_named('PipelineRunEvent').from_dagster_event(
                graphene_info, log, pipeline, self._pipeline_run.execution_plan
            )
            for log in self._logs
        ]

    def resolve_pageInfo(self, graphene_info):
        count = len(self._logs)
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
    class Meta:
        name = 'PipelineRunLogsSubscriptionSuccess'

    messages = dauphin.non_null_list('PipelineRunEvent')


class DauphinPipelineRunLogsSubscriptionMissingRunIdFailure(dauphin.ObjectType):
    class Meta:
        name = 'PipelineRunLogsSubscriptionMissingRunIdFailure'

    missingRunId = dauphin.NonNull(dauphin.String)


class DauphinPipelineRunLogsSubscriptionPayload(dauphin.Union):
    class Meta:
        name = 'PipelineRunLogsSubscriptionPayload'
        types = (
            DauphinPipelineRunLogsSubscriptionSuccess,
            DauphinPipelineRunLogsSubscriptionMissingRunIdFailure,
        )


class DauphinMissingRunIdErrorEvent(dauphin.ObjectType):
    class Meta:
        name = 'MissingRunIdErrorEvent'

    invalidRunId = dauphin.NonNull(dauphin.String)


class DauphinLogMessageEvent(dauphin.ObjectType):
    class Meta:
        name = 'LogMessageEvent'
        interfaces = (DauphinMessageEvent,)


class DauphinPipelineEvent(dauphin.Interface):
    class Meta:
        name = 'PipelineEvent'

    pipeline = dauphin.NonNull('Pipeline')


class DauphinPipelineStartEvent(dauphin.ObjectType):
    class Meta:
        name = 'PipelineStartEvent'
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineSuccessEvent(dauphin.ObjectType):
    class Meta:
        name = 'PipelineSuccessEvent'
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineFailureEvent(dauphin.ObjectType):
    class Meta:
        name = 'PipelineFailureEvent'
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineProcessStartEvent(dauphin.ObjectType):
    class Meta:
        name = 'PipelineProcessStartEvent'
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)


class DauphinPipelineProcessStartedEvent(dauphin.ObjectType):
    class Meta:
        name = 'PipelineProcessStartedEvent'
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)

    process_id = dauphin.NonNull(dauphin.Int)


class DauphinPipelineInitFailureEvent(dauphin.ObjectType):
    class Meta:
        name = 'PipelineInitFailureEvent'
        interfaces = (DauphinMessageEvent, DauphinPipelineEvent)

    error = dauphin.NonNull('PythonError')


class DauphinStepEvent(dauphin.Interface):
    class Meta:
        name = 'StepEvent'

    step = dauphin.Field('ExecutionStep')


class DauphinExecutionStepStartEvent(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepStartEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)


class DauphinExecutionStepSkippedEvent(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepSkippedEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)


class DauphinExecutionStepOutputEvent(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepOutputEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    output_name = dauphin.NonNull(dauphin.String)
    storage_mode = dauphin.NonNull(dauphin.String)
    storage_object_id = dauphin.NonNull(dauphin.String)
    value_repr = dauphin.NonNull(dauphin.String)


class DauphinExecutionStepSuccessEvent(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepSuccessEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)


class DauphinExecutionStepFailureEvent(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepFailureEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    error = dauphin.NonNull('PythonError')


class DauphinStepMaterializationEvent(dauphin.ObjectType):
    class Meta:
        name = 'StepMaterializationEvent'
        interfaces = (DauphinMessageEvent, DauphinStepEvent)

    file_name = dauphin.NonNull(dauphin.String)
    file_location = dauphin.NonNull(dauphin.String)


# Should be a union of all possible events
class DauphinPipelineRunEvent(dauphin.Union):
    class Meta:
        name = 'PipelineRunEvent'
        types = (
            DauphinLogMessageEvent,
            DauphinPipelineStartEvent,
            DauphinPipelineSuccessEvent,
            DauphinPipelineFailureEvent,
            DauphinPipelineInitFailureEvent,
            DauphinExecutionStepStartEvent,
            DauphinExecutionStepSuccessEvent,
            DauphinExecutionStepOutputEvent,
            DauphinExecutionStepFailureEvent,
            DauphinExecutionStepSkippedEvent,
            DauphinPipelineProcessStartEvent,
            DauphinPipelineProcessStartedEvent,
            DauphinStepMaterializationEvent,
        )

    @staticmethod
    def from_dagster_event(graphene_info, event, dauphin_pipeline, execution_plan):
        check.inst_param(event, 'event', EventRecord)
        check.inst_param(
            dauphin_pipeline, 'dauphin_pipeline', graphene_info.schema.type_named('Pipeline')
        )
        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

        pipeline_run = graphene_info.context.pipeline_runs.get_run_by_id(event.run_id)
        dauphin_run = DauphinPipelineRun(pipeline_run)

        dauphin_step = (
            graphene_info.schema.type_named('ExecutionStep')(
                pipeline_run.execution_plan,
                pipeline_run.execution_plan.get_step_by_key(event.step_key),
            )
            if event.step_key
            else None
        )

        basic_params = {
            'run': dauphin_run,
            'message': event.user_message,
            'timestamp': int(event.timestamp * 1000),
            'level': DauphinLogLevel.from_level(event.level),
            'step': dauphin_step,
        }

        if event.is_dagster_event:
            dagster_event = event.dagster_event
            if dagster_event.event_type == DagsterEventType.STEP_START:
                return graphene_info.schema.type_named('ExecutionStepStartEvent')(**basic_params)
            elif dagster_event.event_type == DagsterEventType.STEP_SKIPPED:
                return graphene_info.schema.type_named('ExecutionStepSkippedEvent')(**basic_params)
            elif dagster_event.event_type == DagsterEventType.STEP_SUCCESS:
                return graphene_info.schema.type_named('ExecutionStepSuccessEvent')(**basic_params)
            elif dagster_event.event_type == DagsterEventType.STEP_OUTPUT:
                output_data = event.dagster_event.step_output_data
                return graphene_info.schema.type_named('ExecutionStepOutputEvent')(
                    output_name=output_data.output_name,
                    storage_mode=output_data.storage_mode.value,
                    storage_object_id=output_data.storage_object_id,
                    **basic_params
                )
            elif dagster_event.event_type == DagsterEventType.STEP_MATERIALIZATION:
                materialization_data = dagster_event.step_materialization_data
                return graphene_info.schema.type_named('StepMaterializationEvent')(
                    file_name=materialization_data.name,
                    file_location=materialization_data.path,
                    **basic_params
                )
            elif dagster_event.event_type == DagsterEventType.STEP_FAILURE:
                check.inst(dagster_event.step_failure_data, StepFailureData)
                return graphene_info.schema.type_named('ExecutionStepFailureEvent')(
                    error=graphene_info.schema.type_named('PythonError')(
                        dagster_event.step_failure_data.error
                    ),
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
            elif dagster_event.event_type == DagsterEventType.PIPELINE_PROCESS_START:
                return graphene_info.schema.type_named('PipelineProcessStartEvent')(
                    pipeline=dauphin_pipeline, **basic_params
                )
            elif dagster_event.event_type == DagsterEventType.PIPELINE_PROCESS_STARTED:
                process_data = dagster_event.pipeline_process_started_data
                return graphene_info.schema.type_named('PipelineProcessStartedEvent')(
                    pipeline=dauphin_pipeline, process_id=process_data.process_id, **basic_params
                )
            elif dagster_event.event_type == DagsterEventType.PIPELINE_INIT_FAILURE:
                return graphene_info.schema.type_named('PipelineInitFailureEvent')(
                    pipeline=dauphin_pipeline,
                    error=graphene_info.schema.type_named('PythonError')(
                        dagster_event.pipeline_init_failure_data.error
                    ),
                    **basic_params
                )

            else:
                raise Exception(
                    ('Unknown DAGSTER_EVENT type {inner_type} found in logs').format(
                        inner_type=dagster_event.event_type
                    )
                )

        else:
            return graphene_info.schema.type_named('LogMessageEvent')(**basic_params)
