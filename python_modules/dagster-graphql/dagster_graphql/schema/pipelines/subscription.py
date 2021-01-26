import graphene

from ..logs.events import GraphenePipelineRunEvent
from ..util import non_null_list
from .pipeline import GraphenePipelineRun


class GraphenePipelineRunLogsSubscriptionSuccess(graphene.ObjectType):
    run = graphene.NonNull(GraphenePipelineRun)
    messages = non_null_list(GraphenePipelineRunEvent)

    class Meta:
        name = "PipelineRunLogsSubscriptionSuccess"


class GraphenePipelineRunLogsSubscriptionFailure(graphene.ObjectType):
    message = graphene.NonNull(graphene.String)
    missingRunId = graphene.Field(graphene.String)

    class Meta:
        name = "PipelineRunLogsSubscriptionFailure"


class GraphenePipelineRunLogsSubscriptionPayload(graphene.Union):
    class Meta:
        types = (
            GraphenePipelineRunLogsSubscriptionSuccess,
            GraphenePipelineRunLogsSubscriptionFailure,
        )
        name = "PipelineRunLogsSubscriptionPayload"
