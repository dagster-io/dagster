import sys

from future.utils import raise_from

from dagster import check

from dagster.utils.timing import time_execution_scope

from dagster.core.errors import (
    DagsterError,
    DagsterInvariantViolationError,
    DagsterRuntimeCoercionError,
    DagsterExecutionStepExecutionError,
    DagsterTypeError,
    DagsterStepOutputNotFoundError,
    user_code_error_boundary,
)

from dagster.core.execution_context import (
    ExecutorConfig,
    SystemPipelineExecutionContext,
    SystemStepExecutionContext,
)

from dagster.core.definitions import Materialization, ExpectationResult

from dagster.core.events import DagsterEvent, DagsterEventType

from dagster.core.intermediates_manager import IntermediatesManager

from dagster.utils.error import serializable_error_info_from_exc_info

from dagster.core.execution_plan.objects import (
    ExecutionStep,
    StepOutputHandle,
    StepOutputValue,
    StepOutputData,
    StepFailureData,
    StepSuccessData,
)

from dagster.core.execution_plan.plan import ExecutionPlan

from .engine_base import BaseEngine


class InProcessEngine(BaseEngine):  # pylint: disable=no-init
    @staticmethod
    def execute(pipeline_context, execution_plan, step_keys_to_execute=None):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        step_key_set = None if step_keys_to_execute is None else set(step_keys_to_execute)

        check.param_invariant(
            isinstance(pipeline_context.executor_config, ExecutorConfig),
            'pipeline_context',
            'Expected executor_config to be ExecutorConfig got {}'.format(
                pipeline_context.executor_config
            ),
        )

        failed_or_skipped_steps = set()

        step_levels = execution_plan.topological_step_levels()

        intermediates_manager = pipeline_context.intermediates_manager

        # It would be good to implement a reference tracking algorithm here so we could
        # garbage collection results that are no longer needed by any steps
        # https://github.com/dagster-io/dagster/issues/811

        for step_level in step_levels:
            for step in step_level:
                if step_key_set and step.key not in step_key_set:
                    continue

                step_context = pipeline_context.for_step(step)

                failed_inputs = [
                    step_input.prev_output_handle.step_key
                    for step_input in step.step_inputs
                    if step_input.prev_output_handle.step_key in failed_or_skipped_steps
                ]
                if failed_inputs:
                    step_context.log.info(
                        'Dependencies for step {step} failed: {failed_inputs}. Not executing.'.format(
                            step=step.key, failed_inputs=failed_inputs
                        )
                    )
                    failed_or_skipped_steps.add(step.key)
                    yield DagsterEvent.step_skipped_event(step_context)
                    continue

                uncovered_inputs = intermediates_manager.uncovered_inputs(step_context, step)
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
                    failed_or_skipped_steps.add(step.key)
                    yield DagsterEvent.step_skipped_event(step_context)
                    continue

                input_values = _create_input_values(step_context, intermediates_manager)

                for step_event in check.generator(
                    execute_step_in_memory(step_context, input_values, intermediates_manager)
                ):
                    check.inst(step_event, DagsterEvent)
                    if step_event.is_step_failure:
                        failed_or_skipped_steps.add(step.key)

                    yield step_event


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


def _create_input_values(step_context, intermediates_manager):
    check.inst_param(intermediates_manager, 'intermediates_manager', IntermediatesManager)

    step = step_context.step

    input_values = {}
    for step_input in step.step_inputs:
        if step_input.runtime_type.is_nothing:
            continue

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
            if step_event.event_type is DagsterEventType.STEP_OUTPUT:
                step_context.log.info(
                    'Step {step} emitted {value} for output {output}'.format(
                        step=step_context.step.key,
                        value=step_event.step_output_data.value_repr,
                        output=step_event.step_output_data.output_name,
                    )
                )
            yield step_event
    except DagsterError as dagster_error:
        user_facing_exc_info = (
            # pylint does not know original_exc_info exists is is_user_code_error is true
            # pylint: disable=no-member
            dagster_error.original_exc_info
            if dagster_error.is_user_code_error
            else sys.exc_info()
        )

        error_info = serializable_error_info_from_exc_info(user_facing_exc_info)

        yield DagsterEvent.step_failure_event(
            step_context=step_context, step_failure_data=StepFailureData(error=error_info)
        )

        if step_context.executor_config.raise_on_error:
            raise dagster_error

        return
    except:
        error_info = serializable_error_info_from_exc_info(sys.exc_info())
        yield DagsterEvent.step_failure_event(
            step_context=step_context, step_failure_data=StepFailureData(error=error_info)
        )
        raise


