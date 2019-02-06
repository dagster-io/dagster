import copy

from dagster import check

from dagster.core.definitions import InputDefinition, OutputDefinition, Solid

from dagster.core.errors import DagsterInvariantViolationError, DagsterInvalidSubplanExecutionError


from dagster.core.execution_context import ExecutionMetadata

from .create_plan_tracker import create_new_plan_id

from .expectations import create_expectations_value_subplan, decorate_with_expectations

from .input_thunk import create_input_thunk_execution_step

from .materialization_thunk import decorate_with_output_materializations

from .objects import (
    CreateExecutionPlanInfo,
    ExecutionPlan,
    ExecutionStep,
    ExecutionValueSubplan,
    PlanBuilder,
    StepInput,
    StepKind,
    StepOutputHandle,
)

from .plan_subset import ExecutionPlanSubsetInfo, ExecutionPlanAddedOutputs
from .subplan_executor import decorate_with_subplan_executors, SUBPLAN_BEGIN_SENTINEL
from .transform import create_transform_step


def get_solid_user_config(execution_info, pipeline_solid):
    check.inst_param(execution_info, 'execution_info', CreateExecutionPlanInfo)
    check.inst_param(pipeline_solid, 'pipeline_solid', Solid)

    name = pipeline_solid.name
    solid_configs = execution_info.environment.solids
    return solid_configs[name].config if name in solid_configs else None


def create_execution_plan_core(
    execution_info, execution_metadata, subset_info=None, added_outputs=None
):
    check.inst_param(execution_info, 'execution_info', CreateExecutionPlanInfo)
    check.inst_param(execution_metadata, 'execution_metadata', ExecutionMetadata)
    check.opt_inst_param(subset_info, 'subset_info', ExecutionPlanSubsetInfo)
    check.opt_inst_param(added_outputs, 'added_output', ExecutionPlanAddedOutputs)

    if not execution_info.pipeline.solids:
        return create_execution_plan_from_steps(create_new_plan_id(), [])

    # There must be at least one builder
    check.param_invariant(execution_info.plan_tracker.plan_order, 'execution_info')

    #
    # Create execution plan doesn't create just one execution plan. It creates
    # a root execution plan as well as all the subplans that comprise that
    # root execution plan. When the user defines fan-in and fan-out dependencies
    # system constructs an execution subplan within the parent plan that will be
    # invoked N items, once for each item, as the downstream solids consume the items.
    # All dagster features (dependencies, type-checking, expectations, etc) apply to
    # those individual items as well.
    #
    # When a subplan is needed we construct a plan executor step that is responsible
    # for the multiple executions of the subplan. This is easy when explained by example.
    #
    # Imagine the following pipeline: A --> B --> C
    # A produces a Sequence (of Ints)
    # B accepts an Int -- by specifying a fan-out dependency -- and outputs an Int
    # C accepts a Sequence (of Ints) by specifying a fan-in dependency.
    #
    # This will construct two execution plans:
    #
    # PlanOne Steps:
    # Transform(A) --> PlanExecutor(PlanTwo) --> Transform(C)
    #
    # All inputs and outputs in PlanOne are Sequences
    #
    # PlanTwo:
    # Transform(B)
    #
    # The job of PlanExecutor(PlanTwo) is to invoke PlanTwo, as Transform(C) consumes
    # each item. The items stream from one step to the next.
    #
    # The plans themselves are created in reverse topological order, so that plans
    # are created before plans that depend on them. In this simple example, that means
    # that PlanTwo will be created before PlanOne
    #

    last_plan = None
    plans_dict = {}
    for plan_id in reversed(execution_info.plan_tracker.plan_order):
        plan_builder = PlanBuilder(
            plan_id,
            execution_info.plan_tracker.solid_names_by_plan_id[plan_id],
            copy.copy(plans_dict),
            execution_info.pipeline.name,
            initial_tags=execution_metadata.tags,
        )
        new_plan = _create_plan(plan_id, execution_info, plan_builder, subset_info, added_outputs)
        last_plan = new_plan
        plans_dict[new_plan.plan_id] = new_plan
    return last_plan


