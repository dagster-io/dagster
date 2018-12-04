import graphene

from dagster import check
from dagster.core.events import (
    EventRecord,
    EventType,
)
from dagit import pipeline_run_storage
from . import pipelines, generic
from .utils import non_null_list

PipelineRunStatus = graphene.Enum.from_enum(pipeline_run_storage.PipelineRunStatus)


class PipelineRun(graphene.ObjectType):
    runId = graphene.NonNull(graphene.String)
    status = graphene.NonNull(PipelineRunStatus)
    pipeline = graphene.NonNull(lambda: pipelines.Pipeline)
    logs = graphene.NonNull(lambda: LogMessageConnection)

    def __init__(self, pipeline_run):
        super(PipelineRun, self).__init__(runId=pipeline_run.run_id, status=pipeline_run.status)
        self._pipeline_run = check.inst_param(
            pipeline_run, 'pipeline_run', pipeline_run_storage.PipelineRun
        )

    def resolve_pipeline(self, info):
        from . import model
        return model.get_pipeline_or_raise(info.context, self._pipeline_run.pipeline_name)

    def resolve_logs(self, info):
        return LogMessageConnection(self._pipeline_run)


class MessageEvent(graphene.Interface):
    run_id = graphene.NonNull(graphene.ID)
    message = graphene.NonNull(graphene.String)


class LogMessageConnection(graphene.ObjectType):
    nodes = non_null_list(lambda: PipelineRunEvent)
    pageInfo = graphene.NonNull(lambda: generic.PageInfo)

    def __init__(self, pipeline_run):
        self._pipeline_run = check.inst_param(
            pipeline_run, 'pipeline_run', pipeline_run_storage.PipelineRun
        )
        self._logs = self._pipeline_run.all_logs()

    def resolve_nodes(self, info):
        from . import model
        pipeline = model.get_pipeline_or_raise(info.context, self._pipeline_run.pipeline_name)
        return [PipelineRunEvent.from_dagster_event(log, pipeline) for log in self._logs]

    def resolve_pageInfo(self, info):
        count = len(self._logs)
        lastCursor = None
        if count > 0:
            lastCursor = str(count - 1)
        return generic.PageInfo(
            lastCursor=lastCursor,
            hasNextPage=None,
            hasPreviousPage=None,
            count=count,
            totalCount=count,
        )


class LogMessageEvent(graphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, )


class PipelineEvent(graphene.Interface):
    pipeline = graphene.NonNull(lambda: pipelines.Pipeline)


class PipelineStartEvent(graphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, PipelineEvent)


class PipelineSuccessEvent(graphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, PipelineEvent)


class PipelineFailureEvent(graphene.ObjectType):
    class Meta:
        interfaces = (MessageEvent, PipelineEvent)


# Should be a union of all possible events
class PipelineRunEvent(graphene.Union):
    class Meta:
        types = (
            LogMessageEvent,
            PipelineStartEvent,
            PipelineSuccessEvent,
            PipelineFailureEvent,
        )

    @staticmethod
    def from_dagster_event(event, pipeline):
        check.inst_param(event, 'event', EventRecord)
        check.inst_param(pipeline, 'pipeline', pipelines.Pipeline)

        if event.event_type == EventType.PIPELINE_START:
            return PipelineStartEvent(
                run_id=event.run_id,
                message=event.original_message,
                pipeline=pipeline,
            )
        elif event.event_type == EventType.PIPELINE_SUCCESS:
            return PipelineSuccessEvent(
                run_id=event.run_id,
                message=event.original_message,
                pipeline=pipeline,
            )
        elif event.event_type == EventType.PIPELINE_FAILURE:
            return PipelineFailureEvent(
                run_id=event.run_id,
                message=event.original_message,
                pipeline=pipeline,
            )
        elif event.event_type == EventType.UNCATEGORIZED:
            return LogMessageEvent(run_id=event.run_id, message=event.original_message)
        else:
            return LogMessageEvent(run_id=event.run_id, message=event.original_message)
            # check.failed('Unknown event type {event_type}'.format(event_type=event.event_type))
