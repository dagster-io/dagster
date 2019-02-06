from dagster import check

from dagster.core.definitions import Solid, OutputDefinition, Result
from dagster.core.types.sequence import Sequence, SEQUENCE_RUNTIME_TYPE

from .objects import (
    CreateExecutionPlanInfo,
    ExecutionValueSubplan,
    ExecutionStep,
    ExecutionPlan,
    PlanBuilder,
    StepInput,
    StepOutput,
    StepResult,
    StepOutputHandle,
    StepSuccessData,
    StepKind,
)

from .simple_engine import execute_plan_core


SUBPLAN_EXECUTOR_SEQUENCE_INPUT = 'sequence_input'
SUBPLAN_EXECUTOR_SEQUENCE_OUTPUT = 'sequence_output'

SUBPLAN_BEGIN_SENTINEL = StepOutputHandle.subplan_begin_sentinel()


def _create_output_sequence(context, step, input_sequence, subplan):
    def _produce_output_sequence():
        for item in input_sequence.items():
            step_result = StepResult.success_result(step, step.kind, StepSuccessData('item', item))

            # Inject the single item from the parent sequence as a result. This way the subplan
            # can use execute_plan_core unaltered.
            intermediate_results = {SUBPLAN_BEGIN_SENTINEL: step_result}
            for inner_result in execute_plan_core(
                context,
                subplan,
                # TODO error handling?
                throw_on_user_error=False,
                intermediate_results=intermediate_results,
            ):
                # will need to check what output this is?
                # what to do on error?
                check.invariant(
                    inner_result.success, 'Errors not handled in subplan execution for the moment'
                )
                yield inner_result.success_data.value

    return Sequence(_produce_output_sequence)


def _create_subplan_executor_compute(subplan):
    check.inst_param(subplan, 'subplan', ExecutionPlan)

    def _do_subplan_executor_compute(context, step, inputs):
        input_sequence = inputs[SUBPLAN_EXECUTOR_SEQUENCE_INPUT]

        yield Result(
            _create_output_sequence(context, step, input_sequence, subplan),
            SUBPLAN_EXECUTOR_SEQUENCE_OUTPUT,
        )

    return _do_subplan_executor_compute


def create_subplan_executor_step(
    execution_info, plan_builder, solid, output_def, value_subplan, subplan_id
):
    check.inst_param(execution_info, 'execution_info', CreateExecutionPlanInfo)
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
    # The solid in question in here is the one with the output the caused the
    # subplan to be created.
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)
    check.inst_param(value_subplan, 'value_subplan', ExecutionValueSubplan)
    check.str_param(subplan_id, 'sublan_id')

    check.invariant(output_def.runtime_type is SEQUENCE_RUNTIME_TYPE)

    subplan = plan_builder.get_existing_plan(subplan_id)

    return ExecutionStep(
        key='plan.{}.executor'.format(subplan_id),
        step_inputs=[
            StepInput(
                SUBPLAN_EXECUTOR_SEQUENCE_INPUT,
                SEQUENCE_RUNTIME_TYPE,
                value_subplan.terminal_step_output_handle,
            )
        ],
        step_outputs=[StepOutput(SUBPLAN_EXECUTOR_SEQUENCE_OUTPUT, SEQUENCE_RUNTIME_TYPE)],
        compute_fn=_create_subplan_executor_compute(subplan),
        kind=StepKind.SUBPLAN_EXECUTOR,
        solid=solid,
        subplan=subplan,
        tags=plan_builder.get_tags(),
    )


def decorate_with_subplan_executors(execution_info, plan_builder, solid, output_def, value_subplan):
    dep_structure = execution_info.pipeline.dependency_structure
    solid_output_handle = solid.output_handle(output_def.name)
    subplan_executors = []
    for solid_input_handle in dep_structure.input_handles_depending_on_output(solid_output_handle):
        dep_def = dep_structure.get_dep_def(solid_input_handle)
        if dep_def.is_fanout:
            subplan_id = execution_info.plan_id_for_solid(solid_input_handle.solid)
            subplan_executor_step = create_subplan_executor_step(
                execution_info, plan_builder, solid, output_def, value_subplan, subplan_id
            )
            subplan_executors.append(subplan_executor_step)

            plan_builder.set_step_output_handle_for_plan_id(
                subplan_executor_step.subplan.plan_id,
                StepOutputHandle.create(subplan_executor_step, SUBPLAN_EXECUTOR_SEQUENCE_OUTPUT),
            )

    return ExecutionValueSubplan(
        value_subplan.steps + subplan_executors, value_subplan.terminal_step_output_handle
    )
