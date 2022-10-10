import graphene
from dagster_graphql.schema.inputs import GrapheneAssetKeyInput
from dagster_graphql.schema.util import non_null_list

import dagster._check as check
from dagster import AssetKey
from dagster._core.storage.compute_log_manager import ComputeIOType

from ...implementation.execution import get_compute_log_observable, get_pipeline_run_observable
from ..asset_subscription import (
    GrapheneAssetLogEventsSubscriptionPayload,
    get_asset_log_events_observable,
)
from ..external import GrapheneLocationStateChangeSubscription, get_location_state_change_observable
from ..logs.compute_logs import GrapheneComputeIOType, GrapheneComputeLogFile
from ..pipelines.subscription import GraphenePipelineRunLogsSubscriptionPayload


class GrapheneDagitSubscription(graphene.ObjectType):
    """The root for all subscriptions to retrieve real-time data from the Dagster instance."""

    class Meta:
        name = "DagitSubscription"

    pipelineRunLogs = graphene.Field(
        graphene.NonNull(GraphenePipelineRunLogsSubscriptionPayload),
        runId=graphene.Argument(graphene.NonNull(graphene.ID)),
        cursor=graphene.Argument(graphene.String),
        description="Retrieve real-time event logs after applying a filter on run id and cursor.",
    )

    computeLogs = graphene.Field(
        graphene.NonNull(GrapheneComputeLogFile),
        runId=graphene.Argument(graphene.NonNull(graphene.ID)),
        stepKey=graphene.Argument(graphene.NonNull(graphene.String)),
        ioType=graphene.Argument(graphene.NonNull(GrapheneComputeIOType)),
        cursor=graphene.Argument(graphene.String),
        description="Retrieve real-time compute logs after applying a filter on run id, step name, log type, and cursor.",
    )

    locationStateChangeEvents = graphene.Field(
        graphene.NonNull(GrapheneLocationStateChangeSubscription),
        description="Retrieve real-time events when a location in the workspace undergoes a state change.",
    )

    assetLogEvents = graphene.Field(
        graphene.NonNull(GrapheneAssetLogEventsSubscriptionPayload),
        assetKeys=graphene.Argument(non_null_list(GrapheneAssetKeyInput)),
        description="Real-time events when any run emits an asset materialization or observation event.",
    )

    def resolve_pipelineRunLogs(self, graphene_info, runId, cursor=None):
        return get_pipeline_run_observable(graphene_info, runId, cursor)

    def resolve_computeLogs(self, graphene_info, runId, stepKey, ioType, cursor=None):
        check.str_param(ioType, "ioType")  # need to resolve to enum
        return get_compute_log_observable(
            graphene_info, runId, stepKey, ComputeIOType(ioType), cursor
        )

    def resolve_locationStateChangeEvents(self, graphene_info):
        return get_location_state_change_observable(graphene_info)

    def resolve_assetLogEvents(self, graphene_info, **kwargs):
        asset_keys = set(
            AssetKey.from_graphql_input(asset_key) for asset_key in kwargs.get("assetKeys", [])
        )
        return get_asset_log_events_observable(graphene_info, asset_keys)
