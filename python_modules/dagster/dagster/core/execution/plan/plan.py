from collections import OrderedDict, defaultdict
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    FrozenSet,
    List,
    NamedTuple,
    Optional,
    Set,
    Union,
    cast,
)

from dagster import check
from dagster.core.definitions import (
    GraphDefinition,
    IPipeline,
    InputDefinition,
    Solid,
    SolidDefinition,
    SolidHandle,
    SolidOutputHandle,
)
from dagster.core.definitions.composition import MappedInputPlaceholder
from dagster.core.definitions.dependency import DependencyStructure
from dagster.core.definitions.hook import HookDefinition
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.errors import DagsterExecutionStepNotFoundError, DagsterInvariantViolationError
from dagster.core.execution.plan.handle import (
    ResolvedFromDynamicStepHandle,
    StepHandle,
    UnresolvedStepHandle,
)
from dagster.core.execution.resolve_versions import (
    resolve_step_output_versions_helper,
    resolve_step_versions_helper,
)
from dagster.core.execution.retries import Retries
from dagster.core.instance import DagsterInstance
from dagster.core.storage.mem_io_manager import mem_io_manager
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.types.dagster_type import DagsterTypeKind
from dagster.core.utils import toposort

from .compute import create_step_outputs
from .inputs import (
    FromConfig,
    FromDefaultValue,
    FromMultipleSources,
    FromPendingDynamicStepOutput,
    FromRootInputManager,
    FromStepOutput,
    FromUnresolvedStepOutput,
    StepInput,
    StepInputSource,
    UnresolvedStepInput,
)
from .outputs import StepOutput, StepOutputHandle, UnresolvedStepOutputHandle
from .step import ExecutionStep, UnresolvedExecutionStep

if TYPE_CHECKING:
    from .active import ActiveExecution

StepHandleTypes = (StepHandle, UnresolvedStepHandle, ResolvedFromDynamicStepHandle)
StepHandleUnion = Union[StepHandle, UnresolvedStepHandle, ResolvedFromDynamicStepHandle]
ExecutionStepUnion = Union[ExecutionStep, UnresolvedExecutionStep]


