from dagster import check

from dagster.core.definitions import (
    solids_in_topological_order,
    InputDefinition,
    OutputDefinition,
    Solid,
)

from dagster.core.errors import DagsterInvariantViolationError, DagsterInvalidSubplanExecutionError

from dagster.core.execution_context import ExecutionMetadata

from .expectations import create_expectations_subplan, decorate_with_expectations

from .input_thunk import create_input_thunk_execution_step

from .materialization_thunk import decorate_with_output_materializations

from .objects import (
    ExecutionPlan,
    ExecutionPlanInfo,
    ExecutionStep,
    ExecutionValueSubplan,
    StepBuilderState,
    StepInput,
    StepOutputHandle,
    StepKind,
)

from .plan_subset import ExecutionPlanSubsetInfo

from .transform import create_transform_step


def get_solid_user_config(execution_info, pipeline_solid):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(pipeline_solid, 'pipeline_solid', Solid)

    name = pipeline_solid.name
    solid_configs = execution_info.environment.solids
    return solid_configs[name].config if name in solid_configs else None


def create_execution_plan_core(execution_info, execution_metadata, subset_info=None):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(execution_metadata, 'execution_metadata', ExecutionMetadata)
    check.opt_inst_param(subset_info, 'subset_info', ExecutionPlanSubsetInfo)

    state = StepBuilderState(
        pipeline_name=execution_info.pipeline.name, initial_tags=execution_metadata.tags
    )

    for solid in solids_in_topological_order(execution_info.pipeline):

        with state.push_tags(solid=solid.name, solid_definition=solid.definition.name):
            step_inputs = create_step_inputs(execution_info, state, solid)

            solid_transform_step = create_transform_step(
                execution_info,
                state,
                solid,
                step_inputs,
                get_solid_user_config(execution_info, solid),
            )

            state.steps.append(solid_transform_step)

            for output_def in solid.definition.output_defs:
                with state.push_tags(output=output_def.name):
                    subplan = create_subplan_for_output(
                        execution_info, state, solid, solid_transform_step, output_def
                    )
                    state.steps.extend(subplan.steps)

                    output_handle = solid.output_handle(output_def.name)
                    state.step_output_map[output_handle] = subplan.terminal_step_output_handle

    execution_plan = create_execution_plan_from_steps(state.steps)

    if subset_info:
        return _create_subplan(
            execution_info,
            # ExecutionPlanInfo(context=context, pipeline=pipeline, environment=typed_environment),
            StepBuilderState(execution_info.pipeline.name),
            execution_plan,
            subset_info,
        )
    else:
        return execution_plan


def create_execution_plan_from_steps(steps):
    check.list_param(steps, 'steps', of_type=ExecutionStep)

    step_dict = {step.key: step for step in steps}
    deps = {step.key: set() for step in steps}

    seen_keys = set()

    for step in steps:
        if step.key in seen_keys:
            keys = [s.key for s in steps]
            check.failed(
                'Duplicated key {key}. Full list: {key_list}.'.format(key=step.key, key_list=keys)
            )

        seen_keys.add(step.key)

        for step_input in step.step_inputs:
            deps[step.key].add(step_input.prev_output_handle.step.key)

    return ExecutionPlan(step_dict, deps)


def create_subplan_for_input(execution_info, state, solid, prev_step_output_handle, input_def):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(input_def, 'input_def', InputDefinition)

    if execution_info.environment.expectations.evaluate and input_def.expectations:
        return create_expectations_subplan(
            state, solid, input_def, prev_step_output_handle, kind=StepKind.INPUT_EXPECTATION
        )
    else:
        return ExecutionValueSubplan.empty(prev_step_output_handle)


