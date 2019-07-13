from collections import namedtuple

from dagster import check
from dagster.core.definitions import (
    CompositeSolidDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    ModeDefinition,
    Solid,
    SolidDefinition,
    SolidHandle,
    SolidOutputHandle,
    solids_in_topological_order,
)
from dagster.core.definitions.dependency import DependencyStructure
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.utils import toposort

from .compute import create_compute_step

from .objects import ExecutionStep, ExecutionValueSubplan, StepInput, StepOutputHandle
from .utility import create_join_outputs_step


class _PlanBuilder:
    '''_PlanBuilder. This is the state that is built up during the execution plan build process.

    steps List[ExecutionStep]: a list of the execution steps that have been created.

    step_output_map Dict[SolidOutputHandle, StepOutputHandle]:  maps logical solid outputs
    (solid_name, output_name) to particular step outputs. This covers the case where a solid maps to
    multiple steps and one wants to be able to attach to the logical output of a solid during
    execution.
    '''

    def __init__(self, pipeline_def, environment_config, mode_definition):
        self.pipeline_def = check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
        self.environment_config = check.inst_param(
            environment_config, 'environment_config', EnvironmentConfig
        )
        self.mode_definition = check.inst_param(mode_definition, 'mode_definition', ModeDefinition)
        self.steps = []
        self.step_output_map = dict()
        self.seen_keys = set()

    @property
    def pipeline_name(self):
        return self.pipeline_def.name

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

    def build(self):
        '''Builds the execution plan.
        '''

        # Recursively build the exeuction plan starting at the root pipeline
        self._build_from_sorted_solids(
            solids_in_topological_order(self.pipeline_def), self.pipeline_def.dependency_structure
        )

        # Construct dependency dictionary
        deps = {step.key: set() for step in self.steps}

        for step in self.steps:
            for step_input in step.step_inputs:
                if step_input.is_from_output:
                    deps[step.key].add(step_input.prev_output_handle.step_key)

        step_dict = {step.key: step for step in self.steps}

        system_storage_def = self.mode_definition.get_system_storage_def(
            self.environment_config.storage.system_storage_name
        )

        return ExecutionPlan(self.pipeline_def, step_dict, deps, system_storage_def.is_persistent)

    def _build_from_sorted_solids(
        self, solids, dependency_structure, parent_handle=None, parent_step_inputs=None
    ):
        terminal_compute_step = None
        for solid in solids:
            handle = SolidHandle(solid.name, solid.definition.name, parent_handle)

            ### 1. INPUTS
            # Create and add execution plan steps for solid inputs
            step_inputs = []
            for input_name, input_def in solid.definition.input_dict.items():
                step_input = get_step_input(
                    self,
                    solid,
                    input_name,
                    input_def,
                    dependency_structure,
                    handle,
                    parent_step_inputs,
                )

                # If an input with runtime_type "Nothing" doesnt have a value
                # we don't create a StepInput
                if step_input is None:
                    continue

                check.inst_param(step_input, 'step_input', StepInput)
                step_inputs.append(step_input)

            ### 2. COMPUTE FUNCTION OR RECURSE
            # Create and add execution plan step for the solid compute function or
            # recurse over the solids in a CompositeSolid
            if isinstance(solid.definition, SolidDefinition):
                solid_compute_step = create_compute_step(
                    self.pipeline_name, self.environment_config, solid, step_inputs, handle
                )
                self.add_step(solid_compute_step)
                terminal_compute_step = solid_compute_step
            elif isinstance(solid.definition, CompositeSolidDefinition):
                terminal_compute_step = self._build_from_sorted_solids(
                    solids_in_topological_order(solid.definition),
                    solid.definition.dependency_structure,
                    parent_handle=handle,
                    parent_step_inputs=step_inputs,
                )
            else:
                check.invariant(
                    False,
                    'Unexpected solid type {type} encountered during execution planning'.format(
                        type=type(solid.definition)
                    ),
                )

            ### 3. OUTPUTS
            # Create and add execution plan steps (and output handles) for solid outputs
            for name, output_def in solid.definition.output_dict.items():
                subplan = create_subplan_for_output(
                    self.pipeline_name, solid, terminal_compute_step, output_def
                )
                self.add_steps(subplan.steps)

                output_handle = solid.output_handle(name)
                self.set_output_handle(output_handle, subplan.terminal_step_output_handle)

        return terminal_compute_step


