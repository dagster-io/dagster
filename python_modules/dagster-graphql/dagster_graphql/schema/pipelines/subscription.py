import graphene

from ..logs.events import GrapheneDagsterRunEvent
from ..util import non_null_list
from .pipeline import GrapheneRun


class GraphenePipelineRunLogsSubscriptionSuccess(graphene.ObjectType):
    run = graphene.NonNull(GrapheneRun)
    messages = non_null_list(GrapheneDagsterRunEvent)
    hasMorePastEvents = graphene.NonNull(graphene.Boolean)
    cursor = graphene.NonNull(graphene.String)

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
