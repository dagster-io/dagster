import graphene
from dagster._core.storage.compute_log_manager import ComputeIOType

from ...implementation.execution import gen_captured_log_data, gen_compute_logs, gen_events_for_run
from ..external import GrapheneLocationStateChangeSubscription, gen_location_state_changes
from ..logs.compute_logs import GrapheneCapturedLogs, GrapheneComputeIOType, GrapheneComputeLogFile
from ..pipelines.subscription import GraphenePipelineRunLogsSubscriptionPayload
from ..util import ResolveInfo, non_null_list


class GrapheneDagitSubscription(graphene.ObjectType):
    """The root for all subscriptions to retrieve real-time data from the Dagster instance."""

    class Meta:
        name = "DagitSubscription"

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

    computeLogs = graphene.Field(
        graphene.NonNull(GrapheneComputeLogFile),
        runId=graphene.Argument(graphene.NonNull(graphene.ID)),
        stepKey=graphene.Argument(graphene.NonNull(graphene.String)),
        ioType=graphene.Argument(graphene.NonNull(GrapheneComputeIOType)),
        cursor=graphene.Argument(graphene.String),
        description=(
            "Retrieve real-time compute logs after applying a filter on run id, step name, log"
            " type, and cursor."
        ),
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

    def subscribe_computeLogs(
        self, graphene_info: ResolveInfo, runId, stepKey, ioType, cursor=None
    ):
        return gen_compute_logs(graphene_info, runId, stepKey, ComputeIOType(ioType.value), cursor)

    def subscribe_capturedLogs(self, graphene_info: ResolveInfo, logKey, cursor=None):
        return gen_captured_log_data(graphene_info, logKey, cursor)

    def subscribe_locationStateChangeEvents(self, graphene_info: ResolveInfo):
        return gen_location_state_changes(graphene_info)
