from dagster import check

from dagster.core.definitions import (
    Solid,
    InputDefinition,
    OutputDefinition,
    Result,
    ExpectationDefinition,
    ExpectationExecutionInfo,
)

from dagster.core.errors import DagsterExpectationFailedError

from .objects import (
    ExecutionPlanInfo,
    ExecutionStep,
    ExecutionSubPlan,
    StepInput,
    StepOutput,
    StepOutputHandle,
    StepTag,
)

EXPECTATION_INPUT = 'expectation_input'
EXPECTATION_VALUE_OUTPUT = 'expectation_value'

JOIN_OUTPUT = 'join_output'


def __join_lambda(_context, _step, inputs):
    yield Result(output_name=JOIN_OUTPUT, value=list(inputs.values())[0])


# Move to generalized utility file
def _create_join_step(solid, step_key, prev_steps, prev_output_name):
    check.inst_param(solid, 'solid', Solid)
    check.str_param(step_key, 'step_key')
    check.list_param(prev_steps, 'prev_steps', of_type=ExecutionStep)
    check.invariant(len(prev_steps) > 0)
    check.str_param(prev_output_name, 'output_name')

    step_inputs = []
    seen_dagster_type = None
    for prev_step in prev_steps:
        prev_step_output = prev_step.step_output_named(prev_output_name)

        if seen_dagster_type is None:
            seen_dagster_type = prev_step_output.dagster_type
        else:
            check.invariant(seen_dagster_type == prev_step_output.dagster_type)

        output_handle = StepOutputHandle(prev_step, prev_output_name)

        step_inputs.append(StepInput(prev_step.key, prev_step_output.dagster_type, output_handle))

    return ExecutionStep(
        key=step_key,
        step_inputs=step_inputs,
        step_outputs=[StepOutput(JOIN_OUTPUT, seen_dagster_type)],
        compute_fn=__join_lambda,
        tag=StepTag.JOIN,
        solid=solid,
    )


def _create_expectation_lambda(solid, inout_def, expectation_def, internal_output_name):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(expectation_def, 'expectations_def', ExpectationDefinition)
    check.str_param(internal_output_name, 'internal_output_name')

    def _do_expectation(context, step, inputs):
        with context.values(
            {
                inout_def.descriptive_key: inout_def.name,
                'expectation': expectation_def.name
            }
        ):
            value = inputs[EXPECTATION_INPUT]
            info = ExpectationExecutionInfo(context, inout_def, solid, expectation_def)
            expt_result = expectation_def.expectation_fn(info, value)
            if expt_result.success:
                context.debug(
                    'Expectation {key} succeeded on {value}.'.format(
                        key=step.key,
                        value=value,
                    )
                )
                yield Result(output_name=internal_output_name, value=inputs[EXPECTATION_INPUT])
            else:
                context.debug(
                    'Expectation {key} failed on {value}.'.format(key=step.key, value=value)
                )
                raise DagsterExpectationFailedError(info, value)

    return _do_expectation


def create_expectations_subplan(solid, inout_def, prev_step_output_handle, tag):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(tag, 'tag', StepTag)

    steps = []
    input_expect_steps = []
    for expectation_def in inout_def.expectations:
        expect_step = create_expectation_step(
            solid=solid,
            expectation_def=expectation_def,
            key='{solid.name}.{inout_def.name}.expectation.{expectation_def.name}'.format(
                solid=solid,
                inout_def=inout_def,
                expectation_def=expectation_def,
            ),
            tag=tag,
            prev_step_output_handle=prev_step_output_handle,
            inout_def=inout_def,
        )
        input_expect_steps.append(expect_step)
        steps.append(expect_step)

    join_step = _create_join_step(
        solid,
        '{solid}.{desc_key}.{name}.expectations.join'.format(
            solid=solid.name,
            desc_key=inout_def.descriptive_key,
            name=inout_def.name,
        ),
        input_expect_steps,
        EXPECTATION_VALUE_OUTPUT,
    )

    output_name = join_step.step_outputs[0].name
    return ExecutionSubPlan(
        steps + [join_step],
        StepOutputHandle(join_step, output_name),
    )


def create_expectation_step(
    solid,
    expectation_def,
    key,
    tag,
    prev_step_output_handle,
    inout_def,
):

    check.inst_param(solid, 'solid', Solid)
    check.inst_param(expectation_def, 'input_expct_def', ExpectationDefinition)
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))

    value_type = inout_def.dagster_type

    return ExecutionStep(
        key=key,
        step_inputs=[
            StepInput(
                name=EXPECTATION_INPUT,
                dagster_type=value_type,
                prev_output_handle=prev_step_output_handle,
            )
        ],
        step_outputs=[
            StepOutput(name=EXPECTATION_VALUE_OUTPUT, dagster_type=value_type),
        ],
        compute_fn=_create_expectation_lambda(
            solid,
            inout_def,
            expectation_def,
            EXPECTATION_VALUE_OUTPUT,
        ),
        tag=tag,
        solid=solid,
    )


def decorate_with_expectations(execution_info, solid, transform_step, output_def):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(transform_step, 'transform_step', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    if execution_info.environment.expectations.evaluate and output_def.expectations:
        return create_expectations_subplan(
            solid,
            output_def,
            StepOutputHandle(transform_step, output_def.name),
            tag=StepTag.OUTPUT_EXPECTATION
        )
    else:
        return ExecutionSubPlan(
            steps=[],
            terminal_step_output_handle=StepOutputHandle(
                transform_step,
                output_def.name,
            ),
        )