def _error_check_step_outputs(step, step_output_iter):
    check.inst_param(step, 'step', ExecutionStep)
    check.generator_param(step_output_iter, 'step_output_iter')

    output_names = list([output_def.name for output_def in step.step_outputs])
    seen_outputs = set()

    for step_output in step_output_iter:
        if not isinstance(step_output, StepOutputValue):
            yield step_output
            continue

        # do additional processing on StepOutputValues
        step_output_value = step_output
        if not step.has_step_output(step_output_value.output_name):
            raise DagsterInvariantViolationError(
                'Core transform for solid "{step.solid_handle.name}" returned an output '
                '"{step_output_value.output_name}" that does not exist. The available '
                'outputs are {output_names}'.format(
                    step=step, step_output_value=step_output_value, output_names=output_names
                )
            )

        if step_output_value.output_name in seen_outputs:
            raise DagsterInvariantViolationError(
                'Core transform for solid "{step.solid_handle.name}" returned an output '
                '"{step_output_value.output_name}" multiple times'.format(
                    step=step, step_output_value=step_output_value
                )
            )

        yield step_output_value
        seen_outputs.add(step_output_value.output_name)

    for step_output_def in step.step_outputs:
        if not step_output_def.name in seen_outputs and not step_output_def.optional:
            raise DagsterStepOutputNotFoundError(
                'Core transform for solid "{step.solid_handle.name}" did not return an output '
                'for non-optional output "{step_output_def.name}"'.format(
                    step=step, step_output_def=step_output_def
                ),
                step_key=step.key,
                output_name=step_output_def.name,
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

    yield DagsterEvent.step_start_event(step_context)

    with time_execution_scope() as timer_result:
        step_output_iterator = check.generator(
            _iterate_step_outputs_within_boundary(step_context, evaluated_inputs)
        )
    for step_output in check.generator(
        _error_check_step_outputs(step_context.step, step_output_iterator)
    ):

        if isinstance(step_output, StepOutputValue):
            yield _create_step_output_event(step_context, step_output, intermediates_manager)
        elif isinstance(step_output, Materialization):
            yield DagsterEvent.step_materialization(step_context, step_output)
        elif isinstance(step_output, ExpectationResult):
            yield DagsterEvent.step_expectation_result(step_context, step_output)
        else:
            check.failed(
                'Unexpected step_output {step_output}, should have been caught earlier'.format(
                    step_output=step_output
                )
            )

    yield DagsterEvent.step_success_event(
        step_context, StepSuccessData(duration_ms=timer_result.millis)
    )


def _create_step_output_event(step_context, step_output_value, intermediates_manager):
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

        return DagsterEvent.step_output_event(
            step_context=step_context,
            step_output_data=StepOutputData(
                step_output_handle=step_output_handle,
                value_repr=repr(value),
                intermediate_materialization=Materialization(path=object_key)
                if object_key
                else None,
            ),
        )
    except DagsterRuntimeCoercionError as e:
        raise DagsterInvariantViolationError(
            (
                'In solid "{step.solid_handle.name}" the output "{output_name}" returned '
                'an invalid type: {error_msg}.'
            ).format(
                step=step, error_msg=','.join(e.args), output_name=step_output_value.output_name
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
                    'In solid "{step.solid_handle.name}" the input "{input_name}" received value {input_value} '
                    'of Python type {input_type} which does not pass the typecheck for '
                    'Dagster type {step_input.runtime_type.name}. Step {step.key}.'
                ).format(
                    step=step,
                    input_name=input_name,
                    input_value=input_value,
                    input_type=type(input_value),
                    step_input=step_input,
                )
            ),
            evaluate_error,
        )


def _iterate_step_outputs_within_boundary(step_context, evaluated_inputs):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.dict_param(evaluated_inputs, 'evaluated_inputs', key_type=str)

    error_str = '''Error occured during the execution of step:
    step key: "{key}"
    solid instance: "{solid}"
    solid definition: "{solid_def}"
    '''.format(
        key=step_context.step.key,
        solid_def=step_context.solid_def.name,
        solid=step_context.solid.name,
    )

    with user_code_error_boundary(
        DagsterExecutionStepExecutionError,
        error_str,
        step_key=step_context.step.key,
        solid_def_name=step_context.solid_def.name,
        solid_name=step_context.solid.name,
    ):
        gen = check.opt_generator(step_context.step.compute_fn(step_context, evaluated_inputs))

        if gen is not None:
            for step_output in gen:
                yield step_output
