from dagster import check

from dagster.core.execution_context import PipelineExecutionContext
from dagster.core.definitions import InputDefinition, Solid

from dagster.core.errors import DagsterInvariantViolationError

from .objects import ExecutionStep, StepOutput, StepOutputHandle, StepOutputValue, StepKind

INPUT_THUNK_OUTPUT = 'input_thunk_output'


def _create_input_thunk_execution_step(pipeline_context, solid, input_def, input_spec):
    check.inst_param(pipeline_context, 'pipeline_context', PipelineExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(input_def, 'input_def', InputDefinition)

    check.invariant(input_def.runtime_type.input_schema)

    def _fn(_step_context, _inputs):
        value = input_def.runtime_type.input_schema.construct_from_config_value(input_spec)
        yield StepOutputValue(output_name=INPUT_THUNK_OUTPUT, value=value)

    return ExecutionStep(
        pipeline_context=pipeline_context,
        key=solid.name + '.' + input_def.name + '.input_thunk',
        step_inputs=[],
        step_outputs=[StepOutput(name=INPUT_THUNK_OUTPUT, runtime_type=input_def.runtime_type)],
        compute_fn=_fn,
        kind=StepKind.INPUT_THUNK,
        solid=solid,
        tags={'input': input_def.name},
    )


def create_input_thunk_execution_step(pipeline_context, solid, input_def, input_spec):
    check.inst_param(pipeline_context, 'pipeline_context', PipelineExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(input_def, 'input_def', InputDefinition)

    dependency_structure = pipeline_context.pipeline_def.dependency_structure
    input_handle = solid.input_handle(input_def.name)

    if dependency_structure.has_dep(input_handle):
        raise DagsterInvariantViolationError(
            (
                'In pipeline {pipeline_name} solid {solid_name}, input {input_name} '
                'you have specified an input via config while also specifying '
                'a dependency. Either remove the dependency, specify a subdag '
                'to execute, or remove the inputs specification in the environment.'
            ).format(
                pipeline_name=pipeline_context.pipeline.name,
                solid_name=solid.name,
                input_name=input_def.name,
            )
        )

    input_thunk = _create_input_thunk_execution_step(pipeline_context, solid, input_def, input_spec)
    return StepOutputHandle(input_thunk, INPUT_THUNK_OUTPUT)
