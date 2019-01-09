from contextlib import contextmanager
import sys

from future.utils import raise_from

from dagster import check

from dagster.utils.logging import get_formatted_stack_trace

from dagster.utils.timing import time_execution_scope

from dagster.core.definitions import Result

from dagster.core.errors import (
    DagsterError,
    DagsterInvariantViolationError,
    DagsterRuntimeCoercionError,
    DagsterUserCodeExecutionError,
    DagsterTypeError,
)

from dagster.core.execution_context import RuntimeExecutionContext

from .objects import (
    ExecutionPlan,
    ExecutionStep,
    StepResult,
    StepOutputHandle,
    StepSuccessData,
    StepFailureData,
)


def _all_inputs_covered(step, results):
    for step_input in step.step_inputs:
        if step_input.prev_output_handle not in results:
            return False
    return True


def execute_plan_core(context, execution_plan):
    check.inst_param(context, 'context', RuntimeExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    steps = list(execution_plan.topological_steps())

    intermediate_results = {}
    context.debug(
        'Entering execute_steps loop. Order: {order}'.format(order=[step.key for step in steps])
    )

    for step in steps:
        if not _all_inputs_covered(step, intermediate_results):
            result_keys = set(intermediate_results.keys())
            expected_outputs = [ni.prev_output_handle for ni in step.step_inputs]

            context.debug(
                'Not all inputs covered for {step}. Not executing.'.format(step=step.key)
                + '\nKeys in result: {result_keys}.'.format(result_keys=result_keys)
                + '\nOutputs need for inputs {expected_outputs}'.format(
                    expected_outputs=expected_outputs
                )
            )
            continue

        input_values = {}
        for step_input in step.step_inputs:
            prev_output_handle = step_input.prev_output_handle
            input_value = intermediate_results[prev_output_handle].success_data.value
            input_values[step_input.name] = input_value

        for result in execute_step(step, context, input_values):
            check.invariant(isinstance(result, StepResult))
            yield result
            if result.success:
                output_handle = StepOutputHandle(step, result.success_data.output_name)
                intermediate_results[output_handle] = result


def execute_step(step, context, inputs):
    check.inst_param(step, 'step', ExecutionStep)
    check.inst_param(context, 'context', RuntimeExecutionContext)
    check.dict_param(inputs, 'inputs', key_type=str)

    try:
        for step_result in _execute_steps_core_loop(step, context, inputs):
            context.info(
                'Step {step} emitted {value} for output {output}'.format(
                    step=step.key,
                    value=repr(step_result.success_data.value),
                    output=step_result.success_data.output_name,
                )
            )
            yield step_result
    except DagsterError as dagster_error:
        context.error(str(dagster_error))
        yield StepResult.failure_result(
            step=step, tag=step.tag, failure_data=StepFailureData(dagster_error=dagster_error)
        )
        return


def _error_check_results(step, results):
    seen_outputs = set()
    for result in results:
        if not step.has_step_output(result.output_name):
            output_names = list(
                [output_def.name for output_def in step.solid.definition.output_defs]
            )
            raise DagsterInvariantViolationError(
                '''Core transform for {step.solid.name} returned an output
                {result.output_name} that does not exist. The available
                outputs are {output_names}'''.format(
                    step=step, result=result, output_names=output_names
                )
            )

        if result.output_name in seen_outputs:
            raise DagsterInvariantViolationError(
                '''Core transform for {step.solid.name} returned an output
                {result.output_name} multiple times'''.format(
                    step=step, result=result
                )
            )

        seen_outputs.add(result.output_name)


def _execute_steps_core_loop(step, context, inputs):
    evaluated_inputs = {}
    # do runtime type checks of inputs versus step inputs
    for input_name, input_value in inputs.items():
        evaluated_inputs[input_name] = _get_evaluated_input(step, input_name, input_value)

    results = _compute_result_list(step, context, evaluated_inputs)

    _error_check_results(step, results)

    return [_create_step_result(step, result) for result in results]


def _create_step_result(step, result):
    check.inst_param(result, 'result', Result)

    step_output = step.step_output_named(result.output_name)

    try:
        coerced_value = step_output.runtime_type.coerce_runtime_value(result.value)
    except DagsterRuntimeCoercionError as e:
        raise DagsterInvariantViolationError(
            '''Solid {step.solid.name} output name {output_name} output {result.value}
            type failure: {error_msg}'''.format(
                step=step, result=result, error_msg=','.join(e.args), output_name=result.output_name
            )
        )

    return StepResult.success_result(
        step=step,
        tag=step.tag,
        success_data=StepSuccessData(output_name=result.output_name, value=coerced_value),
    )


def _get_evaluated_input(step, input_name, input_value):
    step_input = step.step_input_named(input_name)
    try:
        return step_input.runtime_type.coerce_runtime_value(input_value)
    except DagsterRuntimeCoercionError as evaluate_error:
        raise_from(
            DagsterTypeError(
                (
                    'Solid {step.solid.name} input {input_name} received value {input_value} '
                    'which does not pass the typecheck for Dagster type '
                    '{step_input.runtime_type.name}. Step {step.key}'
                ).format(
                    step=step, input_name=input_name, input_value=input_value, step_input=step_input
                )
            ),
            evaluate_error,
        )


def _compute_result_list(step, context, evaluated_inputs):
    error_str = 'Error occured during step {key}'.format(key=step.key)

    def_name = step.solid.definition.name

    with context.values({'solid': step.solid.name, 'solid_definition': def_name}):
        with _execution_step_error_boundary(context, step, error_str):
            gen = step.compute_fn(context, step, evaluated_inputs)

            if gen is None:
                check.invariant(not step.step_outputs)
                return

            results = list(gen)

        return results


@contextmanager
def _execution_step_error_boundary(context, step, msg, **kwargs):
    '''
    Wraps the execution of user-space code in an error boundary. This places a uniform
    policy around an user code invoked by the framework. This ensures that all user
    errors are wrapped in the SolidUserCodeExecutionError, and that the original stack
    trace of the user error is preserved, so that it can be reported without confusing
    framework code in the stack trace, if a tool author wishes to do so. This has
    been especially help in a notebooking context.
    '''
    check.inst_param(context, 'context', RuntimeExecutionContext)
    check.str_param(msg, 'msg')

    context.events.execution_plan_step_start(step.key)
    try:
        with time_execution_scope() as timer_result:
            yield

        context.events.execution_plan_step_success(step.key, timer_result.millis)
    except Exception as e:  # pylint: disable=W0703
        context.events.execution_plan_step_failure(step.key, sys.exc_info())

        stack_trace = get_formatted_stack_trace(e)
        context.error(str(e), stack_trace=stack_trace)

        if isinstance(e, DagsterError):
            raise e
        else:
            raise_from(
                DagsterUserCodeExecutionError(
                    msg.format(**kwargs), user_exception=e, original_exc_info=sys.exc_info()
                ),
                e,
            )
