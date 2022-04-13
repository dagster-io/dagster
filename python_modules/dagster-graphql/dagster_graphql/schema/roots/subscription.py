import graphene

from dagster import check
from dagster.core.storage.compute_log_manager import ComputeIOType

from ...implementation.execution import gen_compute_logs, gen_events_for_run
from ..external import GrapheneLocationStateChangeSubscription, gen_location_state_changes
from ..logs.compute_logs import GrapheneComputeIOType, GrapheneComputeLogFile
from ..paging import GrapheneCursor
from ..pipelines.subscription import GraphenePipelineRunLogsSubscriptionPayload


class GrapheneDagitSubscription(graphene.ObjectType):
    class Meta:
        name = "DagitSubscription"

    pipelineRunLogs = graphene.Field(
        graphene.NonNull(GraphenePipelineRunLogsSubscriptionPayload),
        runId=graphene.Argument(graphene.NonNull(graphene.ID)),
        after=graphene.Argument(GrapheneCursor),
    )

    computeLogs = graphene.Field(
        graphene.NonNull(GrapheneComputeLogFile),
        runId=graphene.Argument(graphene.NonNull(graphene.ID)),
        stepKey=graphene.Argument(graphene.NonNull(graphene.String)),
        ioType=graphene.Argument(graphene.NonNull(GrapheneComputeIOType)),
        cursor=graphene.Argument(graphene.String),
    )

    locationStateChangeEvents = graphene.Field(
        graphene.NonNull(GrapheneLocationStateChangeSubscription)
    )

    def subscribe_pipelineRunLogs(self, graphene_info, runId, after=None):
        return gen_events_for_run(graphene_info, runId, after)

    def subscribe_computeLogs(self, graphene_info, runId, stepKey, ioType, cursor=None):
        # check.str_param(ioType, "ioType")  # need to resolve to enum
        return gen_compute_logs(
            graphene_info, runId, stepKey, ComputeIOType(ioType), cursor
        )

    def subscribe_locationStateChangeEvents(self, graphene_info):
        return gen_location_state_changes(graphene_info)
