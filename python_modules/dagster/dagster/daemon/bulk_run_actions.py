import dagster._check as check
from dagster.core.execution.bulk_actions import BulkActionStatus, BulkActionType
from dagster.core.instance import DagsterInstance


def execute_bulk_run_action_iteration(instance: DagsterInstance, logger):
    requested_actions = instance.run_storage.get_bulk_run_actions(
        action_type=BulkActionType.RUN_TERMINATION, status=BulkActionStatus.REQUESTED
    )
    if not requested_actions:
        logger.debug("No bulk actions requested.")
        yield
        return
    for action in requested_actions:
        check.invariant(action.action_type == BulkActionType.RUN_TERMINATION)
        for run_id in action.run_ids:
            instance.run_coordinator.cancel_run(run_id)
            yield

        instance.run_storage.update_bulk_run_action(action.with_status(BulkActionStatus.COMPLETED))
