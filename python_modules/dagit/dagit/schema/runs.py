from __future__ import absolute_import

from dagster import check
from dagster.core.events import EventRecord, EventType
from dagster.utils.logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, check_valid_level_param
from dagster.core.execution_plan.objects import ExecutionPlan

from dagster.utils.error import SerializableErrorInfo
from dagit import pipeline_run_storage
from dagit.pipeline_run_storage import PipelineRunStatus, PipelineRun
from dagit.schema import dauphin, model

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
        return model.get_pipeline_or_raise(graphene_info, self._pipeline_run.selector)

    def resolve_logs(self, graphene_info):
        return graphene_info.schema.type_named('LogMessageConnection')(self._pipeline_run)

    def resolve_executionPlan(self, graphene_info):
        pipeline = self.resolve_pipeline(graphene_info)
        return graphene_info.schema.type_named('ExecutionPlan')(
            pipeline, self._pipeline_run.execution_plan
        )

    def resolve_config(self, _graphene_info):
        return self._pipeline_run.config


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
        self._pipeline_run = check.inst_param(
            pipeline_run, 'pipeline_run', pipeline_run_storage.PipelineRun
        )
        self._logs = self._pipeline_run.all_logs()

    def resolve_nodes(self, graphene_info):
        pipeline = model.get_pipeline_or_raise(graphene_info, self._pipeline_run.selector)
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


class DauphinPipelineRunLogsSubscriptionPayload(dauphin.ObjectType):
    class Meta:
        name = 'PipelineRunLogsSubscriptionPayload'

    messages = dauphin.non_null_list('PipelineRunEvent')


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


class DauphinExecutionStepStartEvent(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepStartEvent'
        interfaces = (DauphinMessageEvent,)


class DauphinExecutionStepOutputEvent(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepOutputEvent'
        interfaces = (DauphinMessageEvent,)

    output_name = dauphin.NonNull(dauphin.String)
    storage_mode = dauphin.NonNull(dauphin.String)
    storage_object_id = dauphin.NonNull(dauphin.String)


class DauphinExecutionStepSuccessEvent(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepSuccessEvent'
        interfaces = (DauphinMessageEvent,)


class DauphinExecutionStepFailureEvent(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepFailureEvent'
        interfaces = (DauphinMessageEvent,)

    error = dauphin.NonNull('PythonError')


class DauphinStepMaterializationEvent(dauphin.ObjectType):
    class Meta:
        name = 'StepMaterializationEvent'
        interfaces = (DauphinMessageEvent,)

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
            DauphinExecutionStepStartEvent,
            DauphinExecutionStepSuccessEvent,
            DauphinExecutionStepOutputEvent,
            DauphinExecutionStepFailureEvent,
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

        if event.event_type == EventType.PIPELINE_START:
            return graphene_info.schema.type_named('PipelineStartEvent')(
                pipeline=dauphin_pipeline, **basic_params
            )
        elif event.event_type == EventType.PIPELINE_SUCCESS:
            return graphene_info.schema.type_named('PipelineSuccessEvent')(
                pipeline=dauphin_pipeline, **basic_params
            )
        elif event.event_type == EventType.PIPELINE_FAILURE:
            return graphene_info.schema.type_named('PipelineFailureEvent')(
                pipeline=dauphin_pipeline, **basic_params
            )
        elif event.event_type == EventType.PIPELINE_PROCESS_START:
            return graphene_info.schema.type_named('PipelineProcessStartEvent')(
                pipeline=dauphin_pipeline, **basic_params
            )
        elif event.event_type == EventType.PIPELINE_PROCESS_STARTED:
            return graphene_info.schema.type_named('PipelineProcessStartedEvent')(
                pipeline=dauphin_pipeline, process_id=event.process_id, **basic_params
            )
        elif event.event_type == EventType.EXECUTION_PLAN_STEP_START:
            return graphene_info.schema.type_named('ExecutionStepStartEvent')(**basic_params)
        elif event.event_type == EventType.EXECUTION_PLAN_STEP_SUCCESS:
            return graphene_info.schema.type_named('ExecutionStepSuccessEvent')(**basic_params)
        elif event.event_type == EventType.EXECUTION_PLAN_STEP_OUTPUT:
            return graphene_info.schema.type_named('ExecutionStepOutputEvent')(
                output_name=event.output_name,
                storage_mode=event.storage_mode,
                storage_object_id=event.storage_object_id,
                **basic_params
            )
        elif event.event_type == EventType.EXECUTION_PLAN_STEP_FAILURE:
            check.inst(event.error_info, SerializableErrorInfo)
            return graphene_info.schema.type_named('ExecutionStepFailureEvent')(
                error=graphene_info.schema.type_named('PythonError')(event.error_info),
                **basic_params
            )
        elif event.event_type == EventType.STEP_MATERIALIZATION:
            return graphene_info.schema.type_named('StepMaterializationEvent')(
                file_name=event.file_name, file_location=event.file_location, **basic_params
            )
        else:
            return graphene_info.schema.type_named('LogMessageEvent')(**basic_params)
