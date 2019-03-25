from contextlib import contextmanager
import sys

from future.utils import raise_from
import six

from dagster import check

from dagster.utils.logging import get_formatted_stack_trace

from dagster.utils.timing import time_execution_scope

from dagster.core.errors import (
    DagsterError,
    DagsterInvariantViolationError,
    DagsterRuntimeCoercionError,
    DagsterExecutionStepExecutionError,
    DagsterTypeError,
)

from dagster.core.execution_context import (
    ExecutorConfig,
    SystemPipelineExecutionContext,
    SystemStepExecutionContext,
)

from dagster.core.intermediates_manager import IntermediatesManager

from dagster.utils.error import serializable_error_info_from_exc_info

from .objects import (
    ExecutionPlan,
    ExecutionStep,
    ExecutionStepEvent,
    StepOutputHandle,
    StepOutputValue,
    StepOutputData,
    StepFailureData,
)


def start_inprocess_executor(
    pipeline_context, execution_plan, intermediates_manager, step_keys_to_execute=None
):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(intermediates_manager, 'intermediates_manager', IntermediatesManager)
    check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

    step_key_set = None if step_keys_to_execute is None else set(step_keys_to_execute)

    check.param_invariant(
        isinstance(pipeline_context.executor_config, ExecutorConfig),
        'pipeline_context',
        'Expected executor_config to be ExecutorConfig got {}'.format(
            pipeline_context.executor_config
        ),
    )

    step_levels = execution_plan.topological_step_levels()

    # It would be good to implement a reference tracking algorithm here so we could
    # garbage collection results that are no longer needed by any steps
    # https://github.com/dagster-io/dagster/issues/811

    for step_level in step_levels:
        for step in step_level:
            if step_key_set and step.key not in step_key_set:
                continue

            step_context = pipeline_context.for_step(step)

            if not intermediates_manager.all_inputs_covered(step_context, step):
                expected_outputs = [ni.prev_output_handle for ni in step.step_inputs]

                step_context.log.info(
                    (
                        'Not all inputs covered for {step}. Not executing. Output need for '
                        'inputs {expected_outputs}'
                    ).format(expected_outputs=expected_outputs, step=step.key)
                )
                continue

            input_values = _create_input_values(step_context, intermediates_manager)

            for step_event in check.generator(
                execute_step_in_memory(step_context, input_values, intermediates_manager)
            ):
                check.inst(step_event, ExecutionStepEvent)
                if (
                    pipeline_context.executor_config.throw_on_user_error
                    and step_event.is_step_failure
                ):
                    step_event.reraise_user_error()

                yield step_event


def _create_input_values(step_context, intermediates_manager):
    check.inst_param(intermediates_manager, 'intermediates_manager', IntermediatesManager)

    step = step_context.step

    input_values = {}
    for step_input in step.step_inputs:
        prev_output_handle = step_input.prev_output_handle
        input_value = intermediates_manager.get_intermediate(
            step_context, step_input.runtime_type, prev_output_handle
        )
        input_values[step_input.name] = input_value
    return input_values


def execute_step_in_memory(step_context, inputs, intermediates_manager):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.dict_param(inputs, 'inputs', key_type=str)
    check.inst_param(intermediates_manager, 'intermediates_manager', IntermediatesManager)

    try:
        for step_event in check.generator(
            _execute_steps_core_loop(step_context, inputs, intermediates_manager)
        ):
            step_context.log.info(
                'Step {step} emitted {value} for output {output}'.format(
                    step=step_context.step.key,
                    value=step_event.step_output_data.value_repr,
                    output=step_event.step_output_data.output_name,
                )
            )
            yield step_event
    except DagsterError as dagster_error:
        step_context.log.error(str(dagster_error))

        exc_info = (
            # pylint does not know original_exc_info exists is is_user_code_error is true
            # pylint: disable=no-member
            dagster_error.original_exc_info
            if dagster_error.is_user_code_error
            else sys.exc_info()
        )

        if step_context.executor_config.throw_on_user_error:
            six.reraise(*exc_info)

        error_info = serializable_error_info_from_exc_info(exc_info)

        yield ExecutionStepEvent.step_failure_event(
            step_context=step_context,
            step_failure_data=StepFailureData(
                error_message=error_info.message,
                error_cls_name=exc_info[0].__name__,  # 0 is the exception type
                stack=error_info.stack,
            ),
        )
        return


def _error_check_step_output_values(step, step_output_values):
    check.inst_param(step, 'step', ExecutionStep)
    check.generator_param(step_output_values, 'step_output_values')

    output_names = list([output_def.name for output_def in step.step_outputs])
    seen_outputs = set()
    for step_output_value in step_output_values:
        if not step.has_step_output(step_output_value.output_name):
            raise DagsterInvariantViolationError(
                'Core transform for solid "{step.solid.name}" returned an output '
                '"{step_output_value.output_name}" that does not exist. The available '
                'outputs are {output_names}'.format(
                    step=step, step_output_value=step_output_value, output_names=output_names
                )
            )

        if step_output_value.output_name in seen_outputs:
            raise DagsterInvariantViolationError(
                'Core transform for solid "{step.solid.name}" returned an output '
                '"{step_output_value.output_name}" multiple times'.format(
                    step=step, step_output_value=step_output_value
                )
            )

        yield step_output_value
        seen_outputs.add(step_output_value.output_name)

    for step_output_def in step.step_outputs:
        if not step_output_def.name in seen_outputs and not step_output_def.optional:
            raise DagsterInvariantViolationError(
                'Core transform for solid "{step.solid.name}" did not return an output '
                'for non-optional output "{step_output_def.name}"'.format(
                    step=step, step_output_def=step_output_def
                )
            )


