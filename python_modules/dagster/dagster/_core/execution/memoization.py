import dagster._check as check
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.context.system import IPlanContext
from dagster._core.execution.plan.plan import ExecutionPlan


def validate_reexecution_memoization(
    plan_context: IPlanContext, execution_plan: ExecutionPlan
) -> None:

    parent_run_id = plan_context.pipeline_run.parent_run_id
    check.opt_str_param(parent_run_id, "parent_run_id")

    if parent_run_id is None:
        return

    # exclude full pipeline re-execution
    if len(execution_plan.step_keys_to_execute) == len(execution_plan.steps):
        return

    if execution_plan.artifacts_persisted:
        return

    raise DagsterInvariantViolationError(
        "Cannot perform reexecution with in-memory io managers.\n"
        "To enable reexecution, you can set a persistent io manager, such as the "
        'fs_io_manager, in the resource_defs argument on your job: resource_defs={"io_manager": fs_io_manager}'
    )
