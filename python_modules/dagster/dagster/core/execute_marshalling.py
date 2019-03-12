from collections import namedtuple

from dagster import check
from dagster.core.errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvalidSubplanInputNotFoundError,
    DagsterInvalidSubplanOutputNotFoundError,
    DagsterInvalidSubplanMissingInputError,
)

from .definitions import PipelineDefinition
from .execution_plan.intermediates_manager import StepOutputHandle

from .execution import (
    check_run_config_param,
    yield_pipeline_execution_context,
    create_execution_plan_core,
    invoke_executor_on_plan,
)


from .execution_context import InProcessExecutorConfig


class MarshalledOutput(namedtuple('_MarshalledOutput', 'output_name marshalling_key')):
    def __new__(cls, output_name, marshalling_key):
        return super(MarshalledOutput, cls).__new__(
            cls,
            check.str_param(output_name, 'output_name'),
            check.str_param(marshalling_key, 'marshalling_key'),
        )


MarshalledInput = namedtuple('MarshalledInput', 'input_name key')


class StepExecution(namedtuple('_StepExecution', 'step_key marshalled_inputs marshalled_outputs')):
    def __new__(cls, step_key, marshalled_inputs, marshalled_outputs):
        return super(StepExecution, cls).__new__(
            cls,
            check.str_param(step_key, 'step_key'),
            check.list_param(marshalled_inputs, 'marshalled_inputs', of_type=MarshalledInput),
            check.list_param(marshalled_outputs, 'marshalled_outputs', of_type=MarshalledOutput),
        )


def execute_marshalling(
    pipeline,
    step_keys,
    inputs_to_marshal=None,
    outputs_to_marshal=None,
    environment_dict=None,
    run_config=None,
):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.list_param(step_keys, 'step_keys', of_type=str)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check_run_config_param(run_config)

    check.param_invariant(
        isinstance(run_config.executor_config, InProcessExecutorConfig),
        'run_config',
        (
            'In order for this function to work properly you must provide an executor config: '
            'for now, you must use the InProcessExecutorConfig'
        ),
    )

    intermediates_manager = run_config.executor_config.inmem_intermediates_manager

    with yield_pipeline_execution_context(
        pipeline, environment_dict, run_config
    ) as pipeline_context:

        execution_plan = create_execution_plan_core(pipeline_context)

        do_error_checking(
            inputs_to_marshal, execution_plan, pipeline_context, step_keys, outputs_to_marshal
        )

        unmarshal_inputs(inputs_to_marshal, execution_plan, pipeline_context, intermediates_manager)

        for step_key in step_keys:
            step = execution_plan.get_step_by_key(step_key)
            for step_input in step.step_inputs:
                if step_input.prev_output_handle.step_key in step_keys:
                    # dep in subset, we're fine
                    continue

                if intermediates_manager.has_value(step_input.prev_output_handle):
                    # dep preset in intermediates manager
                    continue

                raise DagsterInvalidSubplanMissingInputError(
                    (
                        'You have specified a subset execution on pipeline {pipeline_name} '
                        'with step_keys {step_keys}. You have failed to provide the required input '
                        '{input_name} for step {step_key}.'
                    ).format(
                        pipeline_name=pipeline_context.pipeline_def.name,
                        step_keys=step_keys,
                        input_name=step_input.name,
                        step_key=step.key,
                    ),
                    pipeline_name=pipeline_context.pipeline_def.name,
                    step_keys=step_keys,
                    input_name=step_input.name,
                    step=step,
                )

        execution_plan = create_execution_plan_core(pipeline_context)

        events = list(
            invoke_executor_on_plan(
                pipeline_context, execution_plan=execution_plan, step_keys_to_execute=step_keys
            )
        )

        marshal_outputs(
            events, outputs_to_marshal, execution_plan, intermediates_manager, pipeline_context
        )

        return events


def do_error_checking(
    inputs_to_marshal, execution_plan, pipeline_context, step_keys, outputs_to_marshal
):
    if inputs_to_marshal:
        for step_key, input_dict in inputs_to_marshal.items():
            for input_name, _marshalling_key in input_dict.items():
                if not execution_plan.has_step(step_key):
                    raise DagsterExecutionStepNotFoundError(step_key=step_key)
                step = execution_plan.get_step_by_key(step_key)
                if not step.has_step_input(input_name):
                    raise DagsterInvalidSubplanInputNotFoundError(
                        'Input {input_name} on {step_key} does not exist.'.format(
                            input_name=input_name, step_key=step_key
                        ),
                        pipeline_name=pipeline_context.pipeline_def.name,
                        step_keys=step_keys,
                        input_name=input_name,
                        step=step,
                    )

    if outputs_to_marshal:
        for step_key, marshalled_outputs in outputs_to_marshal.items():
            if not execution_plan.has_step(step_key):
                raise DagsterExecutionStepNotFoundError(step_key=step_key)
            step = execution_plan.get_step_by_key(step_key)
            for marshalled_output in marshalled_outputs:
                if not step.has_step_output(marshalled_output.output_name):
                    raise DagsterInvalidSubplanOutputNotFoundError(
                        'Execution step {step_key} does not have output {output}'.format(
                            step_key=step_key, output=marshalled_output.output_name
                        ),
                        pipeline_name=pipeline_context.pipeline_def.name,
                        step_keys=step_keys,
                        step=step,
                        output_name=marshalled_output.output_name,
                    )


def marshal_outputs(
    events, outputs_to_marshal, execution_plan, intermediates_manager, pipeline_context
):
    if outputs_to_marshal:
        successful_outputs = set()
        for event in events:
            if event.is_successful_output:
                successful_outputs.add(
                    StepOutputHandle(event.step_key, event.step_output_data.output_name)
                )

        for step_key, marshalled_outputs in outputs_to_marshal.items():
            if not execution_plan.has_step(step_key):
                raise DagsterExecutionStepNotFoundError(step_key=step_key)
            step = execution_plan.get_step_by_key(step_key)
            for marshalled_output in marshalled_outputs:
                step_output = step.step_output_named(marshalled_output.output_name)
                step_output_handle = StepOutputHandle(step_key, marshalled_output.output_name)

                if step_output_handle not in successful_outputs:
                    continue

                output_value = intermediates_manager.get_value(step_output_handle)
                pipeline_context.persistence_strategy.write_value(
                    step_output.runtime_type.serialization_strategy,
                    marshalled_output.marshalling_key,
                    output_value,
                )


def unmarshal_inputs(inputs_to_marshal, execution_plan, pipeline_context, intermediates_manager):
    if inputs_to_marshal:
        for step_key, input_dict in inputs_to_marshal.items():
            for input_name, marshalling_key in input_dict.items():
                step = execution_plan.get_step_by_key(step_key)
                step_input = step.step_input_named(input_name)
                step_output_handle = step_input.prev_output_handle
                input_value = pipeline_context.persistence_strategy.read_value(
                    step_input.runtime_type.serialization_strategy, marshalling_key
                )
                intermediates_manager.set_value(step_output_handle, input_value)
