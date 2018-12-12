from __future__ import absolute_import

from dagster import check
from dagster.core.events import (
    EventRecord,
    EventType,
)
from dagit import pipeline_run_storage
from dagster.utils.error import SerializableErrorInfo
from dagit.schema import dauphene, model
from dagster.utils.logging import (
    CRITICAL,
    DEBUG,
    ERROR,
    INFO,
    WARNING,
    check_valid_level_param,
)

PipelineRunStatus = dauphene.Enum.from_enum(pipeline_run_storage.PipelineRunStatus)


class PipelineRun(dauphene.ObjectType):
    runId = dauphene.NonNull(dauphene.String)
    status = dauphene.NonNull('PipelineRunStatus')
    pipeline = dauphene.NonNull('Pipeline')
    logs = dauphene.NonNull('LogMessageConnection')
    executionPlan = dauphene.NonNull('ExecutionPlan')

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


class LogLevel(dauphene.Enum):
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


class MessageEvent(dauphene.Interface):
    run = dauphene.NonNull('PipelineRun')
    message = dauphene.NonNull(dauphene.String)
    timestamp = dauphene.NonNull(dauphene.String)
    level = dauphene.NonNull('LogLevel')


class LogMessageConnection(dauphene.ObjectType):
    nodes = dauphene.non_null_list('PipelineRunEvent')
    pageInfo = dauphene.NonNull('PageInfo')

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


class LogMessageEvent(dauphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, )


class PipelineEvent(dauphene.Interface):
    pipeline = dauphene.NonNull('Pipeline')


class PipelineStartEvent(dauphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, PipelineEvent)


class PipelineSuccessEvent(dauphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, PipelineEvent)


class PipelineFailureEvent(dauphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, PipelineEvent)


class ExecutionStepEvent(dauphene.Interface):
    step = dauphene.NonNull('ExecutionStep')


class ExecutionStepStartEvent(dauphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, ExecutionStepEvent)


class ExecutionStepSuccessEvent(dauphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, ExecutionStepEvent)


class ExecutionStepFailureEvent(dauphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, ExecutionStepEvent)

    error = dauphene.NonNull('PythonError')


# Should be a union of all possible events
class PipelineRunEvent(dauphene.Union):
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
