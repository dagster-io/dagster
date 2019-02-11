from dagster import check

from dagster.core.execution_context import StepExecutionContext, PipelineExecutionContext

from dagster.core.definitions import ExpectationDefinition, InputDefinition, OutputDefinition, Solid

from dagster.core.errors import DagsterExpectationFailedError

from .objects import (
    ExecutionStep,
    ExecutionValueSubplan,
    StepInput,
    StepOutput,
    StepOutputHandle,
    StepOutputValue,
    StepKind,
    PlanBuilder,
)

from .utility import create_joining_subplan

EXPECTATION_INPUT = 'expectation_input'
EXPECTATION_VALUE_OUTPUT = 'expectation_value'


def _create_expectation_lambda(solid, inout_def, expectation_def, internal_output_name):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(expectation_def, 'expectations_def', ExpectationDefinition)
    check.str_param(internal_output_name, 'internal_output_name')

    def _do_expectation(step_context, inputs):
        check.inst_param(step_context, 'step_context', StepExecutionContext)
        value = inputs[EXPECTATION_INPUT]
        expectation_context = step_context.for_expectation(inout_def, expectation_def)
        expt_result = expectation_def.expectation_fn(step_context, value)
        if expt_result.success:
            expectation_context.log.debug(
                'Expectation {key} succeeded on {value}.'.format(
                    key=step_context.step.key, value=value
                )
            )
            yield StepOutputValue(output_name=internal_output_name, value=inputs[EXPECTATION_INPUT])
        else:
            expectation_context.log.debug(
                'Expectation {key} failed on {value}.'.format(
                    key=step_context.step.key, value=value
                )
            )
            raise DagsterExpectationFailedError(expectation_context, value)

    return _do_expectation


def create_expectations_subplan(plan_builder, solid, inout_def, prev_step_output_handle, kind):
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(kind, 'kind', StepKind)

    input_expect_steps = []
    for expectation_def in inout_def.expectations:
        with plan_builder.push_tags(expectation=expectation_def.name):
            expect_step = create_expectation_step(
                plan_builder=plan_builder,
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
        plan_builder,
        solid,
        '{solid}.{desc_key}.{inout_name}.expectations.join'.format(
            solid=solid.name, desc_key=inout_def.descriptive_key, inout_name=inout_def.name
        ),
        input_expect_steps,
        EXPECTATION_VALUE_OUTPUT,
    )


def create_expectation_step(
    plan_builder, solid, expectation_def, key, kind, prev_step_output_handle, inout_def
):
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
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
        tags=plan_builder.get_tags(),
    )


def decorate_with_expectations(pipeline_context, plan_builder, solid, transform_step, output_def):
    check.inst_param(pipeline_context, 'pipeline_context', PipelineExecutionContext)
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(transform_step, 'transform_step', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    if pipeline_context.environment_config.expectations.evaluate and output_def.expectations:
        return create_expectations_subplan(
            plan_builder,
            solid,
            output_def,
            StepOutputHandle(transform_step, output_def.name),
            kind=StepKind.OUTPUT_EXPECTATION,
        )
    else:
        return ExecutionValueSubplan.empty(StepOutputHandle(transform_step, output_def.name))
