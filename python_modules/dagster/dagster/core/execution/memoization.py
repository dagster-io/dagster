from collections import defaultdict

from dagster import check
from dagster.core.definitions.events import ObjectStoreOperation, ObjectStoreOperationType
from dagster.core.errors import DagsterInvariantViolationError, DagsterRunNotFoundError
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.core.execution.context.system import SystemExecutionContext
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.storage.asset_store import mem_asset_store


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

    # remove this once intermediate storage is fully deprecated
    # https://github.com/dagster-io/dagster/issues/3043
    if pipeline_context.intermediate_storage.is_persistent:
        return

    # exclude the case where non-in-memory asset stores are configured on the required steps
    if check_all_asset_stores_non_mem_for_reexecution(pipeline_context, execution_plan) is False:
        raise DagsterInvariantViolationError(
            "Cannot perform reexecution with in-memory asset stores.\n"
            "You may have configured non persistent intermediate storage `{}` for reexecution. "
            "Intermediate Storage is deprecated in 0.10.0 and will be removed in 0.11.0.".format(
                pipeline_context.intermediate_storage.__class__.__name__
            )
        )


def check_all_asset_stores_non_mem_for_reexecution(pipeline_context, execution_plan):
    """
    Check if all the border steps of the current run have non-in-memory asset stores for reexecution.

    Border steps: all the steps that don't have upstream steps to execute, i.e. indegree is 0).
    """
    check.inst_param(pipeline_context, "pipeline_context", SystemExecutionContext)
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

    for step in execution_plan.get_steps_to_execute_by_level()[0]:
        # check if all its inputs' upstream step outputs have non-in-memory asset store configured
        for step_input in step.step_inputs:
            for step_output_handle in step_input.source.step_output_handle_dependencies:
                manager_key = execution_plan.get_manager_key(step_output_handle)
                manager_def = pipeline_context.mode_def.resource_defs.get(manager_key)
                if (
                    # no asset store is configured
                    not manager_def
                    # asset store is non persistent
                    or manager_def == mem_asset_store  # pylint: disable=comparison-with-callable
                ):
                    return False
    return True


def copy_required_intermediates_for_execution(pipeline_context, execution_plan):
    """
    Uses the intermediates manager to copy intermediates from the previous run that apply to the
    current execution plan, and yields the corresponding events
    """
    check.inst_param(pipeline_context, "pipeline_context", SystemExecutionContext)
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    parent_run_id = pipeline_context.pipeline_run.parent_run_id

    if not parent_run_id:
        return

    parent_run_logs = pipeline_context.instance.all_logs(parent_run_id)

    output_handles_for_current_run = output_handles_from_execution_plan(execution_plan)
    output_handles_from_previous_run = output_handles_from_event_logs(parent_run_logs)
    output_handles_to_copy = output_handles_for_current_run.intersection(
        output_handles_from_previous_run
    )
    output_handles_to_copy_by_step = defaultdict(list)
    for handle in output_handles_to_copy:
        output_handles_to_copy_by_step[handle.step_key].append(handle)

    intermediate_storage = pipeline_context.intermediate_storage
    for step in execution_plan.get_all_steps_in_topo_order():
        step_context = pipeline_context.for_step(step)
        for handle in output_handles_to_copy_by_step.get(step.key, []):
            if intermediate_storage.has_intermediate(pipeline_context, handle):
                continue

            operation = intermediate_storage.copy_intermediate_from_run(
                pipeline_context, parent_run_id, handle
            )
            yield DagsterEvent.object_store_operation(
                step_context,
                ObjectStoreOperation.serializable(operation, value_name=handle.output_name),
            )


def is_intermediate_storage_write_event(record):
    check.inst_param(record, "record", EventRecord)
    if not record.is_dagster_event:
        return False

    write_ops = (
        ObjectStoreOperationType.SET_OBJECT.value,
        ObjectStoreOperationType.CP_OBJECT.value,
    )
    return (
        record.dagster_event.event_type_value == DagsterEventType.OBJECT_STORE_OPERATION.value
        and record.dagster_event.event_specific_data.op in write_ops
    )


def output_handles_from_event_logs(event_logs):
    output_handles_from_previous_run = set()
    failed_step_keys = set(
        record.dagster_event.step_key
        for record in event_logs
        if record.dagster_event_type == DagsterEventType.STEP_FAILURE
    )

    for record in event_logs:
        if not is_intermediate_storage_write_event(record):
            continue

        if record.dagster_event.step_key in failed_step_keys:
            # skip output events from failed steps
            continue

        output_handles_from_previous_run.add(
            StepOutputHandle(
                record.dagster_event.step_key, record.dagster_event.event_specific_data.value_name
            )
        )

    return output_handles_from_previous_run


def output_handles_from_execution_plan(execution_plan):
    output_handles_for_current_run = set()
    for step_level in execution_plan.get_steps_to_execute_by_level():
        for step in step_level:
            for step_input in step.step_inputs:
                for step_output_handle in step_input.source.step_output_handle_dependencies:
                    # Only include handles that won't be satisfied by steps included in this
                    # execution.
                    if step_output_handle.step_key not in execution_plan.step_keys_to_execute:
                        output_handles_for_current_run.add(step_output_handle)
    return output_handles_for_current_run
