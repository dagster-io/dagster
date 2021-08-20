import graphene

from ..logs.events import GrapheneDagsterRunEvent
from ..util import non_null_list
from .pipeline import GrapheneDagsterRun


class GrapheneDagsterRunLogsSubscriptionSuccess(graphene.ObjectType):
    run = graphene.NonNull(GrapheneDagsterRun)
    messages = non_null_list(GrapheneDagsterRunEvent)

    class Meta:
        name = "DagsterRunLogsSubscriptionSuccess"


class GrapheneDagsterRunLogsSubscriptionFailure(graphene.ObjectType):
    message = graphene.NonNull(graphene.String)
    missingRunId = graphene.Field(graphene.String)

    class Meta:
        name = "DagsterRunLogsSubscriptionFailure"


class GrapheneDagsterRunLogsSubscriptionPayload(graphene.Union):
    class Meta:
        types = (
            GrapheneDagsterRunLogsSubscriptionSuccess,
            GrapheneDagsterRunLogsSubscriptionFailure,
        )
        name = "DagsterRunLogsSubscriptionPayload"