class _PlanBuilder:
    """_PlanBuilder. This is the state that is built up during the execution plan build process.

    steps List[ExecutionStep]: a list of the execution steps that have been created.

    step_output_map Dict[SolidOutputHandle, StepOutputHandle]:  maps logical solid outputs
    (solid_name, output_name) to particular step outputs. This covers the case where a solid maps to
    multiple steps and one wants to be able to attach to the logical output of a solid during
    execution.
    """

    def __init__(
        self,
        pipeline: IPipeline,
        environment_config: EnvironmentConfig,
        mode: Optional[str],
        step_keys_to_execute: Optional[List[str]],
    ):
        self.pipeline = check.inst_param(pipeline, "pipeline", IPipeline)
        self.environment_config = check.inst_param(
            environment_config, "environment_config", EnvironmentConfig
        )
        check.opt_str_param(mode, "mode")
        check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", str)
        self.step_keys_to_execute = step_keys_to_execute
        self.mode_definition = (
            pipeline.get_definition().get_mode_definition(mode)
            if mode is not None
            else pipeline.get_definition().get_default_mode()
        )
        self._steps: Dict[str, ExecutionStepUnion] = OrderedDict()
        self.step_output_map: Dict[
            SolidOutputHandle, Union[StepOutputHandle, UnresolvedStepOutputHandle]
        ] = dict()
        self._seen_handles: Set[StepHandleUnion] = set()

    @property
    def pipeline_name(self) -> str:
        return self.pipeline.get_definition().name

    def add_step(self, step: ExecutionStepUnion) -> None:
        # Keep track of the step keys we've seen so far to ensure we don't add duplicates
        if step.handle in self._seen_handles:
            keys = list(self._steps.keys())
            check.failed(
                "Duplicated key {key}. Full list seen so far: {key_list}.".format(
                    key=step.key, key_list=keys
                )
            )
        self._seen_handles.add(step.handle)
        self._steps[step.solid_handle.to_string()] = step

    def get_step_by_solid_handle(self, handle: SolidHandle) -> ExecutionStepUnion:
        check.inst_param(handle, "handle", SolidHandle)
        return self._steps[handle.to_string()]

    def get_output_handle(
        self, key: SolidOutputHandle
    ) -> Union[StepOutputHandle, UnresolvedStepOutputHandle]:
        check.inst_param(key, "key", SolidOutputHandle)
        return self.step_output_map[key]

    def set_output_handle(
        self, key: SolidOutputHandle, val: Union[StepOutputHandle, UnresolvedStepOutputHandle]
    ) -> None:
        check.inst_param(key, "key", SolidOutputHandle)
        check.inst_param(val, "val", (StepOutputHandle, UnresolvedStepOutputHandle))
        self.step_output_map[key] = val

    def build(self) -> "ExecutionPlan":
        """Builds the execution plan"""
        check_io_manager_intermediate_storage(self.mode_definition, self.environment_config)

        pipeline_def = self.pipeline.get_definition()
        # Recursively build the execution plan starting at the root pipeline
        self._build_from_sorted_solids(
            pipeline_def.solids_in_topological_order, pipeline_def.dependency_structure
        )

        full_plan = ExecutionPlan(
            self.pipeline,
            {step.handle: step for step in self._steps.values()},
            [step.handle for step in self._steps.values()],
            self.environment_config,
        )

        if self.step_keys_to_execute is not None:
            return full_plan.build_subset_plan(self.step_keys_to_execute)
        else:
            return full_plan

    def storage_is_persistent(self) -> bool:
        return self.mode_definition.get_intermediate_storage_def(
            self.environment_config.intermediate_storage.intermediate_storage_name
        ).is_persistent

    def _build_from_sorted_solids(
        self,
        solids: List[Solid],
        dependency_structure: DependencyStructure,
        parent_handle: Optional[SolidHandle] = None,
        parent_step_inputs: Optional[List[Union[StepInput, UnresolvedStepInput]]] = None,
    ):
        for solid in solids:
            handle = SolidHandle(solid.name, parent_handle)

            ### 1. INPUTS
            # Create and add execution plan steps for solid inputs
            has_unresolved_input = False
            step_inputs: List[Union[StepInput, UnresolvedStepInput]] = []
            for input_name, input_def in solid.definition.input_dict.items():
                step_input_source = get_step_input_source(
                    self,
                    solid,
                    input_name,
                    input_def,
                    dependency_structure,
                    handle,
                    parent_step_inputs,
                )

                # If an input with dagster_type "Nothing" doesn't have a value
                # we don't create a StepInput
                if step_input_source is None:
                    continue

                if isinstance(
                    step_input_source, (FromPendingDynamicStepOutput, FromUnresolvedStepOutput)
                ):
                    has_unresolved_input = True
                    step_inputs.append(
                        UnresolvedStepInput(
                            name=input_name,
                            dagster_type_key=input_def.dagster_type.key,
                            source=step_input_source,
                        )
                    )
                else:
                    check.inst_param(step_input_source, "step_input_source", StepInputSource)
                    step_inputs.append(
                        StepInput(
                            name=input_name,
                            dagster_type_key=input_def.dagster_type.key,
                            source=step_input_source,
                        )
                    )

            ### 2a. COMPUTE FUNCTION
            # Create and add execution plan step for the solid compute function
            if isinstance(solid.definition, SolidDefinition):
                step_outputs = create_step_outputs(solid, handle, self.environment_config)
                tags = solid.definition.tags

                if has_unresolved_input:
                    step: ExecutionStepUnion = UnresolvedExecutionStep(
                        handle=UnresolvedStepHandle(solid_handle=handle),
                        pipeline_name=self.pipeline_name,
                        step_inputs=step_inputs,
                        step_outputs=step_outputs,
                        tags=tags,
                    )
                else:
                    step = ExecutionStep(
                        handle=StepHandle(solid_handle=handle),
                        pipeline_name=self.pipeline_name,
                        step_inputs=cast(List[StepInput], step_inputs),
                        step_outputs=step_outputs,
                        tags=tags,
                    )

                self.add_step(step)

            ### 2b. RECURSE
            # Recurse over the solids contained in an instance of GraphDefinition
            elif isinstance(solid.definition, GraphDefinition):
                self._build_from_sorted_solids(
                    solid.definition.solids_in_topological_order,
                    solid.definition.dependency_structure,
                    parent_handle=handle,
                    parent_step_inputs=step_inputs,
                )

            else:
                check.invariant(
                    False,
                    "Unexpected solid type {type} encountered during execution planning".format(
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
                step = self.get_step_by_solid_handle(resolved_handle)
                if isinstance(step, ExecutionStep):
                    step_output_handle: Union[
                        StepOutputHandle, UnresolvedStepOutputHandle
                    ] = StepOutputHandle(step.key, resolved_output_def.name)
                else:
                    step_output_handle = UnresolvedStepOutputHandle(
                        step.handle,
                        resolved_output_def.name,
                        step.resolved_by_step_key,
                        step.resolved_by_output_name,
                    )

                self.set_output_handle(output_handle, step_output_handle)


def get_step_input_source(
    plan_builder, solid, input_name, input_def, dependency_structure, handle, parent_step_inputs
):
    check.inst_param(plan_builder, "plan_builder", _PlanBuilder)
    check.inst_param(solid, "solid", Solid)
    check.str_param(input_name, "input_name")
    check.inst_param(input_def, "input_def", InputDefinition)
    check.inst_param(dependency_structure, "dependency_structure", DependencyStructure)
    check.opt_inst_param(handle, "handle", SolidHandle)
    check.opt_list_param(
        parent_step_inputs, "parent_step_inputs", of_type=(StepInput, UnresolvedStepInput)
    )

    input_handle = solid.input_handle(input_name)
    solid_config = plan_builder.environment_config.solids.get(str(handle))

    input_def = solid.definition.input_def_named(input_name)
    if input_def.root_manager_key and not dependency_structure.has_deps(input_handle):
        return FromRootInputManager(solid_handle=handle, input_name=input_name)

    if dependency_structure.has_singular_dep(input_handle):
        solid_output_handle = dependency_structure.get_singular_dep(input_handle)
        step_output_handle = plan_builder.get_output_handle(solid_output_handle)
        if isinstance(step_output_handle, UnresolvedStepOutputHandle):
            return FromUnresolvedStepOutput(
                unresolved_step_output_handle=step_output_handle,
                solid_handle=handle,
                input_name=input_name,
            )

        if solid_output_handle.output_def.is_dynamic:
            return FromPendingDynamicStepOutput(
                step_output_handle=step_output_handle,
                solid_handle=handle,
                input_name=input_name,
            )

        return FromStepOutput(
            step_output_handle=step_output_handle,
            solid_handle=handle,
            input_name=input_name,
            fan_in=False,
        )

    if dependency_structure.has_multi_deps(input_handle):
        sources = []
        for idx, handle_or_placeholder in enumerate(
            dependency_structure.get_multi_deps(input_handle)
        ):
            if handle_or_placeholder is MappedInputPlaceholder:
                parent_name = solid.container_mapped_fan_in_input(input_name, idx).definition.name
                parent_inputs = {step_input.name: step_input for step_input in parent_step_inputs}
                parent_input = parent_inputs[parent_name]
                sources.append(parent_input.source)
            else:
                sources.append(
                    FromStepOutput(
                        step_output_handle=plan_builder.get_output_handle(handle_or_placeholder),
                        solid_handle=handle,
                        input_name=input_name,
                        fan_in=True,
                    )
                )

        return FromMultipleSources(solid_handle=handle, input_name=input_name, sources=sources)
    if solid_config and input_name in solid_config.inputs:
        return FromConfig(solid_handle=handle, input_name=input_name)

    if solid.container_maps_input(input_name):
        parent_name = solid.container_mapped_input(input_name).definition.name
        parent_inputs = {step_input.name: step_input for step_input in parent_step_inputs}
        if parent_name in parent_inputs:
            parent_input = parent_inputs[parent_name]
            return parent_input.source
        # else fall through to Nothing case or raise

    if solid.definition.input_has_default(input_name):
        return FromDefaultValue(solid_handle=handle, input_name=input_name)

    # At this point we have an input that is not hooked up to
    # the output of another solid or provided via environment config.

    # We will allow this for "Nothing" type inputs and continue.
    if input_def.dagster_type.kind == DagsterTypeKind.NOTHING:
        return None

    # Otherwise we throw an error.
    raise DagsterInvariantViolationError(
        (
            "In pipeline {pipeline_name} solid {solid_name}, input {input_name} "
            "must get a value either (a) from a dependency or (b) from the "
            "inputs section of its configuration."
        ).format(
            pipeline_name=plan_builder.pipeline_name, solid_name=solid.name, input_name=input_name
        )
    )


class ExecutionPlan(
    NamedTuple(
        "_ExecutionPlan",
        [
            ("pipeline", IPipeline),
            ("step_dict", Dict[StepHandleUnion, ExecutionStepUnion]),
            ("executable_map", Dict[str, Union[StepHandle, ResolvedFromDynamicStepHandle]]),
            ("resolvable_map", Dict[str, List[UnresolvedStepHandle]]),
            ("step_handles_to_execute", List[StepHandleUnion]),
            ("environment_config", EnvironmentConfig),
        ],
    )
):
    def __new__(
        cls,
        pipeline,
        step_dict,
        step_handles_to_execute,
        environment_config,
    ):
        check.list_param(
            step_handles_to_execute,
            "step_handles_to_execute",
            of_type=(StepHandle, UnresolvedStepHandle, ResolvedFromDynamicStepHandle),
        )
        missing_steps = [
            step_handle.to_key()
            for step_handle in step_handles_to_execute
            if step_handle not in step_dict
        ]
        if missing_steps:
            raise DagsterExecutionStepNotFoundError(
                "Execution plan does not contain step{plural}: {steps}".format(
                    plural="s" if len(missing_steps) > 1 else "", steps=", ".join(missing_steps)
                ),
                step_keys=missing_steps,
            )

        executable_map = {}
        for handle in step_handles_to_execute:
            step = step_dict[handle]
            if isinstance(step, ExecutionStep):
                executable_map[step.key] = step.handle

        resolvable_map: Dict[str, List[UnresolvedStepHandle]] = defaultdict(list)
        for handle in step_handles_to_execute:
            step = step_dict[handle]
            if isinstance(step, UnresolvedExecutionStep):
                if step.resolved_by_step_key not in executable_map:
                    raise DagsterInvariantViolationError(
                        f'UnresolvedExecutionStep "{step.key}" is resolved by "{step.resolved_by_step_key}" '
                        "which is not part of the current step selection"
                    )
                resolvable_map[step.resolved_by_step_key].append(step.handle)

        return super(ExecutionPlan, cls).__new__(
            cls,
            pipeline=check.inst_param(pipeline, "pipeline", IPipeline),
            step_dict=check.dict_param(
                step_dict,
                "step_dict",
                key_type=StepHandleTypes,
                value_type=(ExecutionStep, UnresolvedExecutionStep),
            ),
            executable_map=executable_map,
            resolvable_map=resolvable_map,
            step_handles_to_execute=step_handles_to_execute,
            environment_config=check.inst_param(
                environment_config, "environment_config", EnvironmentConfig
            ),
        )

    @property
    def steps(self) -> List[ExecutionStepUnion]:
        return list(self.step_dict.values())

    @property
    def step_keys_to_execute(self) -> List[str]:
        return [handle.to_key() for handle in self.step_handles_to_execute]

    @property
    def pipeline_def(self) -> PipelineDefinition:
        return self.pipeline.get_definition()

    def get_all_hook_defs(self) -> FrozenSet[HookDefinition]:
        hook_defs: Set[HookDefinition] = set()
        for step in self.steps:
            hook_defs = hook_defs.union(
                self.pipeline_def.get_all_hooks_for_handle(step.solid_handle)
            )
        return frozenset(hook_defs)

    def get_step_output(self, step_output_handle: StepOutputHandle) -> StepOutput:
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        step = self.get_step_by_key(step_output_handle.step_key)
        return step.step_output_named(step_output_handle.output_name)

    def get_manager_key(self, step_output_handle: StepOutputHandle) -> str:
        step_output = self.get_step_output(step_output_handle)
        solid_handle = step_output.solid_handle
        output_def = self.pipeline_def.get_solid(solid_handle).output_def_named(step_output.name)
        return output_def.io_manager_key

    def has_step(self, handle: StepHandleUnion) -> bool:
        check.inst_param(handle, "handle", StepHandleTypes)
        return handle in self.step_dict

    def get_step(self, handle: StepHandleUnion) -> ExecutionStepUnion:
        check.inst_param(handle, "handle", StepHandleTypes)
        return self.step_dict[handle]

    def get_step_by_key(self, key: str) -> ExecutionStepUnion:
        check.str_param(key, "key")
        for step in self.step_dict.values():
            if step.key == key:
                return step
        check.failed(f"plan has no step with key {key}")

    def get_executable_step_by_key(self, key: str) -> ExecutionStep:
        step = self.get_step_by_key(key)
        return cast(ExecutionStep, check.inst(step, ExecutionStep))

    def get_all_steps_in_topo_order(self) -> List[ExecutionStepUnion]:
        return [step for step_level in self.get_all_steps_by_level() for step in step_level]

    def get_all_steps_by_level(self) -> List[List[ExecutionStepUnion]]:
        return [
            [self.get_step_by_key(step_key) for step_key in sorted(step_key_level)]
            for step_key_level in toposort(self.get_all_step_deps())
        ]

    def get_all_step_deps(self) -> Dict[str, Set[str]]:
        deps = OrderedDict()
        for step in self.step_dict.values():
            if isinstance(step, ExecutionStep):
                deps[step.key] = step.get_execution_dependency_keys()
            elif isinstance(step, UnresolvedExecutionStep):
                deps[step.key] = step.get_all_dependency_keys()
            else:
                check.failed(f"Unexpected execution step type {step}")

        return deps

    def get_steps_to_execute_in_topo_order(self) -> List[ExecutionStep]:
        return [step for step_level in self.get_steps_to_execute_by_level() for step in step_level]

    def get_steps_to_execute_by_level(self) -> List[List[ExecutionStep]]:
        return [
            [
                cast(ExecutionStep, self.get_step_by_key(step_key))
                for step_key in sorted(step_key_level)
            ]
            for step_key_level in toposort(self.get_executable_step_deps())
        ]

    def get_executable_step_deps(self) -> Dict[str, Set[str]]:
        """
        Returns:
            Dict[str, Set[str]]: Maps step keys to sets of step keys that they depend on. Includes
                only steps that are included in step_keys_to_execute.
        """
        deps = OrderedDict()
        executable_keys = set(self.executable_map.keys())
        for key, handle in self.executable_map.items():
            step = cast(ExecutionStep, self.step_dict[handle])
            deps[key] = step.get_execution_dependency_keys().intersection(executable_keys)

        return deps

    def resolve(
        self, resolved_by_step_key: str, mappings: Dict[str, List[str]]
    ) -> Dict[str, Set[str]]:
        """Resolve UnresolvedExecutionSteps that depend on resolved_by_step_key, with the mapped output results"""
        check.str_param(resolved_by_step_key, "resolved_by_step_key")
        check.dict_param(mappings, "mappings", key_type=str, value_type=list)

        resolved_steps = []
        for unresolved_step_handle in self.resolvable_map[resolved_by_step_key]:
            # don't resolve steps we are not executing
            if unresolved_step_handle in self.step_handles_to_execute:
                unresolved_step = cast(
                    UnresolvedExecutionStep,
                    self.step_dict[unresolved_step_handle],
                )
                resolved_steps += unresolved_step.resolve(resolved_by_step_key, mappings)

        # update internal structures
        for step in resolved_steps:
            self.step_dict[step.handle] = step
            self.executable_map[step.key] = step.handle

        executable_keys = set(self.executable_map.keys())
        resolved_step_deps = {}
        for step in resolved_steps:
            # respect the plans step_handles_to_execute by intersecting against the executable keys
            resolved_step_deps[step.key] = step.get_execution_dependency_keys().intersection(
                executable_keys
            )

        return resolved_step_deps

    def build_subset_plan(self, step_keys_to_execute: List[str]) -> "ExecutionPlan":
        check.list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
        step_handles_to_execute = [StepHandle.parse_from_key(key) for key in step_keys_to_execute]

        bad_keys = []
        for handle in step_handles_to_execute:
            if handle in self.step_dict:
                pass  # no further processing required
            elif (
                isinstance(handle, ResolvedFromDynamicStepHandle)
                and handle.unresolved_form in self.step_dict
            ):
                unresolved_step = cast(
                    UnresolvedExecutionStep, self.step_dict[handle.unresolved_form]
                )
                # self.step_dict updated as side effect
                self.resolve(
                    unresolved_step.resolved_by_step_key,
                    {unresolved_step.resolved_by_output_name: [handle.mapping_key]},
                )
                check.invariant(
                    handle in self.step_dict,
                    f"Handle did not resolve as expected, not found in step dict {handle}",
                )
            else:
                bad_keys.append(handle.to_key())

        if bad_keys:
            raise DagsterExecutionStepNotFoundError(
                f"Can not build subset plan from unknown step{'s' if len(bad_keys)> 1 else ''}: {', '.join(bad_keys)}",
                step_keys=bad_keys,
            )

        return ExecutionPlan(
            self.pipeline,
            self.step_dict,
            step_handles_to_execute,
            self.environment_config,
        )

    def resolve_step_versions(self) -> Dict[str, Optional[str]]:
        return resolve_step_versions_helper(self)

    def resolve_step_output_versions(self) -> Dict[StepOutputHandle, Optional[str]]:
        return resolve_step_output_versions_helper(self)

    def start(
        self,
        retries: Retries,
        sort_key_fn: Optional[Callable[[ExecutionStep], float]] = None,
    ) -> "ActiveExecution":
        from .active import ActiveExecution

        return ActiveExecution(self, retries, sort_key_fn)

    def step_handle_for_single_step_plans(
        self,
    ) -> Optional[Union[StepHandle, ResolvedFromDynamicStepHandle]]:
        # Temporary hack to isolate single-step plans, which are often the representation of
        # sub-plans in a multiprocessing execution environment.  We want to attribute pipeline
        # events (like resource initialization) that are associated with the execution of these
        # single step sub-plans.  Most likely will be removed with the refactor detailed in
        # https://github.com/dagster-io/dagster/issues/2239
        if len(self.step_handles_to_execute) == 1:
            only_step = self.step_dict[self.step_handles_to_execute[0]]
            check.invariant(
                isinstance(only_step, ExecutionStep),
                "Unexpected unresolved single step plan",
            )
            return cast(ExecutionStep, only_step).handle

        return None

    @staticmethod
    def build(
        pipeline: IPipeline,
        environment_config: EnvironmentConfig,
        mode: Optional[str] = None,
        step_keys_to_execute: Optional[List[str]] = None,
    ) -> "ExecutionPlan":
        """Here we build a new ExecutionPlan from a pipeline definition and the environment config.

        To do this, we iterate through the pipeline's solids in topological order, and hand off the
        execution steps for each solid to a companion _PlanBuilder object.

        Once we've processed the entire pipeline, we invoke _PlanBuilder.build() to construct the
        ExecutionPlan object.
        """
        check.inst_param(pipeline, "pipeline", IPipeline)
        check.inst_param(environment_config, "environment_config", EnvironmentConfig)
        check.opt_str_param(mode, "mode")
        check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)

        plan_builder = _PlanBuilder(
            pipeline,
            environment_config,
            mode=mode,
            step_keys_to_execute=step_keys_to_execute,
        )

        # Finally, we build and return the execution plan
        return plan_builder.build()

    @property
    def storage_is_persistent(self) -> bool:
        mode_def = self.pipeline_def.get_mode_definition(self.environment_config.mode)
        return mode_def.get_intermediate_storage_def(
            self.environment_config.intermediate_storage.intermediate_storage_name
        ).is_persistent

    @property
    def artifacts_persisted(self) -> bool:
        """
        Check if all the border steps of the current run have non-in-memory IO managers for reexecution.

        Border steps: all the steps that don't have upstream steps to execute, i.e. indegree is 0).
        """
        # pylint: disable=comparison-with-callable

        # intermediate storage backcomopat
        # https://github.com/dagster-io/dagster/issues/3043
        if self.storage_is_persistent:
            return True

        # empty pipeline
        if len(self.steps) == 0:
            return False

        mode_def = self.pipeline_def.get_mode_definition(self.environment_config.mode)
        for step in self.get_steps_to_execute_by_level()[0]:
            # check if all its inputs' upstream step outputs have non-in-memory IO manager configured
            for step_input in step.step_inputs:
                for step_output_handle in step_input.get_step_output_handle_dependencies():
                    io_manager_key = self.get_manager_key(step_output_handle)
                    manager_def = mode_def.resource_defs.get(io_manager_key)
                    if (
                        # no IO manager is configured
                        not manager_def
                        # IO manager is non persistent
                        or manager_def == mem_io_manager
                    ):
                        return False
        return True


def check_io_manager_intermediate_storage(
    mode_def: ModeDefinition, environment_config: EnvironmentConfig
) -> None:
    """Only one of io_manager and intermediate_storage should be set."""
    # pylint: disable=comparison-with-callable
    from dagster.core.storage.system_storage import mem_intermediate_storage

    intermediate_storage_def = environment_config.intermediate_storage_def_for_mode(mode_def)
    intermediate_storage_is_default = (
        intermediate_storage_def is None or intermediate_storage_def == mem_intermediate_storage
    )

    io_manager = mode_def.resource_defs["io_manager"]
    io_manager_is_default = io_manager == mem_io_manager

    if not intermediate_storage_is_default and not io_manager_is_default:
        raise DagsterInvariantViolationError(
            'You have specified an intermediate storage, "{intermediate_storage_name}", and have '
            "also specified a default IO manager. You must specify only one. To avoid specifying "
            "an intermediate storage, omit the intermediate_storage_defs argument to your"
            'ModeDefinition and omit "intermediate_storage" in your run config. To avoid '
            'specifying a default IO manager, omit the "io_manager" key from the '
            "resource_defs argument to your ModeDefinition.".format(
                intermediate_storage_name=intermediate_storage_def.name
            )
        )


def should_skip_step(execution_plan: ExecutionPlan, instance: DagsterInstance, run_id: str) -> bool:
    """[INTERNAL] Check if it should skip executing the plan. Primarily used by execution without
    run-level plan process, e.g. Airflow step execution. Note: this only checks one step at a time.

    For each Dagster execution step
    - if none of its inputs come from optional outputs, do not skip
    - if there is at least one input, where none of the upstream steps have yielded an
      output, we should skip the step.
    """
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(instance, "instance", DagsterInstance)
    check.str_param(run_id, "run_id")

    # only checks one step at a time
    if len(execution_plan.step_keys_to_execute) != 1:
        return False

    step_key = execution_plan.step_keys_to_execute[0]
    optional_source_handles = set()
    step = execution_plan.get_executable_step_by_key(step_key)
    for step_input in step.step_inputs:
        for source_handle in step_input.get_step_output_handle_dependencies():
            if not execution_plan.get_step_output(source_handle).is_required:
                optional_source_handles.add(source_handle)

    # early terminate to avoid unnecessary instance/db calls
    if len(optional_source_handles) == 0:
        # do not skip when all the inputs come from non-optional outputs
        return False

    # find all yielded step outputs
    all_logs = instance.all_logs(run_id)
    yielded_step_output_handles = set()
    for event_record in all_logs:
        if event_record.dagster_event and event_record.dagster_event.is_successful_output:
            yielded_step_output_handles.add(
                event_record.dagster_event.event_specific_data.step_output_handle
            )

    # If there is at least one of the step's inputs, none of whose upstream steps has
    # yielded an output, we should skip that step.
    for step_input in step.step_inputs:
        missing_source_handles = [
            source_handle
            for source_handle in step_input.get_step_output_handle_dependencies()
            if source_handle in optional_source_handles
            and source_handle not in yielded_step_output_handles
        ]
        if len(missing_source_handles) == len(step_input.get_step_output_handle_dependencies()):
            return True

    return False
