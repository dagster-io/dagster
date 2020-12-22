from collections import defaultdict

from dagster import check
from dagster.core.events import DagsterEventType
from dagster.core.execution.plan.handle import UnresolvedStepHandle
from dagster.core.execution.plan.step import ResolvedFromDynamicStepHandle
from dagster.core.host_representation import ExternalExecutionPlan, ExternalPipeline
from dagster.core.instance import DagsterInstance
from dagster.core.storage.tags import RESUME_RETRY_TAG
from graphql.execution.base import ResolveInfo

from .external import get_external_execution_plan_or_raise
from .utils import ExecutionParams


def _update_tracking_dict(tracking, handle):
    if isinstance(handle, ResolvedFromDynamicStepHandle):
        tracking[handle.unresolved_form.to_key()].add(handle)
    else:
        tracking[handle].add(handle)


def _in_tracking_dict(handle, tracking):
    if isinstance(handle, ResolvedFromDynamicStepHandle):
        unresolved_key = handle.unresolved_form.to_key()
        if unresolved_key in tracking:
            return handle in tracking[unresolved_key]
        else:
            return False
    else:
        return handle in tracking


def get_retry_steps_from_execution_plan(instance, execution_plan, parent_run_id):
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(execution_plan, "execution_plan", ExternalExecutionPlan)
    check.opt_str_param(parent_run_id, "parent_run_id")

    if not parent_run_id:
        return execution_plan.step_keys_in_plan

    parent_run = instance.get_run_by_id(parent_run_id)
    parent_run_logs = instance.all_logs(parent_run_id)

    # keep track of steps with dicts that point:
    # * step_key -> set(step_key) in the normal case
    # * unresolved_step_key -> set(mapped_step_key_1, ...) for dynamic outputs
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
    for step in execution_plan.topological_steps():
        if parent_run.step_keys_to_execute and step.key not in parent_run.step_keys_to_execute:
            continue

        if step.handle in failed_steps_in_parent_run_logs:
            to_retry[step.handle].update(failed_steps_in_parent_run_logs[step.handle])

        # Interrupted steps can occur when graceful cleanup from a step failure fails to run,
        # and a step failure event is not generated
        if step.handle in interrupted_steps_in_parent_run_logs:
            to_retry[step.handle].update(interrupted_steps_in_parent_run_logs[step.handle])

        # Missing steps did not execute, e.g. when a run was terminated
        if step.handle not in all_steps_in_parent_run_logs:
            to_retry[step.handle].add(step.handle)

        step_dep_keys = execution_deps[step.key]
        retrying_deps = []
        for handle in to_retry.keys():
            if handle.to_key() in step_dep_keys:
                retrying_deps.append(handle)

        # this step is downstream of a step we are about to retry
        if retrying_deps:
            step_handle = step.handle
            for retrying_handle in retrying_deps:
                if isinstance(retrying_handle, UnresolvedStepHandle) and isinstance(
                    step_handle, UnresolvedStepHandle
                ):
                    resolved_keys = to_retry[retrying_handle]
                    for resolved_handle in resolved_keys:
                        check.invariant(
                            isinstance(resolved_handle, ResolvedFromDynamicStepHandle),
                            "Expected ResolvedFromDynamicStepHandle",
                        )
                        to_retry[step.handle].add(step_handle.resolve(resolved_handle.mapping_key))
                else:
                    to_retry[step.handle].add(step.handle)

    return [step_handle.to_key() for step_set in to_retry.values() for step_handle in step_set]


def compute_step_keys_to_execute(graphene_info, external_pipeline, execution_params):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
    check.inst_param(execution_params, "execution_params", ExecutionParams)

    instance = graphene_info.context.instance

    if not execution_params.step_keys and is_resume_retry(execution_params):
        # Get step keys from parent_run_id if it's a resume/retry
        external_execution_plan = get_external_execution_plan_or_raise(
            graphene_info=graphene_info,
            external_pipeline=external_pipeline,
            mode=execution_params.mode,
            run_config=execution_params.run_config,
            step_keys_to_execute=None,
        )
        return get_retry_steps_from_execution_plan(
            instance, external_execution_plan, execution_params.execution_metadata.parent_run_id
        )
    else:
        return execution_params.step_keys


def is_resume_retry(execution_params):
    check.inst_param(execution_params, "execution_params", ExecutionParams)
    return execution_params.execution_metadata.tags.get(RESUME_RETRY_TAG) == "true"
