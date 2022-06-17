import pendulum
from dagster_graphql.schema.inputs import GrapheneRunsFilter

from dagster import DagsterInstance
from dagster.core.execution.bulk_actions import (
    BulkAction,
    BulkActionStatus,
    BulkActionType,
    RunTerminationAction,
)
from dagster.core.utils import make_new_bulk_action_id

from ..utils import capture_error


@capture_error
def add_termination_request(graphene_info, runs_filter: GrapheneRunsFilter) -> None:
    instance: DagsterInstance = graphene_info.context.instance
    instance.run_storage.add_bulk_action(
        BulkAction(
            make_new_bulk_action_id(),
            BulkActionType.RUN_TERMINATION,
            BulkActionStatus.REQUESTED,
            pendulum.now("UTC").timestamp(),
            RunTerminationAction(runs_filter.to_selector()),
        )
    )