def _create_plan(plan_id, execution_info, plan_builder, subset_info, added_outputs):
    check.inst_param(execution_info, 'execution_info', CreateExecutionPlanInfo)
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)

    for solid_name in plan_builder.get_solid_names():
        solid = execution_info.pipeline.solid_named(solid_name)
        with plan_builder.push_tags(solid=solid.name, solid_definition=solid.definition.name):
            step_inputs = create_step_inputs(execution_info, plan_builder, solid)
            solid_transform_step = create_transform_step(
                execution_info,
                plan_builder,
                solid,
                step_inputs,
                get_solid_user_config(execution_info, solid),
            )

            plan_builder.add_step(solid_transform_step)

            for output_def in solid.definition.output_defs:
                with plan_builder.push_tags(output=output_def.name):
                    subplan = create_value_subplan_for_output(
                        execution_info, plan_builder, solid, solid_transform_step, output_def
                    )
                    plan_builder.add_steps(subplan.steps)

                    output_handle = solid.output_handle(output_def.name)
                    plan_builder.set_step_output_for_solid_output_handle(
                        output_handle, subplan.terminal_step_output_handle
                    )

    if subset_info or added_outputs:
        return _create_augmented_subplan(execution_info, plan_builder, subset_info, added_outputs)
    else:
        return create_execution_plan_from_steps(plan_id, plan_builder.get_steps())


def create_execution_plan_from_steps(plan_id, steps):
    check.str_param(plan_id, 'plan_id')
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
            # For now. Should probably not checkin
            if not step_input.prev_output_handle is SUBPLAN_BEGIN_SENTINEL:
                deps[step.key].add(step_input.prev_output_handle.step.key)

    return ExecutionPlan(plan_id, step_dict, deps)


def create_value_subplan_for_input(
    execution_info, plan_builder, solid, prev_step_output_handle, input_def
):
    check.inst_param(execution_info, 'execution_info', CreateExecutionPlanInfo)
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(input_def, 'input_def', InputDefinition)

    if execution_info.environment.expectations.evaluate and input_def.expectations:
        return create_expectations_value_subplan(
            plan_builder, solid, input_def, prev_step_output_handle, kind=StepKind.INPUT_EXPECTATION
        )
    else:
        return ExecutionValueSubplan.empty(prev_step_output_handle)


