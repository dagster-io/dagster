# pylint: disable=missing-graphene-docstring
import graphene

import dagster._check as check
from dagster.core.storage.compute_log_manager import ComputeIOType

from ...implementation.execution import get_compute_log_observable, get_pipeline_run_observable
from ..external import GrapheneLocationStateChangeSubscription, get_location_state_change_observable
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

    def resolve_pipelineRunLogs(self, graphene_info, runId, after=None):
        return get_pipeline_run_observable(graphene_info, runId, after)

    def resolve_computeLogs(self, graphene_info, runId, stepKey, ioType, cursor=None):
        check.str_param(ioType, "ioType")  # need to resolve to enum
        return get_compute_log_observable(
            graphene_info, runId, stepKey, ComputeIOType(ioType), cursor
        )

    def resolve_locationStateChangeEvents(self, graphene_info):
        return get_location_state_change_observable(graphene_info)
