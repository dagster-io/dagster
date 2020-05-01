from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.tags import RESUME_RETRY_TAG

from .utils import ExecutionParams


def get_retry_steps_from_execution_plan(instance, execution_plan, parent_run_id):
    check.inst_param(instance, 'instance', DagsterInstance)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.opt_str_param(parent_run_id, 'parent_run_id')

    if not parent_run_id:
        return execution_plan.step_keys_to_execute

    parent_run = instance.get_run_by_id(parent_run_id)
    parent_run_logs = instance.all_logs(parent_run_id)
    steps_in_parent_run_logs = set(
        record.dagster_event.step_key
        for record in parent_run_logs
        if record.dagster_event and record.dagster_event.step_key
    )
    failed_step_keys = set(
        record.dagster_event.step_key
        for record in parent_run_logs
        if record.dagster_event_type == DagsterEventType.STEP_FAILURE
    )

    to_retry = []

    execution_deps = execution_plan.execution_deps()
    for step in execution_plan.topological_steps():
        if parent_run.step_keys_to_execute and step.key not in parent_run.step_keys_to_execute:
            continue

        if step.key in failed_step_keys:
            to_retry.append(step.key)
            continue

        # include the steps that did not run
        # e.g. when the run was terminated through the dagit "terminate" button
        if step.key not in steps_in_parent_run_logs:
            to_retry.append(step.key)
            continue

        step_deps = execution_deps[step.key]
        if step_deps.intersection(to_retry):
            # this step is downstream of a step we are about to retry
            to_retry.append(step.key)

    return to_retry


def compute_step_keys_to_execute(graphene_info, execution_params):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    from .fetch_pipelines import get_reconstructable_pipeline_from_selector

    instance = graphene_info.context.instance

    pipeline = get_reconstructable_pipeline_from_selector(graphene_info, execution_params.selector)

    if not execution_params.step_keys and is_resume_retry(execution_params):
        # Get step keys from parent_run_id if it's a resume/retry
        execution_plan = create_execution_plan(
            pipeline, execution_params.environment_dict, mode=execution_params.mode,
        )
        return get_retry_steps_from_execution_plan(
            instance, execution_plan, execution_params.execution_metadata.parent_run_id
        )
    else:
        return execution_params.step_keys


def is_resume_retry(execution_params):
    check.inst_param(execution_params, 'execution_params', ExecutionParams)
    return execution_params.execution_metadata.tags.get(RESUME_RETRY_TAG) == 'true'