def create_subplan_for_output(pipeline_name, solid, solid_compute_step, output_def):
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(solid_compute_step, 'solid_compute_step', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    output_def = solid.definition.resolve_output_to_origin(output_def.name)
    terminal_step_output_handle = StepOutputHandle.from_step(solid_compute_step, output_def.name)
    return ExecutionValueSubplan.empty(terminal_step_output_handle)


def get_step_input(
    plan_builder, solid, input_name, input_def, dependency_structure, handle, parent_step_inputs
):
    check.inst_param(plan_builder, 'plan_builder', _PlanBuilder)
    check.inst_param(solid, 'solid', Solid)
    check.str_param(input_name, 'input_name')
    check.inst_param(input_def, 'input_def', InputDefinition)
    check.inst_param(dependency_structure, 'dependency_structure', DependencyStructure)
    check.opt_inst_param(handle, 'handle', SolidHandle)
    check.opt_list_param(parent_step_inputs, 'parent_step_inputs', of_type=StepInput)

    solid_config = plan_builder.environment_config.solids.get(str(handle))
    if solid_config and input_name in solid_config.inputs:
        return StepInput(
            input_name, input_def.runtime_type, config_data=solid_config.inputs[input_name]
        )

    input_handle = solid.input_handle(input_name)
    if dependency_structure.has_singular_dep(input_handle):
        solid_output_handle = dependency_structure.get_singular_dep(input_handle)
        return StepInput(
            input_name, input_def.runtime_type, plan_builder.get_output_handle(solid_output_handle)
        )

    if dependency_structure.has_multi_deps(input_handle):
        solid_output_handles = dependency_structure.get_multi_deps(input_handle)
        join_data = create_join_outputs_step(
            plan_builder.pipeline_name,
            input_handle,
            solid_output_handles,
            {
                solid_output_handle: plan_builder.get_output_handle(solid_output_handle)
                for solid_output_handle in solid_output_handles
            },
            handle,
        )
        plan_builder.add_step(join_data.step)
        return StepInput(input_name, input_def.runtime_type, join_data.step_output_handle)

    if solid.container_maps_input(input_name):
        parent_name = solid.container_mapped_input(input_name).definition.name
        parent_inputs = {step_input.name: step_input for step_input in parent_step_inputs}
        if parent_name in parent_inputs:
            parent_input = parent_inputs[parent_name]
            return StepInput(
                input_name,
                input_def.runtime_type,
                parent_input.prev_output_handle,
                parent_input.config_data,
            )

    # At this point we have an input that is not hooked up to
    # the output of another solid or provided via environment config.

    # We will allow this for "Nothing" type inputs and continue.
    if input_def.runtime_type.is_nothing:
        return None

    # Otherwise we throw an error.
    raise DagsterInvariantViolationError(
        (
            'In pipeline {pipeline_name} solid {solid_name}, input {input_name} '
            'must get a value either (a) from a dependency or (b) from the '
            'inputs section of its configuration.'
        ).format(
            pipeline_name=plan_builder.pipeline_name, solid_name=solid.name, input_name=input_name
        )
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
    def build(pipeline_def, environment_config, mode_definition):
        '''Here we build a new ExecutionPlan from a pipeline definition and the environment config.

        To do this, we iterate through the pipeline's solids in topological order, and hand off the
        execution steps for each solid to a companion _PlanBuilder object.

        Once we've processed the entire pipeline, we invoke _PlanBuilder.build() to construct the
        ExecutionPlan object.
        '''
        check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
        check.inst_param(environment_config, 'environment_config', EnvironmentConfig)

        plan_builder = _PlanBuilder(pipeline_def, environment_config, mode_definition)

        # Finally, we build and return the execution plan
        return plan_builder.build()
