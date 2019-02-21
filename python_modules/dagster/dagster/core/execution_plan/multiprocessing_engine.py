import os
import multiprocessing

from dagster import check

from dagster.core.execution_context import PipelineExecutionContext

from .create import create_execution_plan_core
from .objects import ExecutionPlan, ExecutionStepEvent, ExecutionStepEventType, StepOutputHandle
from .plan_subset import ExecutionPlanSubsetInfo
from .simple_engine import start_inprocess_executor


def _execute_in_child_process(
    queue, executor_config, environment_dict, execution_metadata, step_key, inputs_for_step
):
    from dagster.core.execution import yield_pipeline_execution_context

    pipeline = executor_config.pipeline_fn()

    inputs_to_inject = {step_key: inputs_for_step}

    with yield_pipeline_execution_context(
        pipeline, environment_dict, execution_metadata.with_tags(pid=str(os.getpid()))
    ) as pipeline_context:

        execution_plan = create_execution_plan_core(
            pipeline_context,
            subset_info=ExecutionPlanSubsetInfo.with_input_values([step_key], inputs_to_inject),
        )

        for step_event in start_inprocess_executor(pipeline_context, execution_plan):
            data_to_put = {
                'event_type': step_event.event_type,
                'success_data': step_event.success_data,
                'failure_data': step_event.failure_data,
                'step_key': step_event.step.key,
                'tags': step_event.tags,
            }

            queue.put(data_to_put)

    queue.put('DONE')
    queue.close()


def execute_step_out_of_process(executor_config, step_context, step, prev_step_events):
    queue = multiprocessing.Queue()

    check.invariant(
        not step_context.execution_metadata.loggers,
        'Cannot inject loggers via ExecutionMetadata with the Multiprocess executor',
    )

    process = multiprocessing.Process(
        target=_execute_in_child_process,
        args=(
            queue,
            executor_config,
            step_context.environment_dict,
            step_context.execution_metadata,
            step.key,
            _create_input_values(step, prev_step_events),
        ),
    )

    process.start()
    while process.is_alive():
        result = queue.get()
        if result == 'DONE':
            break
        event_type = result['event_type']

        # TODO: should we filter out? Need to think about the relationship between pipelines
        # and subplans
        if step.key != result['step_key']:
            continue

        check.invariant(step.key == result['step_key'])

        yield ExecutionStepEvent(
            event_type=event_type,
            step=step,
            success_data=result['success_data'],
            failure_data=result['failure_data'],
            tags=result['tags'],
        )

    # Do something reasonable on total process failure
    process.join()


def _all_inputs_covered(step, results):
    for step_input in step.step_inputs:
        if step_input.prev_output_handle not in results:
            return False
    return True


def _create_input_values(step, prev_level_results):
    input_values = {}
    for step_input in step.step_inputs:
        prev_output_handle = step_input.prev_output_handle
        input_value = prev_level_results[prev_output_handle].success_data.value
        input_values[step_input.name] = input_value
    return input_values


class MultiprocessExecutorConfig:
    def __init__(self, pipeline_fn):
        self.pipeline_fn = pipeline_fn


def multiprocess_execute_plan(executor_config, pipeline_context, execution_plan):
    check.inst_param(executor_config, 'executor_config', MultiprocessExecutorConfig)
    check.inst_param(pipeline_context, 'pipeline_context', PipelineExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

    step_levels = execution_plan.topological_step_levels()

    # It would be good to implement a reference tracking algorithm here so we could
    # garbage collection results that are no longer needed by any steps
    # https://github.com/dagster-io/dagster/issues/811
    prev_step_events = {}

    for step_level in step_levels:
        for step in step_level:
            step_context = pipeline_context.for_step(step)

            if not _all_inputs_covered(step, prev_step_events):
                result_keys = set(prev_step_events.keys())
                expected_outputs = [ni.prev_output_handle for ni in step.step_inputs]

                step_context.log.debug(
                    (
                        'Not all inputs covered for {step}. Not executing. Keys in result: '
                        '{result_keys}. Outputs need for inputs {expected_outputs}'
                    ).format(
                        expected_outputs=expected_outputs, step=step.key, result_keys=result_keys
                    )
                )
                continue

            for step_event in check.generator(
                execute_step_out_of_process(executor_config, step_context, step, prev_step_events)
            ):
                check.inst(step_event, ExecutionStepEvent)
                yield step_event

                if step_event.event_type == ExecutionStepEventType.STEP_OUTPUT:
                    output_handle = StepOutputHandle(step, step_event.success_data.output_name)
                    prev_step_events[output_handle] = step_event
