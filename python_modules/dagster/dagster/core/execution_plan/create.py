from collections import (
    defaultdict,
    namedtuple,
)

from dagster import check

from dagster.core.definitions import (
    InputDefinition,
    OutputDefinition,
    Result,
    Solid,
    SolidOutputHandle,
    TransformExecutionInfo,
)

from dagster.core.errors import DagsterInvariantViolationError

from dagster.core.execution_context import RuntimeExecutionContext

from .expectations import (
    create_expectations_subplan,
    decorate_with_expectations,
)

from .input_thunk import create_input_thunk_execution_step

from .objects import (
    ExecutionPlan,
    ExecutionPlanInfo,
    ExecutionStep,
    ExecutionSubPlan,
    StepInput,
    StepOutput,
    StepOutputHandle,
    StepTag,
)

from .serialization import (
    decorate_with_serialization,
)

def _yield_transform_results(context, step, conf, inputs):
    gen = step.solid.definition.transform_fn(
        TransformExecutionInfo(context, conf, step.solid.definition),
        inputs,
    )

    if isinstance(gen, Result):
        raise DagsterInvariantViolationError(
            (
                'Transform for solid {solid_name} returned a Result rather than ' +
                'yielding it. The transform_fn of the core SolidDefinition must yield ' +
                'its results'
            ).format(solid_name=step.solid.name)
        )

    if gen is None:
        return

    for result in gen:
        if not isinstance(result, Result):
            raise DagsterInvariantViolationError(
                (
                    'Transform for solid {solid_name} yielded {result} rather an ' +
                    'an instance of the Result class.'
                ).format(
                    result=repr(result),
                    solid_name=step.solid.name,
                )
            )

        context.info(
            'Solid {solid} emitted output "{output}" value {value}'.format(
                solid=step.solid.name,
                output=result.output_name,
                value=repr(result.value),
            )
        )
        yield result

