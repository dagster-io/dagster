from collections import OrderedDict, namedtuple

from dagster import check
from dagster.core.definitions import (
    CompositeSolidDefinition,
    InputDefinition,
    PipelineDefinition,
    Solid,
    SolidDefinition,
    SolidHandle,
    SolidOutputHandle,
    solids_in_topological_order,
)
from dagster.core.definitions.dependency import DependencyStructure
from dagster.core.errors import DagsterExecutionStepNotFoundError, DagsterInvariantViolationError
from dagster.core.events import DagsterEvent
from dagster.core.execution.config import IRunConfig
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.utils import toposort

from .compute import create_compute_step
from .objects import ExecutionStep, StepInput, StepInputSourceType, StepOutputHandle


class _PlanBuilder(object):
    '''_PlanBuilder. This is the state that is built up during the execution plan build process.

    steps List[ExecutionStep]: a list of the execution steps that have been created.

    step_output_map Dict[SolidOutputHandle, StepOutputHandle]:  maps logical solid outputs
    (solid_name, output_name) to particular step outputs. This covers the case where a solid maps to
    multiple steps and one wants to be able to attach to the logical output of a solid during
    execution.
    '''

    def __init__(self, pipeline_def, environment_config, run_config):
        self.pipeline_def = check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
        self.environment_config = check.inst_param(
            environment_config, 'environment_config', EnvironmentConfig
        )
        self.run_config = check.inst_param(run_config, 'run_config', IRunConfig)
        self.mode_definition = pipeline_def.get_mode_definition(run_config.mode)
        self._steps = OrderedDict()
        self.step_output_map = dict()
        self._seen_keys = set()

    @property
    def pipeline_name(self):
        return self.pipeline_def.name

    def add_step(self, step):
        # Keep track of the step keys we've seen so far to ensure we don't add duplicates
        if step.key in self._seen_keys:
            keys = [s.key for s in self._steps]
            check.failed(
                'Duplicated key {key}. Full list seen so far: {key_list}.'.format(
                    key=step.key, key_list=keys
                )
            )
        self._seen_keys.add(step.key)
        self._steps[step.solid_handle.to_string()] = step

    def add_steps(self, steps):
        for step in steps:
            self.add_step(step)

    def get_step_by_handle(self, handle):
        check.inst_param(handle, 'handle', SolidHandle)
        return self._steps[handle.to_string()]

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
        deps = {step.key: set() for step in self._steps.values()}

        for step in self._steps.values():
            for step_input in step.step_inputs:
                deps[step.key].update(step_input.dependency_keys)

        step_dict = {step.key: step for step in self._steps.values()}

        system_storage_def = self.mode_definition.get_system_storage_def(
            self.environment_config.storage.system_storage_name
        )

        previous_run_id = self.run_config.previous_run_id
        step_keys_to_execute = self.run_config.step_keys_to_execute or [
            step.key for step in self._steps.values()
        ]

        return ExecutionPlan(
            self.pipeline_def,
            step_dict,
            deps,
            system_storage_def.is_persistent,
            previous_run_id,
            step_keys_to_execute,
        )

    def _build_from_sorted_solids(
        self, solids, dependency_structure, parent_handle=None, parent_step_inputs=None
    ):
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

            ### 2a. COMPUTE FUNCTION
            # Create and add execution plan step for the solid compute function
            if isinstance(solid.definition, SolidDefinition):
                solid_compute_step = create_compute_step(
                    self.pipeline_name, self.environment_config, solid, step_inputs, handle
                )
                self.add_step(solid_compute_step)

            ### 2b. RECURSE
            # Recurse over the solids contained in an instance of CompositeSolidDefinition
            elif isinstance(solid.definition, CompositeSolidDefinition):
                self._build_from_sorted_solids(
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
            # Create output handles for solid outputs
            for name, output_def in solid.definition.output_dict.items():
                output_handle = solid.output_handle(name)

                # Punch through layers of composition scope to map to the output of the
                # actual compute step
                resolved_output_def, resolved_handle = solid.definition.resolve_output_to_origin(
                    output_def.name, handle
                )
                compute_step = self.get_step_by_handle(resolved_handle)
                self.set_output_handle(
                    output_handle,
                    StepOutputHandle.from_step(compute_step, resolved_output_def.name),
                )


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
            input_name,
            input_def.runtime_type,
            StepInputSourceType.CONFIG,
            config_data=solid_config.inputs[input_name],
        )

    input_handle = solid.input_handle(input_name)
    if dependency_structure.has_singular_dep(input_handle):
        solid_output_handle = dependency_structure.get_singular_dep(input_handle)
        return StepInput(
            input_name,
            input_def.runtime_type,
            StepInputSourceType.SINGLE_OUTPUT,
            [plan_builder.get_output_handle(solid_output_handle)],
        )

    if dependency_structure.has_multi_deps(input_handle):
        solid_output_handles = dependency_structure.get_multi_deps(input_handle)
        return StepInput(
            input_name,
            input_def.runtime_type,
            StepInputSourceType.MULTIPLE_OUTPUTS,
            [
                plan_builder.get_output_handle(solid_output_handle)
                for solid_output_handle in solid_output_handles
            ],
        )

    if solid.container_maps_input(input_name):
        parent_name = solid.container_mapped_input(input_name).definition.name
        parent_inputs = {step_input.name: step_input for step_input in parent_step_inputs}
        if parent_name in parent_inputs:
            parent_input = parent_inputs[parent_name]
            return StepInput(
                input_name,
                input_def.runtime_type,
                parent_input.source_type,
                parent_input.source_handles,
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
    namedtuple(
        '_ExecutionPlan',
        'pipeline_def step_dict deps steps artifacts_persisted previous_run_id step_keys_to_execute',
    )
):
    def __new__(
        cls,
        pipeline_def,
        step_dict,
        deps,
        artifacts_persisted,
        previous_run_id,
        step_keys_to_execute,
    ):
        missing_steps = [step_key for step_key in step_keys_to_execute if step_key not in step_dict]
        if missing_steps:
            raise DagsterExecutionStepNotFoundError(
                'Execution plan does not contain step{plural}: {steps}'.format(
                    plural='s' if len(missing_steps) > 1 else '', steps=', '.join(missing_steps)
                ),
                step_keys=missing_steps,
            )
        return super(ExecutionPlan, cls).__new__(
            cls,
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            step_dict=check.dict_param(
                step_dict, 'step_dict', key_type=str, value_type=ExecutionStep
            ),
            deps=check.dict_param(deps, 'deps', key_type=str, value_type=set),
            steps=list(step_dict.values()),
            artifacts_persisted=check.bool_param(artifacts_persisted, 'artifacts_persisted'),
            previous_run_id=check.opt_str_param(previous_run_id, 'previous_run_id'),
            step_keys_to_execute=check.list_param(
                step_keys_to_execute, 'step_keys_to_execute', of_type=str
            ),
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
            [self.step_dict[step_key] for step_key in sorted(step_key_level)]
            for step_key_level in toposort(self.deps)
        ]

    def execution_step_levels(self):
        return [
            [self.step_dict[step_key] for step_key in sorted(step_key_level)]
            for step_key_level in toposort(self.execution_deps())
        ]

    def missing_steps(self):
        return [step_key for step_key in self.step_keys_to_execute if not self.has_step(step_key)]

    def execution_deps(self):
        deps = OrderedDict()

        for key in self.step_keys_to_execute:
            deps[key] = set()

        for key in self.step_keys_to_execute:
            step = self.step_dict[key]
            for step_input in step.step_inputs:
                deps[step.key].update(
                    step_input.dependency_keys.intersection(self.step_keys_to_execute)
                )
        return deps

    def build_subset_plan(self, step_keys_to_execute):
        check.list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)
        return ExecutionPlan(
            self.pipeline_def,
            self.step_dict,
            self.deps,
            self.artifacts_persisted,
            self.previous_run_id,
            step_keys_to_execute,
        )

    def start(self, sort_key_fn=None):
        return ActiveExecution(self, sort_key_fn)

    @staticmethod
    def build(pipeline_def, environment_config, run_config):
        '''Here we build a new ExecutionPlan from a pipeline definition and the environment config.

        To do this, we iterate through the pipeline's solids in topological order, and hand off the
        execution steps for each solid to a companion _PlanBuilder object.

        Once we've processed the entire pipeline, we invoke _PlanBuilder.build() to construct the
        ExecutionPlan object.
        '''
        check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
        check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
        check.inst_param(run_config, 'run_config', IRunConfig)

        plan_builder = _PlanBuilder(pipeline_def, environment_config, run_config)

        # Finally, we build and return the execution plan
        return plan_builder.build()


