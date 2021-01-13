from dagster import check
from dagster.core.errors import DagsterInvariantViolationError, DagsterRunNotFoundError
from dagster.core.execution.context.system import SystemExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan


def validate_reexecution_memoization(pipeline_context, execution_plan):
    check.inst_param(pipeline_context, "pipeline_context", SystemExecutionContext)
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

    parent_run_id = pipeline_context.pipeline_run.parent_run_id
    check.opt_str_param(parent_run_id, "parent_run_id")

    if parent_run_id is None:
        return

    if not pipeline_context.instance.has_run(parent_run_id):
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
        "Cannot perform reexecution with in-memory asset stores.\n"
        "You may have configured non persistent intermediate storage `{}` for reexecution. "
        "Intermediate Storage is deprecated in 0.10.0 and will be removed in 0.11.0.".format(
            pipeline_context.intermediate_storage.__class__.__name__
        )
    )