def _execute_core_transform(context, step, conf, inputs):
    '''
    Execute the user-specified transform for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(context, 'context', RuntimeExecutionContext)
    check.inst_param(step, 'step', ExecutionStep)
    check.dict_param(inputs, 'inputs', key_type=str)

    solid = step.solid

    context.debug('Executing core transform for solid {solid}.'.format(solid=solid.name))

    all_results = list(_yield_transform_results(context, step, conf, inputs))

    if len(all_results) != len(solid.definition.output_defs):
        emitted_result_names = set([r.output_name for r in all_results])
        solid_output_names = set([output_def.name for output_def in solid.definition.output_defs])
        omitted_outputs = solid_output_names.difference(emitted_result_names)
        context.info(
            'Solid {solid} did not fire outputs {outputs}'.format(
                solid=solid.name,
                outputs=repr(omitted_outputs),
            )
        )

    return all_results

def get_solid_user_config(execution_info, pipeline_solid):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(pipeline_solid, 'pipeline_solid', Solid)

    name = pipeline_solid.name
    solid_configs = execution_info.environment.solids
    return solid_configs[name].config if name in solid_configs else None





# This is the state that is built up during the execution plan build process.
# steps is just a list of the steps that have been created
# step_output_map maps logical solid outputs (solid_name, output_name) to particular
# step outputs. This covers the case where a solid maps to multiple steps
# and one wants to be able to attach to the logical output of a solid during execution
StepBuilderState = namedtuple('StepBuilderState', 'steps step_output_map')



class StepOutputMap(dict):
    def __getitem__(self, key):
        check.inst_param(key, 'key', SolidOutputHandle)
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        check.inst_param(key, 'key', SolidOutputHandle)
        check.inst_param(val, 'val', StepOutputHandle)
        return dict.__setitem__(self, key, val)










def create_execution_plan_core(execution_info):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)

    execution_graph = execution_info.execution_graph

    state = StepBuilderState(
        steps=[],
        step_output_map=StepOutputMap(),
    )

    for pipeline_solid in execution_graph.topological_solids:
        step_inputs = create_step_inputs(execution_info, state, pipeline_solid)

        solid_transform_step = create_transform_step(
            pipeline_solid,
            step_inputs,
            get_solid_user_config(execution_info, pipeline_solid),
        )

        state.steps.append(solid_transform_step)

        for output_def in pipeline_solid.definition.output_defs:
            subplan = create_subplan_for_output(
                execution_info,
                pipeline_solid,
                solid_transform_step,
                output_def,
            )
            state.steps.extend(subplan.steps)

            output_handle = pipeline_solid.output_handle(output_def.name)
            state.step_output_map[output_handle] = subplan.terminal_step_output_handle

    return create_execution_plan_from_steps(state.steps)


def create_execution_plan_from_steps(steps):
    check.list_param(steps, 'steps', of_type=ExecutionStep)

    step_dict = {step.key: step for step in steps}

    deps = defaultdict()

    seen_keys = set()

    for step in steps:

        if step.key in seen_keys:
            keys = [s.key for s in steps]
            check.failed(
                'Duplicated key {key}. Full list: {key_list}.'.format(key=step.key, key_list=keys)
            )

        seen_keys.add(step.key)

        deps[step.key] = set()
        for step_input in step.step_inputs:
            deps[step.key].add(step_input.prev_output_handle.step.key)

    return ExecutionPlan(step_dict, deps)


def create_subplan_for_input(execution_info, solid, prev_step_output_handle, input_def):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(input_def, 'input_def', InputDefinition)

    if execution_info.environment.expectations.evaluate and input_def.expectations:
        return create_expectations_subplan(
            solid,
            input_def,
            prev_step_output_handle,
            tag=StepTag.INPUT_EXPECTATION,
        )
    else:
        return ExecutionSubPlan(
            steps=[],
            terminal_step_output_handle=prev_step_output_handle,
        )




def create_subplan_for_output(execution_info, solid, solid_transform_step, output_def):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(solid_transform_step, 'solid_transform_step', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    subplan = decorate_with_expectations(execution_info, solid, solid_transform_step, output_def)

    return decorate_with_serialization(execution_info, solid, output_def, subplan)




def create_transform_step(solid, step_inputs, conf):
    check.inst_param(solid, 'solid', Solid)
    check.list_param(step_inputs, 'step_inputs', of_type=StepInput)

    return ExecutionStep(
        key='{solid.name}.transform'.format(solid=solid),
        step_inputs=step_inputs,
        step_outputs=[
            StepOutput(name=output_def.name, dagster_type=output_def.dagster_type)
            for output_def in solid.definition.output_defs
        ],
        compute_fn=lambda context, step, inputs: _execute_core_transform(
            context,
            step,
            conf,
            inputs,
        ),
        tag=StepTag.TRANSFORM,
        solid=solid,
    )



def create_step_inputs(info, state, pipeline_solid):
    check.inst_param(info, 'info', ExecutionPlanInfo)
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(pipeline_solid, 'pipeline_solid', Solid)

    step_inputs = []

    topo_solid = pipeline_solid.definition
    dependency_structure = info.execution_graph.dependency_structure

    for input_def in topo_solid.input_defs:
        input_handle = pipeline_solid.input_handle(input_def.name)

        solid_config = info.environment.solids.get(topo_solid.name)
        if solid_config and input_def.name in solid_config.inputs:
            prev_step_output_handle = create_input_thunk_execution_step(
                info,
                pipeline_solid,
                input_def,
                solid_config.inputs[input_def.name],
            )
            state.steps.append(prev_step_output_handle.step)
        elif dependency_structure.has_dep(input_handle):
            solid_output_handle = dependency_structure.get_dep(input_handle)
            prev_step_output_handle = state.step_output_map[solid_output_handle]
        else:
            raise DagsterInvariantViolationError(
                (
                    'In pipeline {pipeline_name} solid {solid_name}, input {input_name} '
                    'must get a value either (a) from a dependency or (b) from the '
                    'inputs section of its configuration.'
                ).format(
                    pipeline_name=info.execution_graph.pipeline.name,
                    solid_name=pipeline_solid.name,
                    input_name=input_def.name,
                )
            )

        subplan = create_subplan_for_input(
            info,
            pipeline_solid,
            prev_step_output_handle,
            input_def,
        )

        state.steps.extend(subplan.steps)
        step_inputs.append(
            StepInput(
                input_def.name,
                input_def.dagster_type,
                subplan.terminal_step_output_handle,
            )
        )

    return step_inputs
