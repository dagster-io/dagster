from __future__ import absolute_import

from dagster import check
from dagster.core.events import EventRecord, EventType
from dagster.utils.logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, check_valid_level_param

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

    def __init__(self, pipeline_run):
        super(DauphinPipelineRun, self).__init__(
            runId=pipeline_run.run_id, status=pipeline_run.status
        )
        self._pipeline_run = check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

    def resolve_pipeline(self, info):
        return model.get_pipeline_or_raise(info, self._pipeline_run.pipeline_name)

    def resolve_logs(self, info):
        return info.schema.type_named('LogMessageConnection')(self._pipeline_run)

    def resolve_executionPlan(self, info):
        pipeline = self.resolve_pipeline(info)
        return info.schema.type_named('ExecutionPlan')(pipeline, self._pipeline_run.execution_plan)


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

    def resolve_nodes(self, info):
        pipeline = model.get_pipeline_or_raise(info, self._pipeline_run.pipeline_name)
        return [
            info.schema.type_named('PipelineRunEvent').from_dagster_event(info, log, pipeline)
            for log in self._logs
        ]

    def resolve_pageInfo(self, info):
        count = len(self._logs)
        lastCursor = None
        if count > 0:
            lastCursor = str(count - 1)
        return info.schema.type_named('PageInfo')(
            lastCursor=lastCursor,
            hasNextPage=None,
            hasPreviousPage=None,
            count=count,
            totalCount=count,
        )


class DaupinPipelineRunLogsSubscriptionPayload(dauphin.ObjectType):
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


class DauphinExecutionStepEvent(dauphin.Interface):
    class Meta:
        name = 'ExecutionStepEvent'

    step = dauphin.NonNull('ExecutionStep')


class DauphinExecutionStepStartEvent(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepStartEvent'
        interfaces = (DauphinMessageEvent, DauphinExecutionStepEvent)


class DauphinExecutionStepSuccessEvent(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepSuccessEvent'
        interfaces = (DauphinMessageEvent, DauphinExecutionStepEvent)


class DauphinExecutionStepFailureEvent(dauphin.ObjectType):
    class Meta:
        name = 'ExecutionStepFailureEvent'
        interfaces = (DauphinMessageEvent, DauphinExecutionStepEvent)

    error = dauphin.NonNull('PythonError')


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
            DauphinExecutionStepFailureEvent,
            DauphinPipelineProcessStartEvent,
            DauphinPipelineProcessStartedEvent,
        )

    @staticmethod
    def from_dagster_event(info, event, pipeline):
        check.inst_param(event, 'event', EventRecord)
        check.inst_param(pipeline, 'pipeline', info.schema.type_named('Pipeline'))
        pipeline_run = info.context.pipeline_runs.get_run_by_id(event.run_id)
        run = DauphinPipelineRun(pipeline_run)

        basic_params = {
            'run': run,
            'message': event.user_message,
            'timestamp': int(event.timestamp * 1000),
            'level': DauphinLogLevel.from_level(event.level),
        }

        if event.event_type == EventType.PIPELINE_START:
            return info.schema.type_named('PipelineStartEvent')(pipeline=pipeline, **basic_params)
        elif event.event_type == EventType.PIPELINE_SUCCESS:
            return info.schema.type_named('PipelineSuccessEvent')(pipeline=pipeline, **basic_params)
        elif event.event_type == EventType.PIPELINE_FAILURE:
            return info.schema.type_named('PipelineFailureEvent')(pipeline=pipeline, **basic_params)
        elif event.event_type == EventType.PIPELINE_PROCESS_START:
            return info.schema.type_named('PipelineProcessStartEvent')(
                pipeline=pipeline, **basic_params
            )
        elif event.event_type == EventType.PIPELINE_PROCESS_STARTED:
            return info.schema.type_named('PipelineProcessStartedEvent')(
                pipeline=pipeline, process_id=event.process_id, **basic_params
            )
        elif event.event_type == EventType.EXECUTION_PLAN_STEP_START:
            return info.schema.type_named('ExecutionStepStartEvent')(
                step=info.schema.type_named('ExecutionStep')(
                    pipeline_run.execution_plan.get_step_by_key(event.step_key)
                ),
                **basic_params
            )
        elif event.event_type == EventType.EXECUTION_PLAN_STEP_SUCCESS:
            return info.schema.type_named('ExecutionStepSuccessEvent')(
                step=info.schema.type_named('ExecutionStep')(
                    pipeline_run.execution_plan.get_step_by_key(event.step_key)
                ),
                **basic_params
            )
        elif event.event_type == EventType.EXECUTION_PLAN_STEP_FAILURE:
            check.inst(event.error_info, SerializableErrorInfo)
            return info.schema.type_named('ExecutionStepFailureEvent')(
                step=info.schema.type_named('ExecutionStep')(
                    pipeline_run.execution_plan.get_step_by_key(event.step_key)
                ),
                error=info.schema.type_named('PythonError')(event.error_info),
                **basic_params
            )
        else:
            return info.schema.type_named('LogMessageEvent')(**basic_params)