def _default_sort_key(step):
    return int(step.tags.get('dagster/priority', 0)) * -1


class ActiveExecution(object):
    def __init__(self, execution_plan, sort_key_fn=None):
        self._plan = check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
        self._sort_key_fn = check.opt_callable_param(sort_key_fn, 'sort_key_fn', _default_sort_key)

        self._pending = self._plan.execution_deps()

        self._completed = set()
        self._success = set()
        self._failed = set()
        self._skipped = set()

        self._in_flight = set()

        self._executable = []
        self._to_skip = []

        self._update()

    def _update(self):
        new_steps_to_execute = []
        new_steps_to_skip = []
        for step_key, requirements in self._pending.items():

            if requirements.issubset(self._completed):
                if requirements.issubset(self._success):
                    new_steps_to_execute.append(step_key)
                else:
                    new_steps_to_skip.append(step_key)

        for key in new_steps_to_execute:
            self._executable.append(key)
            del self._pending[key]

        for key in new_steps_to_skip:
            self._to_skip.append(key)
            del self._pending[key]

    def get_steps_to_execute(self, limit=None):
        check.opt_int_param(limit, 'limit')

        steps = sorted(
            [self._plan.get_step_by_key(key) for key in self._executable], key=self._sort_key_fn
        )

        if limit:
            steps = steps[:limit]

        for step in steps:
            self._in_flight.add(step.key)
            self._executable.remove(step.key)

        return steps

    def get_steps_to_skip(self):
        steps = []
        steps_to_skip = list(self._to_skip)
        for key in steps_to_skip:
            steps.append(self._plan.get_step_by_key(key))
            self._in_flight.add(key)
            self._to_skip.remove(key)

        return sorted(steps, key=self._sort_key_fn)

    def skipped_step_events_iterator(self, pipeline_context):
        failed_or_skipped_steps = self._skipped.union(self._failed)

        steps_to_skip = self.get_steps_to_skip()
        while steps_to_skip:
            for step in steps_to_skip:
                step_context = pipeline_context.for_step(step)
                failed_inputs = []
                for step_input in step.step_inputs:
                    failed_inputs.extend(
                        failed_or_skipped_steps.intersection(step_input.dependency_keys)
                    )

                step_context.log.info(
                    'Dependencies for step {step} failed: {failed_inputs}. Not executing.'.format(
                        step=step.key, failed_inputs=failed_inputs
                    )
                )
                yield DagsterEvent.step_skipped_event(step_context)

                self.mark_skipped(step.key)

            steps_to_skip = self.get_steps_to_skip()

    def mark_failed(self, step_key):
        self._failed.add(step_key)
        self._mark_complete(step_key)

    def mark_success(self, step_key):
        self._success.add(step_key)
        self._mark_complete(step_key)

    def mark_skipped(self, step_key):
        self._skipped.add(step_key)
        self._mark_complete(step_key)

    def _mark_complete(self, step_key):
        check.invariant(
            step_key not in self._completed,
            'Attempted to mark step {} as complete that was already completed'.format(step_key),
        )
        check.invariant(
            step_key in self._in_flight,
            'Attempted to mark step {} as complete that was not known to be in flight'.format(
                step_key
            ),
        )
        self._in_flight.remove(step_key)
        self._completed.add(step_key)
        self._update()

    @property
    def is_complete(self):
        return (
            len(self._pending) == 0
            and len(self._in_flight) == 0
            and len(self._executable) == 0
            and len(self._to_skip) == 0
        )
