from collections import defaultdict

from dagster import check
from dagster.core.events import DagsterEventType
from dagster.core.execution.plan.handle import StepHandle, UnresolvedStepHandle
from dagster.core.execution.plan.step import ResolvedFromDynamicStepHandle
from dagster.core.host_representation import ExternalExecutionPlan
from dagster.core.instance import DagsterInstance


def _update_tracking_dict(tracking, handle):
    if isinstance(handle, ResolvedFromDynamicStepHandle):
        tracking[handle.unresolved_form.to_key()].add(handle)
    else:
        tracking[handle.to_key()].add(handle)


def _in_tracking_dict(handle, tracking):
    if isinstance(handle, ResolvedFromDynamicStepHandle):
        unresolved_key = handle.unresolved_form.to_key()
        if unresolved_key in tracking:
            return handle in tracking[unresolved_key]
        else:
            return False
    else:
        return handle.to_key() in tracking


def get_retry_steps_from_execution_plan(instance, execution_plan, parent_run_id):
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(execution_plan, "execution_plan", ExternalExecutionPlan)
    check.opt_str_param(parent_run_id, "parent_run_id")

    if not parent_run_id:
        return execution_plan.step_keys_in_plan

    parent_run = instance.get_run_by_id(parent_run_id)
    parent_run_logs = instance.all_logs(parent_run_id)

    # keep track of steps with dicts that point:
    # * step_key -> set(step_handle) in the normal case
    # * unresolved_step_key -> set(resolved_step_handle, ...) for dynamic outputs
    all_steps_in_parent_run_logs = defaultdict(set)
    failed_steps_in_parent_run_logs = defaultdict(set)
    successful_steps_in_parent_run_logs = defaultdict(set)
    interrupted_steps_in_parent_run_logs = defaultdict(set)
    skipped_steps_in_parent_run_logs = defaultdict(set)

    for record in parent_run_logs:
        if record.dagster_event and record.dagster_event.step_handle:
            step_handle = record.dagster_event.step_handle
            _update_tracking_dict(all_steps_in_parent_run_logs, step_handle)

            if record.dagster_event_type == DagsterEventType.STEP_FAILURE:
                _update_tracking_dict(failed_steps_in_parent_run_logs, step_handle)

            if record.dagster_event_type == DagsterEventType.STEP_SUCCESS:
                _update_tracking_dict(successful_steps_in_parent_run_logs, step_handle)

            if record.dagster_event_type == DagsterEventType.STEP_SKIPPED:
                _update_tracking_dict(skipped_steps_in_parent_run_logs, step_handle)

    for step_set in all_steps_in_parent_run_logs.values():
        for step_handle in step_set:
            if (
                not _in_tracking_dict(step_handle, failed_steps_in_parent_run_logs)
                and not _in_tracking_dict(step_handle, successful_steps_in_parent_run_logs)
                and not _in_tracking_dict(step_handle, skipped_steps_in_parent_run_logs)
            ):
                _update_tracking_dict(interrupted_steps_in_parent_run_logs, step_handle)

    to_retry = defaultdict(set)

    execution_deps = execution_plan.execution_deps()
    for step_snap in execution_plan.topological_steps():
        step_key = step_snap.key
        step_handle = StepHandle.parse_from_key(step_snap.key)

        if parent_run.step_keys_to_execute and step_snap.key not in parent_run.step_keys_to_execute:
            continue

        if step_snap.key in failed_steps_in_parent_run_logs:
            to_retry[step_key].update(failed_steps_in_parent_run_logs[step_key])

        # Interrupted steps can occur when graceful cleanup from a step failure fails to run,
        # and a step failure event is not generated
        if step_key in interrupted_steps_in_parent_run_logs:
            to_retry[step_key].update(interrupted_steps_in_parent_run_logs[step_key])

        # Missing steps did not execute, e.g. when a run was terminated
        if step_key not in all_steps_in_parent_run_logs:
            to_retry[step_key].add(step_handle)

        step_dep_keys = execution_deps[step_key]
        retrying_dep_keys = step_dep_keys.intersection(to_retry.keys())

        # this step is downstream of a step we are about to retry
        if retrying_dep_keys:
            for retrying_key in retrying_dep_keys:
                # If this step and its ancestor are both downstream of a dynamic output,
                # add resolved instances of this step for the retrying mapping keys
                if isinstance(step_handle, UnresolvedStepHandle) and all(
                    map(
                        lambda handle: isinstance(handle, ResolvedFromDynamicStepHandle),
                        to_retry[retrying_key],
                    )
                ):
                    for resolved_handle in to_retry[retrying_key]:
                        to_retry[step_key].add(step_handle.resolve(resolved_handle.mapping_key))

                else:
                    to_retry[step_key].add(step_handle)

    return [step_handle.to_key() for step_set in to_retry.values() for step_handle in step_set]