def _execute_steps_core_loop(step_context, inputs, intermediates_manager):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.dict_param(inputs, 'inputs', key_type=str)
    check.inst_param(intermediates_manager, 'intermediates_manager', IntermediatesManager)

    evaluated_inputs = {}
    # do runtime type checks of inputs versus step inputs
    for input_name, input_value in inputs.items():
        evaluated_inputs[input_name] = _get_evaluated_input(
            step_context.step, input_name, input_value
        )

    step = step_context.step
    step_context.events.execution_plan_step_start(step.key)

    try:
        with time_execution_scope() as timer_result:
            step_output_value_iterator = check.generator(
                _iterate_step_output_values_within_boundary(step_context, evaluated_inputs)
            )

        for step_output_value in check.generator(
            _error_check_step_output_values(step_context.step, step_output_value_iterator)
        ):

            yield _create_step_event(step_context, step_output_value, intermediates_manager)

        step_context.events.execution_plan_step_success(step.key, timer_result.millis)

    except DagsterError as e:
        # The step compute_fn and output error checking both raise exceptions. Catch
        # and re-throw these to ensure that the step is always marked as failed.
        step_context.events.execution_plan_step_failure(step.key, sys.exc_info())
        stack_trace = get_formatted_stack_trace(e)
        step_context.log.error(str(e), stack_trace=stack_trace)
        six.reraise(*sys.exc_info())


def _create_step_event(step_context, step_output_value, intermediates_manager):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.inst_param(step_output_value, 'step_output_value', StepOutputValue)
    check.inst_param(intermediates_manager, 'intermediates_manager', IntermediatesManager)

    step = step_context.step
    step_output = step.step_output_named(step_output_value.output_name)

    try:
        value = step_output.runtime_type.coerce_runtime_value(step_output_value.value)
        step_output_handle = StepOutputHandle.from_step(
            step=step, output_name=step_output_value.output_name
        )

        object_key = intermediates_manager.set_intermediate(
            context=step_context,
            runtime_type=step_output.runtime_type,
            step_output_handle=step_output_handle,
            value=value,
        )

        step_context.events.execution_plan_step_output(
            step_key=step.key,
            output_name=step_output_handle.output_name,
            storage_mode=intermediates_manager.storage_mode.value,
            storage_object_id=object_key,
        )

        return ExecutionStepEvent.step_output_event(
            step_context=step_context,
            step_output_data=StepOutputData(
                step_output_handle=step_output_handle,
                value_repr=repr(value),
                intermediates_manager=intermediates_manager,
            ),
        )
    except DagsterRuntimeCoercionError as e:
        raise DagsterInvariantViolationError(
            (
                'Solid {step.solid.name} output name {output_name} output '
                '{step_output_value.value} type failure: {error_msg}.'
            ).format(
                step=step,
                step_output_value=step_output_value,
                error_msg=','.join(e.args),
                output_name=step_output_value.output_name,
            )
        )


def _get_evaluated_input(step, input_name, input_value):
    check.inst_param(step, 'step', ExecutionStep)
    check.str_param(input_name, 'input_name')

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


def _iterate_step_output_values_within_boundary(step_context, evaluated_inputs):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.dict_param(evaluated_inputs, 'evaluated_inputs', key_type=str)

    error_str = 'Error occured during step {key}'.format(key=step_context.step.key)
    with _execution_step_error_boundary(step_context, error_str):
        gen = check.opt_generator(step_context.step.compute_fn(step_context, evaluated_inputs))

        if gen is not None:
            for step_output_value in gen:
                yield step_output_value


@contextmanager
def _execution_step_error_boundary(step_context, msg, **kwargs):
    '''
    Wraps the execution of user-space code in an error boundary. This places a uniform
    policy around an user code invoked by the framework. This ensures that all user
    errors are wrapped in the SolidUserCodeExecutionError, and that the original stack
    trace of the user error is preserved, so that it can be reported without confusing
    framework code in the stack trace, if a tool author wishes to do so. This has
    been especially help in a notebooking context.
    '''
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.str_param(msg, 'msg')

    try:
        yield
    except Exception as e:  # pylint: disable=W0703
        step_context.log.error('Inner error in step execution ' + str(e))
        if isinstance(e, DagsterError):
            raise e
        else:
            raise_from(
                DagsterExecutionStepExecutionError(
                    msg.format(**kwargs), user_exception=e, original_exc_info=sys.exc_info()
                ),
                e,
            )
