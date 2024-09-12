import graphene

from dagster_graphql.implementation.execution import gen_captured_log_data, gen_events_for_run
from dagster_graphql.schema.external import (
    GrapheneLocationStateChangeSubscription,
    gen_location_state_changes,
)
from dagster_graphql.schema.logs.compute_logs import GrapheneCapturedLogs
from dagster_graphql.schema.pipelines.subscription import GraphenePipelineRunLogsSubscriptionPayload
from dagster_graphql.schema.util import ResolveInfo, non_null_list


class GrapheneSubscription(graphene.ObjectType):
    """The root for all subscriptions to retrieve real-time data from the Dagster instance."""

    class Meta:
        name = "Subscription"

    pipelineRunLogs = graphene.Field(
        graphene.NonNull(GraphenePipelineRunLogsSubscriptionPayload),
        runId=graphene.Argument(graphene.NonNull(graphene.ID)),
        cursor=graphene.Argument(
            graphene.String,
            description=(
                "A cursor retrieved from the API. Pass 'HEAD' to stream from the current event"
                " onward."
            ),
        ),
        description="Retrieve real-time event logs after applying a filter on run id and cursor.",
    )

    capturedLogs = graphene.Field(
        graphene.NonNull(GrapheneCapturedLogs),
        logKey=graphene.Argument(non_null_list(graphene.String)),
        cursor=graphene.Argument(graphene.String),
        description="Retrieve real-time compute logs.",
    )

    locationStateChangeEvents = graphene.Field(
        graphene.NonNull(GrapheneLocationStateChangeSubscription),
        description=(
            "Retrieve real-time events when a location in the workspace undergoes a state change."
        ),
    )

    def subscribe_pipelineRunLogs(self, graphene_info: ResolveInfo, runId, cursor=None):
        return gen_events_for_run(graphene_info, runId, cursor)

    def subscribe_capturedLogs(self, graphene_info: ResolveInfo, logKey, cursor=None):
        return gen_captured_log_data(graphene_info, logKey, cursor)

    def subscribe_locationStateChangeEvents(self, graphene_info: ResolveInfo):
        return gen_location_state_changes(graphene_info)
