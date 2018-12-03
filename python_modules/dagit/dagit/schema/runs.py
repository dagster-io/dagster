import graphene

from dagster import check
from dagster.core.events import (
    EventRecord,
    EventType,
    PipelineEventRecord,
)
from . import pipelines


class PipelineRun(graphene.ObjectType):
    runId = graphene.NonNull(graphene.String)
    pipeline = graphene.NonNull(lambda: pipelines.Pipeline)


class LogMessageEvent(graphene.ObjectType):
    run_id = graphene.NonNull(graphene.ID)
    message = graphene.NonNull(graphene.String)


class PipelineEvent(graphene.ObjectType):
    run_id = graphene.NonNull(graphene.ID)
    message = graphene.NonNull(graphene.String)
    pipeline = graphene.NonNull(lambda: pipelines.Pipeline)


class PipelineStartEvent(PipelineEvent):
    pass


class PipelineSuccessEvent(PipelineEvent):
    pass


class PipelineFailureEvent(PipelineEvent):
    pass


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
                message=event.message,
                pipeline=pipeline,
            )
        elif event.event_type == EventType.PIPELINE_SUCCESS:
            return PipelineSuccessEvent(
                run_id=event.run_id,
                message=event.message,
                pipeline=pipeline,
            )
        elif event.event_type == EventType.PIPELINE_FAILURE:
            return PipelineFailureEvent(
                run_id=event.run_id,
                message=event.message,
                pipeline=pipeline,
            )
        elif event.event_type == EventType.UNCATEGORIZED:
            return LogMessageEvent(run_id=event.run_id, message=event.message)
        else:
            check.failed('Unknown event type {event_type}'.format(event_type=event.event_type))
