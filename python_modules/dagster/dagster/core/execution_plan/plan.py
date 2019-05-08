from collections import namedtuple

from dagster import check

from dagster.core.definitions import (
    solids_in_topological_order,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    Solid,
    SolidOutputHandle,
)

from dagster.core.errors import DagsterInvariantViolationError

from dagster.core.system_config.objects import EnvironmentConfig

from dagster.core.utils import toposort

from .expectations import create_expectations_subplan, decorate_with_expectations

from .input_thunk import create_input_thunk_execution_step

from .materialization_thunk import decorate_with_output_materializations

from .objects import ExecutionStep, ExecutionValueSubplan, StepInput, StepOutputHandle, StepKind

from .transform import create_transform_step


class _PlanBuilder:
    '''_PlanBuilder. This is the state that is built up during the execution plan build process.

    steps List[ExecutionStep]: a list of the execution steps that have been created.

    step_output_map Dict[SolidOutputHandle, StepOutputHandle]:  maps logical solid outputs
    (solid_name, output_name) to particular step outputs. This covers the case where a solid maps to
    multiple steps and one wants to be able to attach to the logical output of a solid during
    execution.
    '''

    def __init__(self):
        self.steps = []
        self.step_output_map = dict()
        self.seen_keys = set()

    def add_step(self, step):
        # Keep track of the step keys we've seen so far to ensure we don't add duplicates
        if step.key in self.seen_keys:
            keys = [s.key for s in self.steps]
            check.failed(
                'Duplicated key {key}. Full list seen so far: {key_list}.'.format(
                    key=step.key, key_list=keys
                )
            )
        self.seen_keys.add(step.key)
        self.steps.append(step)

    def add_steps(self, steps):
        for step in steps:
            self.add_step(step)

    def get_output_handle(self, key):
        check.inst_param(key, 'key', SolidOutputHandle)
        return self.step_output_map[key]

    def set_output_handle(self, key, val):
        check.inst_param(key, 'key', SolidOutputHandle)
        check.inst_param(val, 'val', StepOutputHandle)
        self.step_output_map[key] = val

    def build(self, pipeline_def, artifacts_persisted):
        '''Builds the execution plan.
        '''

        # Construct dependency dictionary
        deps = {step.key: set() for step in self.steps}

        for step in self.steps:
            for step_input in step.step_inputs:
                deps[step.key].add(step_input.prev_output_handle.step_key)

        step_dict = {step.key: step for step in self.steps}

        return ExecutionPlan(pipeline_def, step_dict, deps, artifacts_persisted)


def create_subplan_for_input(
    pipeline_def, environment_config, solid, prev_step_output_handle, input_def
):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(input_def, 'input_def', InputDefinition)

    if environment_config.expectations.evaluate and input_def.expectations:
        return create_expectations_subplan(
            pipeline_def, solid, input_def, prev_step_output_handle, kind=StepKind.INPUT_EXPECTATION
        )
    else:
        return ExecutionValueSubplan.empty(prev_step_output_handle)