def create_subplan_for_output(execution_info, state, solid, solid_transform_step, output_def):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(solid_transform_step, 'solid_transform_step', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    subplan = decorate_with_expectations(
        execution_info, state, solid, solid_transform_step, output_def
    )

    return decorate_with_output_materializations(execution_info, state, solid, output_def, subplan)


def get_input_source_step_handle(execution_info, state, solid, input_def):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(input_def, 'input_def', InputDefinition)

    input_handle = solid.input_handle(input_def.name)
    solid_config = execution_info.environment.solids.get(solid.name)
    dependency_structure = execution_info.pipeline.dependency_structure
    if solid_config and input_def.name in solid_config.inputs:
        input_thunk_output_handle = create_input_thunk_execution_step(
            execution_info, state, solid, input_def, solid_config.inputs[input_def.name]
        )
        state.steps.append(input_thunk_output_handle.step)
        return input_thunk_output_handle
    elif dependency_structure.has_dep(input_handle):
        solid_output_handle = dependency_structure.get_dep(input_handle)
        return state.step_output_map[solid_output_handle]
    else:
        raise DagsterInvariantViolationError(
            (
                'In pipeline {pipeline_name} solid {solid_name}, input {input_name} '
                'must get a value either (a) from a dependency or (b) from the '
                'inputs section of its configuration.'
            ).format(
                pipeline_name=execution_info.pipeline.name,
                solid_name=solid.name,
                input_name=input_def.name,
            )
        )


def create_step_inputs(info, state, solid):
    check.inst_param(info, 'info', ExecutionPlanInfo)
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(solid, 'solid', Solid)

    step_inputs = []

    for input_def in solid.definition.input_defs:
        with state.push_tags(input=input_def.name):
            prev_step_output_handle = get_input_source_step_handle(info, state, solid, input_def)

            subplan = create_subplan_for_input(
                info, state, solid, prev_step_output_handle, input_def
            )

            state.steps.extend(subplan.steps)
            step_inputs.append(
                StepInput(
                    input_def.name, input_def.runtime_type, subplan.terminal_step_output_handle
                )
            )

    return step_inputs


def _create_subplan(execution_plan_info, state, execution_plan, subset_info):
    check.inst_param(execution_plan_info, 'execution_plan_info', ExecutionPlanInfo)
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(subset_info, 'subset_info', ExecutionPlanSubsetInfo)

    steps = []

    for step in execution_plan.steps:
        if step.key not in subset_info.subset:
            # Not included in subset. Skip.
            continue

        with state.push_tags(**step.tags):
            if step.key not in subset_info.step_factory_fns:
                steps.append(step)
            else:
                steps.extend(_create_new_steps_for_input(state, step, subset_info))

    new_plan = create_execution_plan_from_steps(steps)

    for step in new_plan.steps:
        for step_input in step.step_inputs:
            if new_plan.has_step(step_input.prev_output_handle.step.key):
                # step in is in the new plan, we're fine
                continue

            # Now check to see if the input is provided

            if not subset_info.has_injected_step(step.key, step_input.name):
                raise DagsterInvalidSubplanExecutionError(
                    (
                        'You have specified a subset execution on pipeline {pipeline_name} '
                        'with step_keys {step_keys}. You have failed to provide the required input '
                        '{input_name} for step {step_key}.'
                    ).format(
                        pipeline_name=execution_plan_info.pipeline.name,
                        step_keys=list(subset_info.subset),
                        input_name=step_input.name,
                        step_key=step.key,
                    ),
                    pipeline_name=execution_plan_info.pipeline.name,
                    step_keys=list(subset_info.subset),
                    input_name=step_input.name,
                    step_key=step.key,
                )

    return new_plan


def _create_new_steps_for_input(state, step, subset_info):
    new_steps = []
    new_step_inputs = []
    for step_input in step.step_inputs:
        if subset_info.has_injected_step(step.key, step_input.name):
            subset_info.step_factory_fns[step.key][step_input.name](state, step, step_input)

            step_output_handle = check.inst(
                subset_info.step_factory_fns[step.key][step_input.name](state, step, step_input),
                StepOutputHandle,
                'Step factory function must create StepOutputHandle',
            )

            new_steps.append(step_output_handle.step)
            new_step_inputs.append(
                StepInput(step_input.name, step_input.runtime_type, step_output_handle)
            )

        else:
            # TODO: I don't think you should able to get here
            new_step_inputs.append(step_input)

    new_steps.append(step.with_new_inputs(new_step_inputs))
    return new_steps
