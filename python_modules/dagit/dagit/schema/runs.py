from __future__ import absolute_import

from dagster import check
from dagster.core.events import (
    EventRecord,
    EventType,
)
from dagit import pipeline_run_storage
from dagster.utils.error import SerializableErrorInfo
from dagit.schema import dauphin, model
from dagster.utils.logging import (
    CRITICAL,
    DEBUG,
    ERROR,
    INFO,
    WARNING,
    check_valid_level_param,
)

PipelineRunStatus = dauphin.Enum.from_enum(pipeline_run_storage.PipelineRunStatus)


class PipelineRun(dauphin.ObjectType):
    runId = dauphin.NonNull(dauphin.String)
    status = dauphin.NonNull('PipelineRunStatus')
    pipeline = dauphin.NonNull('Pipeline')
    logs = dauphin.NonNull('LogMessageConnection')
    executionPlan = dauphin.NonNull('ExecutionPlan')

    def __init__(self, pipeline_run):
        super(PipelineRun, self).__init__(runId=pipeline_run.run_id, status=pipeline_run.status)
        self._pipeline_run = check.inst_param(
            pipeline_run, 'pipeline_run', pipeline_run_storage.PipelineRun
        )

    def resolve_pipeline(self, info):
        return model.get_pipeline_or_raise(info, self._pipeline_run.pipeline_name)

    def resolve_logs(self, info):
        return info.schema.LogMessageConnection(self._pipeline_run)

    def resolve_executionPlan(self, info):
        pipeline = self.resolve_pipeline(info)
        return info.schema.ExecutionPlan(pipeline, self._pipeline_run.execution_plan)


class LogLevel(dauphin.Enum):
    CRITICAL = 'CRITICAL'
    ERROR = 'ERROR'
    INFO = 'INFO'
    WARNING = 'WARNING'
    DEBUG = 'DEBUG'

    @staticmethod
    def from_level(level):
        check_valid_level_param(level)
        if level == CRITICAL:
            return LogLevel.CRITICAL
        elif level == ERROR:
            return LogLevel.ERROR
        elif level == INFO:
            return LogLevel.INFO
        elif level == WARNING:
            return LogLevel.WARNING
        elif level == DEBUG:
            return LogLevel.DEBUG
        else:
            check.failed('unknown log level')


class MessageEvent(dauphin.Interface):
    run = dauphin.NonNull('PipelineRun')
    message = dauphin.NonNull(dauphin.String)
    timestamp = dauphin.NonNull(dauphin.String)
    level = dauphin.NonNull('LogLevel')


class LogMessageConnection(dauphin.ObjectType):
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
            info.schema.PipelineRunEvent.from_dagster_event(info, log, pipeline)
            for log in self._logs
        ]

    def resolve_pageInfo(self, info):
        count = len(self._logs)
        lastCursor = None
        if count > 0:
            lastCursor = str(count - 1)
        return info.schema.PageInfo(
            lastCursor=lastCursor,
            hasNextPage=None,
            hasPreviousPage=None,
            count=count,
            totalCount=count,
        )


class LogMessageEvent(dauphin.ObjectType):
    class Meta:
        interfaces = (MessageEvent, )


class PipelineEvent(dauphin.Interface):
    pipeline = dauphin.NonNull('Pipeline')


class PipelineStartEvent(dauphin.ObjectType):
    class Meta:
        interfaces = (MessageEvent, PipelineEvent)


class PipelineSuccessEvent(dauphin.ObjectType):
    class Meta:
        interfaces = (MessageEvent, PipelineEvent)


class PipelineFailureEvent(dauphin.ObjectType):
    class Meta:
        interfaces = (MessageEvent, PipelineEvent)


class ExecutionStepEvent(dauphin.Interface):
    step = dauphin.NonNull('ExecutionStep')


class ExecutionStepStartEvent(dauphin.ObjectType):
    class Meta:
        interfaces = (MessageEvent, ExecutionStepEvent)


class ExecutionStepSuccessEvent(dauphin.ObjectType):
    class Meta:
        interfaces = (MessageEvent, ExecutionStepEvent)


class ExecutionStepFailureEvent(dauphin.ObjectType):
    class Meta:
        interfaces = (MessageEvent, ExecutionStepEvent)

    error = dauphin.NonNull('PythonError')


# Should be a union of all possible events
class PipelineRunEvent(dauphin.Union):
    class Meta:
        types = (
            LogMessageEvent,
            PipelineStartEvent,
            PipelineSuccessEvent,
            PipelineFailureEvent,
            ExecutionStepStartEvent,
            ExecutionStepSuccessEvent,
            ExecutionStepFailureEvent,
        )

    @staticmethod
    def from_dagster_event(info, event, pipeline):
        check.inst_param(event, 'event', EventRecord)
        check.inst_param(pipeline, 'pipeline', info.schema.Pipeline)
        pipeline_run = info.context.pipeline_runs.get_run_by_id(event.run_id)
        run = PipelineRun(pipeline_run)

        basic_params = {
            'run': run,
            'message': event.original_message,
            'timestamp': int(event.timestamp * 1000),
            'level': LogLevel.from_level(event.level),
        }

        if event.event_type == EventType.PIPELINE_START:
            return info.schema.PipelineStartEvent(pipeline=pipeline, **basic_params)
        elif event.event_type == EventType.PIPELINE_SUCCESS:
            return info.schema.PipelineSuccessEvent(pipeline=pipeline, **basic_params)
        elif event.event_type == EventType.PIPELINE_FAILURE:
            return info.schema.PipelineFailureEvent(pipeline=pipeline, **basic_params)
        elif event.event_type == EventType.EXECUTION_PLAN_STEP_START:
            return info.schema.ExecutionStepStartEvent(
                step=info.schema.ExecutionStep(
                    pipeline_run.execution_plan.get_step_by_key(event.step_key)
                ),
                **basic_params
            )
        elif event.event_type == EventType.EXECUTION_PLAN_STEP_SUCCESS:
            return info.schema.ExecutionStepSuccessEvent(
                step=info.schema.ExecutionStep(
                    pipeline_run.execution_plan.get_step_by_key(event.step_key)
                ),
                **basic_params
            )
        elif event.event_type == EventType.EXECUTION_PLAN_STEP_FAILURE:
            check.inst(event.error_info, SerializableErrorInfo)
            failure_event = info.schema.ExecutionStepFailureEvent(
                step=info.schema.ExecutionStep(
                    pipeline_run.execution_plan.get_step_by_key(event.step_key)
                ),
                error=info.schema.PythonError(event.error_info),
                **basic_params
            )
            return failure_event
        else:
            return info.schema.LogMessageEvent(**basic_params)
