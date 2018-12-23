from dagster import check

from dagster.core.definitions import (
    InputDefinition,
    Result,
    Solid,
)

from dagster.core.errors import DagsterInvariantViolationError

from .objects import (
    ExecutionPlanInfo,
    ExecutionStep,
    StepCreationInfo,
    StepOutput,
    StepOutputHandle,
    StepTag,
)

INPUT_THUNK_OUTPUT = 'input_thunk_output'


def create_input_thunk_compute_fn(value):
    def _fn(_context, _step, _inputs):
        yield Result(value, INPUT_THUNK_OUTPUT)

    return _fn


def _create_input_thunk_execution_step(info, solid, input_def):
    value = info.environment.solids[solid.name].inputs[input_def.name]
    return ExecutionStep(
        key=solid.name + '.' + input_def.name + '.input_thunk',
        step_inputs=[],
        step_outputs=[
            StepOutput.from_props(
                name=INPUT_THUNK_OUTPUT,
                dagster_type=input_def.dagster_type,
            )
        ],
        compute_fn=create_input_thunk_compute_fn(value),
        tag=StepTag.INPUT_THUNK,
        solid=solid,
    )


def create_input_thunk_execution_step(info, solid, input_def):
    check.inst_param(info, 'info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(input_def, 'input_def', InputDefinition)

    dependency_structure = info.pipeline.dependency_structure
    input_handle = solid.input_handle(input_def.name)

    if dependency_structure.has_dep(input_handle):
        raise DagsterInvariantViolationError(
            (
                'In pipeline {pipeline_name} solid {solid_name}, input {input_name} '
                'you have specified an input via config while also specifying '
                'a dependency. Either remove the dependency, specify a subdag '
                'to execute, or remove the inputs specification in the environment.'
            ).format(
                pipeline_name=info.pipeline.name,
                solid_name=solid.name,
                input_name=input_def.name,
            )
        )

    input_thunk = _create_input_thunk_execution_step(info, solid, input_def)
    return StepCreationInfo(
        input_thunk,
        StepOutputHandle(step_key=input_thunk.key, output_name=INPUT_THUNK_OUTPUT),
    )
