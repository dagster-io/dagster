from dagster import check
from dagster.core.errors import DagsterStepOutputNotFoundError
from dagster.core.events import DagsterEvent
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.memoization import copy_required_intermediates_for_execution
from dagster.core.execution.plan.execute_step import dagster_event_sequence_for_step
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.execution.retries import Retries


def inner_plan_execution_iterator(pipeline_context, execution_plan, retries):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(retries, 'retries', Retries)

    for event in copy_required_intermediates_for_execution(pipeline_context, execution_plan):
        yield event

    # It would be good to implement a reference tracking algorithm here to
    # garbage collect results that are no longer needed by any steps
    # https://github.com/dagster-io/dagster/issues/811
    active_execution = execution_plan.start(retries=retries)
    while not active_execution.is_complete:
        step = active_execution.get_next_step()

        step_context = pipeline_context.for_step(step)
        missing_resources = [
            resource_key
            for resource_key in step_context.required_resource_keys
            if not hasattr(step_context.resources, resource_key)
        ]
        check.invariant(
            len(missing_resources) == 0,
            (
                'Expected step context for solid {solid_name} to have all required resources, but '
                'missing {missing_resources}.'
            ).format(solid_name=step_context.solid.name, missing_resources=missing_resources),
        )

        with pipeline_context.instance.compute_log_manager.watch(
            step_context.pipeline_run, step_context.step.key
        ):
            # capture all of the logs for this step
            uncovered_inputs = pipeline_context.intermediates_manager.uncovered_inputs(
                step_context, step
            )
            if uncovered_inputs:
                # In partial pipeline execution, we may end up here without having validated the
                # missing dependent outputs were optional
                _assert_missing_inputs_optional(uncovered_inputs, execution_plan, step.key)

                step_context.log.info(
                    (
                        'Not all inputs covered for {step}. Not executing. Output missing for '
                        'inputs: {uncovered_inputs}'
                    ).format(uncovered_inputs=uncovered_inputs, step=step.key)
                )
                yield DagsterEvent.step_skipped_event(step_context)
                active_execution.mark_skipped(step.key)
            else:
                for step_event in check.generator(
                    dagster_event_sequence_for_step(step_context, retries)
                ):
                    check.inst(step_event, DagsterEvent)
                    yield step_event
                    active_execution.handle_event(step_event)

            active_execution.verify_complete(pipeline_context, step.key)

        # process skips from failures or uncovered inputs
        for event in active_execution.skipped_step_events_iterator(pipeline_context):
            yield event


def _assert_missing_inputs_optional(uncovered_inputs, execution_plan, step_key):
    nonoptionals = [
        handle for handle in uncovered_inputs if not execution_plan.get_step_output(handle).optional
    ]
    if nonoptionals:
        raise DagsterStepOutputNotFoundError(
            (
                'When executing {step} discovered required outputs missing '
                'from previous step: {nonoptionals}'
            ).format(nonoptionals=nonoptionals, step=step_key),
            step_key=nonoptionals[0].step_key,
            output_name=nonoptionals[0].output_name,
        )
