import enum
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import dagster._check as check
from dagster.core.errors import DagsterExecutionPlanSnapshotNotFoundError
from dagster.core.events import DagsterEventType
from dagster.core.execution.plan.handle import StepHandle, UnresolvedStepHandle
from dagster.core.execution.plan.state import KnownExecutionState
from dagster.core.execution.plan.step import ResolvedFromDynamicStepHandle
from dagster.core.host_representation import ExternalExecutionPlan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun


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


class ReexecutionStrategy(enum.Enum):
    ALL_STEPS = "ALL_STEPS"
    FROM_FAILURE = "FROM_FAILURE"


def get_retry_steps_from_parent_run(
    instance, parent_run_id: str = None, parent_run: PipelineRun = None
) -> Tuple[List[str], Optional[KnownExecutionState]]:
    check.inst_param(instance, "instance", DagsterInstance)

    check.invariant(
        bool(parent_run_id) != bool(parent_run), "Must provide one of parent_run_id or parent_run"
    )
    check.opt_str_param(parent_run_id, "parent_run_id")
    check.opt_inst_param(parent_run, "parent_run", PipelineRun)

    parent_run = parent_run or instance.get_run_by_id(parent_run_id)
    parent_run_id = parent_run.run_id
    parent_run_logs = instance.all_logs(parent_run_id)

    execution_plan_snapshot = instance.get_execution_plan_snapshot(
        parent_run.execution_plan_snapshot_id
    )

    if not execution_plan_snapshot:
        raise DagsterExecutionPlanSnapshotNotFoundError(
            f"Could not load execution plan snapshot for run {parent_run_id}"
        )

    execution_plan = ExternalExecutionPlan(execution_plan_snapshot=execution_plan_snapshot)

    # keep track of steps with dicts that point:
    # * step_key -> set(step_handle) in the normal case
    # * unresolved_step_key -> set(resolved_step_handle, ...) for dynamic outputs
    all_steps_in_parent_run_logs: Dict[str, set] = defaultdict(set)
    failed_steps_in_parent_run_logs: Dict[str, set] = defaultdict(set)
    successful_steps_in_parent_run_logs: Dict[str, set] = defaultdict(set)
    interrupted_steps_in_parent_run_logs: Dict[str, set] = defaultdict(set)
    skipped_steps_in_parent_run_logs: Dict[str, set] = defaultdict(set)

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

    steps_to_retry = [
        step_handle.to_key() for step_set in to_retry.values() for step_handle in step_set
    ]

    return steps_to_retry, KnownExecutionState.for_reexecution(parent_run_logs, steps_to_retry)
