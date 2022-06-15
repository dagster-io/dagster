import dagster._check as check
from dagster.core.execution.bulk_actions import (
    BulkAction,
    BulkActionStatus,
    BulkActionType,
    RunTerminationAction,
)
from dagster.core.instance import DagsterInstance


def execute_bulk_action_iteration(instance: DagsterInstance, logger):
    requested_actions = instance.run_storage.get_bulk_actions(
        type=BulkActionType.RUN_TERMINATION, status=BulkActionStatus.REQUESTED
    )

    if not requested_actions:
        logger.debug("No bulk actions requested.")
        yield
        return

    for action in requested_actions:
        check.invariant(action.type == BulkActionType.RUN_TERMINATION)
        run_termation_action = check.inst(action.action_data, RunTerminationAction)

        filter = run_termation_action.runs_filter

        for run in instance.get_runs(filters=filter):
            instance.run_coordinator.cancel_run(run.run_id)

        instance.run_storage.update_bulk_action(action.with_status(BulkActionStatus.COMPLETED))
