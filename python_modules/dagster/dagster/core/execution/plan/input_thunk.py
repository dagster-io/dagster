from dagster import check
from dagster.core.definitions import InputDefinition, Solid, SolidHandle
from dagster.core.errors import DagsterInvariantViolationError

from .objects import (
    ExecutionStep,
    SingleOutputStepCreationData,
    StepKind,
    StepOutput,
    StepOutputValue,
)

INPUT_THUNK_OUTPUT = 'input_thunk_output'


def _create_input_thunk_execution_step(pipeline_name, solid, input_def, input_spec, handle):
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(input_def, 'input_def', InputDefinition)
    check.opt_inst_param(handle, 'handle', SolidHandle)

    check.invariant(input_def.runtime_type.input_schema)

    def _fn(step_context, _inputs):
        value = input_def.runtime_type.input_schema.construct_from_config_value(
            step_context, input_spec
        )
        yield StepOutputValue(output_name=INPUT_THUNK_OUTPUT, value=value)

    return ExecutionStep(
        pipeline_name=pipeline_name,
        key_suffix='inputs.' + input_def.name + '.read',
        step_inputs=[],
        step_outputs=[
            StepOutput(name=INPUT_THUNK_OUTPUT, runtime_type=input_def.runtime_type, optional=False)
        ],
        compute_fn=_fn,
        kind=StepKind.INPUT_THUNK,
        solid_handle=handle,
        logging_tags={'input': input_def.name},
    )


def create_input_thunk_execution_step(
    pipeline_name, dependency_structure, solid, input_name, input_def, input_spec, handle
):
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(solid, 'solid', Solid)
    check.str_param(input_name, 'intput_name')
    check.inst_param(input_def, 'input_def', InputDefinition)

    input_handle = solid.input_handle(input_name)

    if dependency_structure.has_deps(input_handle):
        raise DagsterInvariantViolationError(
            (
                'In pipeline {pipeline_name} solid {solid_name}, input {input_name} '
                'you have specified an input via config while also specifying '
                'a dependency. Either remove the dependency, specify a subdag '
                'to execute, or remove the inputs specification in the environment.'
            ).format(pipeline_name=pipeline_name, solid_name=solid.name, input_name=input_name)
        )

    input_thunk = _create_input_thunk_execution_step(
        pipeline_name, solid, input_def, input_spec, handle
    )
    return SingleOutputStepCreationData(input_thunk, INPUT_THUNK_OUTPUT)
