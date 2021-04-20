from dagster import check
from dagster.core.errors import DagsterInvariantViolationError, DagsterRunNotFoundError
from dagster.core.execution.context.system import IPlanContext
from dagster.core.execution.plan.plan import ExecutionPlan


def validate_reexecution_memoization(plan_context, execution_plan):
    check.inst_param(plan_context, "plan_context", IPlanContext)
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

    parent_run_id = plan_context.pipeline_run.parent_run_id
    check.opt_str_param(parent_run_id, "parent_run_id")

    if parent_run_id is None:
        return

    if not plan_context.instance.has_run(parent_run_id):
        raise DagsterRunNotFoundError(
            "Run id {} set as parent run id was not found in instance".format(parent_run_id),
            invalid_run_id=parent_run_id,
        )

    # exclude full pipeline re-execution
    if len(execution_plan.step_keys_to_execute) == len(execution_plan.steps):
        return

    if execution_plan.artifacts_persisted:
        return

    raise DagsterInvariantViolationError(
        "Cannot perform reexecution with in-memory io managers.\n"
        "To enable reexecution, you can set a persistent io manager, such as the "
        'fs_io_manager, in the resource_defs argument on your ModeDefinition: resource_defs={"io_manager": fs_io_manager}'
    )