def create_value_subplan_for_output(
    execution_info, plan_builder, solid, solid_transform_step, output_def
):
    check.inst_param(execution_info, 'execution_info', CreateExecutionPlanInfo)
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(solid_transform_step, 'solid_transform_step', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    value_subplan = decorate_with_expectations(
        execution_info, plan_builder, solid, solid_transform_step, output_def
    )

    value_subplan = decorate_with_output_materializations(
        execution_info, plan_builder, solid, output_def, value_subplan
    )

    return decorate_with_subplan_executors(
        execution_info, plan_builder, solid, output_def, value_subplan
    )


def get_input_source_step_handle(execution_info, plan_builder, solid, input_def):
    check.inst_param(execution_info, 'execution_info', CreateExecutionPlanInfo)
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(input_def, 'input_def', InputDefinition)

    input_handle = solid.input_handle(input_def.name)
    solid_config = execution_info.environment.solids.get(solid.name)
    dependency_structure = execution_info.pipeline.dependency_structure

    if solid_config and input_def.name in solid_config.inputs:
        input_thunk_output_handle = create_input_thunk_execution_step(
            execution_info, plan_builder, solid, input_def, solid_config.inputs[input_def.name]
        )
        plan_builder.add_step(input_thunk_output_handle.step)
        return input_thunk_output_handle
    elif dependency_structure.has_dep(input_handle):
        solid_output_handle = dependency_structure.get_dep_output_handle(input_handle)
        dep_def = dependency_structure.get_dep_def(input_handle)
        if dep_def.is_fanin:
            # We need to get the step output handle of the subplan executor
            subplan_id = execution_info.plan_id_for_solid(solid_output_handle.solid)
            return plan_builder.get_step_output_handle_for_plan_id(subplan_id)
        elif dep_def.is_fanout:
            # This is going to be the entry point into the subplan
            return SUBPLAN_BEGIN_SENTINEL
        else:
            return plan_builder.get_step_output_for_solid_output_handle(solid_output_handle)
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


def create_step_inputs(execution_info, plan_builder, solid):
    check.inst_param(execution_info, 'execution_info', CreateExecutionPlanInfo)
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
    check.inst_param(solid, 'solid', Solid)

    step_inputs = []

    for input_def in solid.definition.input_defs:
        with plan_builder.push_tags(input=input_def.name):
            prev_step_output_handle = get_input_source_step_handle(
                execution_info, plan_builder, solid, input_def
            )

            subplan = create_value_subplan_for_input(
                execution_info, plan_builder, solid, prev_step_output_handle, input_def
            )

            plan_builder.add_steps(subplan.steps)
            step_inputs.append(
                StepInput(
                    input_def.name, input_def.runtime_type, subplan.terminal_step_output_handle
                )
            )

    return step_inputs


def _create_augmented_subplan(execution_info, plan_builder, subset_info=None, added_outputs=None):
    check.inst_param(execution_info, 'execution_info', CreateExecutionPlanInfo)
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
    check.opt_inst_param(subset_info, 'subset_info', ExecutionPlanSubsetInfo)
    check.opt_inst_param(added_outputs, 'added_outputs', ExecutionPlanAddedOutputs)

    check.invariant(len(execution_info.plan_tracker.plan_order) == 1)
    plan_id = execution_info.plan_tracker.plan_order[0]

    plan_builder = PlanBuilder(
        plan_id,
        execution_info.plan_tracker.solid_names_by_plan_id[plan_id],
        {},
        execution_info.pipeline.name,
    )

    steps = []

    for step in plan_builder.get_steps():
        if subset_info and step.key not in subset_info.subset:
            # Not included in subset. Skip.
            continue

        with plan_builder.push_tags(**step.tags):
            steps.extend(
                _all_augmented_steps_for_step(plan_builder, step, subset_info, added_outputs)
            )

    new_plan = create_execution_plan_from_steps(plan_id, steps)

    return _validate_new_plan(new_plan, subset_info, execution_info)


def _validate_new_plan(new_plan, subset_info, execution_info):
    check.inst_param(new_plan, 'new_plan', ExecutionPlan)
    check.opt_inst_param(subset_info, 'subset_info', ExecutionPlanSubsetInfo)
    check.inst_param(execution_info, 'execution_info', CreateExecutionPlanInfo)

    included_keys = {step.key for step in new_plan.steps}

    for step in new_plan.steps:
        for step_input in step.step_inputs:
            if step_input.prev_output_handle.step.key in included_keys:
                # step in is in the new plan, we're fine
                continue

            # Now check to see if the input is provided

            if subset_info and not subset_info.has_injected_step_for_input(
                step.key, step_input.name
            ):
                raise DagsterInvalidSubplanExecutionError(
                    (
                        'You have specified a subset execution on pipeline {pipeline_name} '
                        'with step_keys {step_keys}. You have failed to provide the required input '
                        '{input_name} for step {step_key}.'
                    ).format(
                        pipeline_name=execution_info.pipeline.name,
                        step_keys=list(subset_info.subset),
                        input_name=step_input.name,
                        step_key=step.key,
                    ),
                    pipeline_name=execution_info.pipeline.name,
                    step_keys=list(subset_info.subset),
                    input_name=step_input.name,
                    step_key=step.key,
                )
    return new_plan


def _all_augmented_steps_for_step(plan_builder, step, subset_info, added_outputs):
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
    check.inst_param(step, 'step', ExecutionStep)
    check.opt_inst_param(subset_info, 'subset_info', ExecutionPlanSubsetInfo)
    check.opt_inst_param(added_outputs, 'added_output', ExecutionPlanAddedOutputs)

    new_input_steps = []

    if subset_info and step.key in subset_info.input_step_factory_fns:
        step, new_input_steps = _create_new_step_with_added_inputs(plan_builder, step, subset_info)

    all_new_steps = [step] + new_input_steps

    if added_outputs and step.key in added_outputs.output_step_factory_fns:
        for output_step_factory_entry in added_outputs.output_step_factory_fns[step.key]:
            check.invariant(step.has_step_output(output_step_factory_entry.output_name))
            step_output = step.step_output_named(output_step_factory_entry.output_name)
            all_new_steps.append(
                output_step_factory_entry.step_factory_fn(plan_builder, step, step_output)
            )

    return all_new_steps


# def _create_new_steps_for_input(plan_builder, step, subset_info):
#     check.inst_param(plan_builder, 'plan_builder', PlanBuilder)

#     new_steps = []
#     new_step_inputs = []
#     for step_input in step.step_inputs:
#         if step_input.name in subset_info.inputs[step.key]:
#             value_thunk_step_output_handle = create_value_thunk_step(
#                 plan_builder,
#                 step.solid,
#                 step_input.runtime_type,
#                 step.key + '.input.' + step_input.name + '.value',
#                 subset_info.inputs[step.key][step_input.name],
#             )

#             new_value_step = value_thunk_step_output_handle.step
# >>>>>>> PR #699
# <<<<<<< HEAD


def _create_new_step_with_added_inputs(plan_builder, step, subset_info):
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
    check.inst_param(step, 'step', ExecutionStep)
    check.opt_inst_param(subset_info, 'subset_info', ExecutionPlanSubsetInfo)

    new_steps = []
    new_step_inputs = []
    for step_input in step.step_inputs:
        if not subset_info.has_injected_step_for_input(step.key, step_input.name):
            continue

        step_output_handle = check.inst(
            subset_info.input_step_factory_fns[step.key][step_input.name](
                plan_builder, step, step_input
            ),
            StepOutputHandle,
            'Step factory function must create StepOutputHandle',
        )

        new_steps.append(step_output_handle.step)
        new_step_inputs.append(
            StepInput(step_input.name, step_input.runtime_type, step_output_handle)
        )

    return step.with_new_inputs(new_step_inputs), new_steps
