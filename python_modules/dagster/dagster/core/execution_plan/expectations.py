from dagster import check

from dagster.core.definitions import (
    ExpectationDefinition,
    ExpectationExecutionInfo,
    InputDefinition,
    OutputDefinition,
    Result,
    Solid,
)

from dagster.core.errors import DagsterExpectationFailedError

from .objects import (
    ExecutionPlanInfo,
    ExecutionStep,
    ExecutionValueSubplan,
    StepInput,
    StepOutput,
    StepOutputHandle,
    StepKind,
    StepBuilderState,
)

from .utility import create_joining_subplan

EXPECTATION_INPUT = 'expectation_input'
EXPECTATION_VALUE_OUTPUT = 'expectation_value'


def _create_expectation_lambda(solid, inout_def, expectation_def, internal_output_name):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(expectation_def, 'expectations_def', ExpectationDefinition)
    check.str_param(internal_output_name, 'internal_output_name')

    def _do_expectation(context, step, inputs):
        value = inputs[EXPECTATION_INPUT]
        info = ExpectationExecutionInfo(context, inout_def, solid, expectation_def)
        expt_result = expectation_def.expectation_fn(info, value)
        if expt_result.success:
            context.debug(
                'Expectation {key} succeeded on {value}.'.format(key=step.key, value=value)
            )
            yield Result(output_name=internal_output_name, value=inputs[EXPECTATION_INPUT])
        else:
            context.debug('Expectation {key} failed on {value}.'.format(key=step.key, value=value))
            raise DagsterExpectationFailedError(info, value)

    return _do_expectation


def create_expectations_subplan(state, solid, inout_def, prev_step_output_handle, kind):
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(kind, 'kind', StepKind)

    input_expect_steps = []
    for expectation_def in inout_def.expectations:
        with state.push_tags(expectation=expectation_def.name):
            expect_step = create_expectation_step(
                state=state,
                solid=solid,
                expectation_def=expectation_def,
                key='{solid}.{desc_key}.{inout_name}.expectation.{expectation_name}'.format(
                    solid=solid.name,
                    desc_key=inout_def.descriptive_key,
                    inout_name=inout_def.name,
                    expectation_name=expectation_def.name,
                ),
                kind=kind,
                prev_step_output_handle=prev_step_output_handle,
                inout_def=inout_def,
            )
            input_expect_steps.append(expect_step)

    return create_joining_subplan(
        state,
        solid,
        '{solid}.{desc_key}.{inout_name}.expectations.join'.format(
            solid=solid.name, desc_key=inout_def.descriptive_key, inout_name=inout_def.name
        ),
        input_expect_steps,
        EXPECTATION_VALUE_OUTPUT,
    )


def create_expectation_step(
    state, solid, expectation_def, key, kind, prev_step_output_handle, inout_def
):
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(expectation_def, 'input_expct_def', ExpectationDefinition)
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))

    value_type = inout_def.runtime_type

    return ExecutionStep(
        key=key,
        step_inputs=[
            StepInput(
                name=EXPECTATION_INPUT,
                runtime_type=value_type,
                prev_output_handle=prev_step_output_handle,
            )
        ],
        step_outputs=[StepOutput(name=EXPECTATION_VALUE_OUTPUT, runtime_type=value_type)],
        compute_fn=_create_expectation_lambda(
            solid, inout_def, expectation_def, EXPECTATION_VALUE_OUTPUT
        ),
        kind=kind,
        solid=solid,
        tags=state.get_tags(),
    )


def decorate_with_expectations(execution_info, state, solid, transform_step, output_def):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(transform_step, 'transform_step', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    if execution_info.environment.expectations.evaluate and output_def.expectations:
        return create_expectations_subplan(
            state,
            solid,
            output_def,
            StepOutputHandle(transform_step, output_def.name),
            kind=StepKind.OUTPUT_EXPECTATION,
        )
    else:
        return ExecutionValueSubplan.empty(StepOutputHandle(transform_step, output_def.name))
