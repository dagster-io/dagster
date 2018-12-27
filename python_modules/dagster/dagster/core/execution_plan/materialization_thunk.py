from dagster import check

from dagster.core.definitions import (
    Solid,
    OutputDefinition,
)

from dagster.core.errors import DagsterInvariantViolationError

from .objects import (
    ExecutionPlanInfo,
    ExecutionSubPlan,
)

OUTPUT_THUNK_INPUT = 'output_thunk_input'


def create_output_thunk_execution_step(info, solid, output_def):
    check.inst_param(info, 'info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    dependency_structure = info.pipeline.dependency_structure
    # input_handle = solid.input_handle(input_def.name)

    # if dependency_structure.has_dep(input_handle):
    #     raise DagsterInvariantViolationError(
    #         (
    #             'In pipeline {pipeline_name} solid {solid_name}, input {input_name} '
    #             'you have specified an input via config while also specifying '
    #             'a dependency. Either remove the dependency, specify a subdag '
    #             'to execute, or remove the inputs specification in the environment.'
    #         ).format(
    #             pipeline_name=info.pipeline.name,
    #             solid_name=solid.name,
    #             input_name=input_def.name,
    #         )
    #     )

    # input_thunk = _create_input_thunk_execution_step(solid, input_def, value)
    # return StepOutputHandle(input_thunk, INPUT_THUNK_OUTPUT)
    check.failed('TODO')


def decorate_with_output_materializations(execution_info, solid, output_def, subplan):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)
    check.inst_param(subplan, 'subplan', ExecutionSubPlan)

    return subplan