def create_subplan_for_output(
    pipeline_def, environment_config, solid, solid_transform_step, output_def
):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(solid_transform_step, 'solid_transform_step', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    subplan = decorate_with_expectations(
        pipeline_def, environment_config, solid, solid_transform_step, output_def
    )

    return decorate_with_output_materializations(
        pipeline_def, environment_config, solid, output_def, subplan
    )


def get_input_source_step_handle(
    pipeline_def, environment_config, plan_builder, solid, input_name, input_def
):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
    check.inst_param(plan_builder, 'plan_builder', _PlanBuilder)
    check.inst_param(solid, 'solid', Solid)
    check.str_param(input_name, 'input_name')
    check.inst_param(input_def, 'input_def', InputDefinition)

    input_handle = solid.input_handle(input_name)
    solid_config = environment_config.solids.get(solid.name)
    dependency_structure = pipeline_def.dependency_structure
    if solid_config and input_def.name in solid_config.inputs:
        step_creation_data = create_input_thunk_execution_step(
            pipeline_def, solid, input_def, solid_config.inputs[input_name]
        )
        plan_builder.add_step(step_creation_data.step)
        return step_creation_data.step_output_handle
    elif dependency_structure.has_dep(input_handle):
        solid_output_handle = dependency_structure.get_dep(input_handle)
        return plan_builder.get_output_handle(solid_output_handle)
    elif input_def.runtime_type.is_nothing:
        return None
    else:
        raise DagsterInvariantViolationError(
            (
                'In pipeline {pipeline_name} solid {solid_name}, input {input_name} '
                'must get a value either (a) from a dependency or (b) from the '
                'inputs section of its configuration.'
            ).format(pipeline_name=pipeline_def.name, solid_name=solid.name, input_name=input_name)
        )


class ExecutionPlan(
    namedtuple('_ExecutionPlan', 'pipeline_def step_dict deps steps artifacts_persisted')
):
    def __new__(cls, pipeline_def, step_dict, deps, artifacts_persisted):
        return super(ExecutionPlan, cls).__new__(
            cls,
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            step_dict=check.dict_param(
                step_dict, 'step_dict', key_type=str, value_type=ExecutionStep
            ),
            deps=check.dict_param(deps, 'deps', key_type=str, value_type=set),
            steps=list(step_dict.values()),
            artifacts_persisted=check.bool_param(artifacts_persisted, 'artifacts_persisted'),
        )

    def get_step_output(self, step_output_handle):
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        step = self.get_step_by_key(step_output_handle.step_key)
        return step.step_output_named(step_output_handle.output_name)

    def has_step(self, key):
        check.str_param(key, 'key')
        return key in self.step_dict

    def get_step_by_key(self, key):
        check.str_param(key, 'key')
        return self.step_dict[key]

    def topological_steps(self):
        return [step for step_level in self.topological_step_levels() for step in step_level]

    def topological_step_levels(self):
        return [
            [self.step_dict[step_key] for step_key in step_key_level]
            for step_key_level in toposort(self.deps)
        ]

    @staticmethod
    def build(pipeline_def, environment_config):
        '''Here we build a new ExecutionPlan from a pipeline definition and the environment config.

        To do this, we iterate through the pipeline's solids in topological order, and hand off the
        execution steps for each solid to a companion _PlanBuilder object.

        Once we've processed the entire pipeline, we invoke _PlanBuilder.build() to construct the
        ExecutionPlan object.
        '''
        check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
        check.inst_param(environment_config, 'environment_config', EnvironmentConfig)

        plan_builder = _PlanBuilder()

        for solid in solids_in_topological_order(pipeline_def):
            ### 1. INPUTS
            # Create and add execution plan steps for solid inputs
            step_inputs = []
            for input_name, input_def in solid.definition.input_dict.items():
                prev_step_output_handle = get_input_source_step_handle(
                    pipeline_def, environment_config, plan_builder, solid, input_name, input_def
                )

                # We return None for the handle (see above in get_input_source_step_handle) when the
                # input def runtime type is "Nothing"
                if not prev_step_output_handle:
                    continue

                subplan = create_subplan_for_input(
                    pipeline_def, environment_config, solid, prev_step_output_handle, input_def
                )

                plan_builder.add_steps(subplan.steps)

                step_inputs.append(
                    StepInput(
                        input_def.name, input_def.runtime_type, subplan.terminal_step_output_handle
                    )
                )

            ### 2. TRANSFORM FUNCTION
            # Create and add execution plan step for the solid transform function
            solid_transform_step = create_transform_step(
                pipeline_def, environment_config, solid, step_inputs
            )
            plan_builder.add_step(solid_transform_step)

            ### 3. OUTPUTS
            # Create and add execution plan steps (and output handles) for solid outputs
            for name, output_def in solid.definition.output_dict.items():
                subplan = create_subplan_for_output(
                    pipeline_def, environment_config, solid, solid_transform_step, output_def
                )
                plan_builder.add_steps(subplan.steps)

                output_handle = solid.output_handle(name)
                plan_builder.set_output_handle(output_handle, subplan.terminal_step_output_handle)

        # Finally, we build and return the execution plan
        return plan_builder.build(
            pipeline_def=pipeline_def,
            artifacts_persisted=environment_config.storage.construct_run_storage().is_persistent,
        )
