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
from dagster.core.definitions.executor import ExecutorRequirement
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvariantViolationError,
    DagsterUnmetExecutorRequirementsError,
)
from dagster.core.execution.plan.handle import (
    ResolvedFromDynamicStepHandle,
    StepHandle,
    UnresolvedStepHandle,
)
from dagster.core.execution.retries import RetryMode, RetryState
from dagster.core.instance import DagsterInstance
from dagster.core.storage.mem_io_manager import mem_io_manager
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.types.dagster_type import DagsterTypeKind
from dagster.core.utils import toposort

from .compute import create_step_outputs
from .inputs import (
    FromConfig,
    FromDefaultValue,
    FromDynamicCollect,
    FromMultipleSources,
    FromPendingDynamicStepOutput,
    FromRootInputManager,
    FromStepOutput,
    FromUnresolvedStepOutput,
    StepInput,
    StepInputSource,
    UnresolvedCollectStepInput,
    UnresolvedMappedStepInput,
)
from .outputs import StepOutput, StepOutputHandle, UnresolvedStepOutputHandle
from .state import KnownExecutionState
from .step import (
    ExecutionStep,
    IExecutionStep,
    StepKind,
    UnresolvedCollectExecutionStep,
    UnresolvedMappedExecutionStep,
)

if TYPE_CHECKING:
    from .active import ActiveExecution

StepHandleTypes = (StepHandle, UnresolvedStepHandle, ResolvedFromDynamicStepHandle)
StepHandleUnion = Union[StepHandle, UnresolvedStepHandle, ResolvedFromDynamicStepHandle]


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
        step_keys_to_execute: Optional[List[str]],
        known_state,
    ):
        self.pipeline = check.inst_param(pipeline, "pipeline", IPipeline)
        self.environment_config = check.inst_param(
            environment_config, "environment_config", EnvironmentConfig
        )
        check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", str)
        self.step_keys_to_execute = step_keys_to_execute
        self.mode_definition = (
            pipeline.get_definition().get_mode_definition(environment_config.mode)
            if environment_config.mode is not None
            else pipeline.get_definition().get_default_mode()
        )
        self._steps: Dict[str, IExecutionStep] = OrderedDict()
        self.step_output_map: Dict[
            SolidOutputHandle, Union[StepOutputHandle, UnresolvedStepOutputHandle]
        ] = dict()
        self.known_state = known_state
        self._seen_handles: Set[StepHandleUnion] = set()

    @property
    def pipeline_name(self) -> str:
        return self.pipeline.get_definition().name

    def add_step(self, step: IExecutionStep) -> None:
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

    def get_step_by_solid_handle(self, handle: SolidHandle) -> IExecutionStep:
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

        _check_io_manager_intermediate_storage(self.mode_definition, self.environment_config)
        _check_persistent_storage_requirement(
            self.pipeline,
            self.mode_definition,
            self.environment_config,
        )

        pipeline_def = self.pipeline.get_definition()
        # Recursively build the execution plan starting at the root pipeline
        self._build_from_sorted_solids(
            pipeline_def.solids_in_topological_order,
            pipeline_def.dependency_structure,
        )

        step_dict = {step.handle: step for step in self._steps.values()}
        step_handles_to_execute = [step.handle for step in self._steps.values()]

        executable_map, resolvable_map = _compute_step_maps(
            step_dict,
            step_handles_to_execute,
            self.known_state,
        )

        full_plan = ExecutionPlan(
            step_dict,
            executable_map,
            resolvable_map,
            step_handles_to_execute,
            self.known_state,
            _compute_artifacts_persisted(
                step_dict,
                step_handles_to_execute,
                pipeline_def,
                self.environment_config,
                executable_map,
            ),
        )

        if self.step_keys_to_execute is not None:
            return full_plan.build_subset_plan(
                self.step_keys_to_execute, pipeline_def, self.environment_config
            )
        else:
            return full_plan

    def _build_from_sorted_solids(
        self,
        solids: List[Solid],
        dependency_structure: DependencyStructure,
        parent_handle: Optional[SolidHandle] = None,
        parent_step_inputs: Optional[
            List[Union[StepInput, UnresolvedMappedStepInput, UnresolvedCollectStepInput]]
        ] = None,
    ):
        for solid in solids:
            handle = SolidHandle(solid.name, parent_handle)

            ### 1. INPUTS
            # Create and add execution plan steps for solid inputs
            has_unresolved_input = False
            has_pending_input = False
            step_inputs: List[
                Union[StepInput, UnresolvedMappedStepInput, UnresolvedCollectStepInput]
            ] = []
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
                    step_input_source,
                    (FromPendingDynamicStepOutput, FromUnresolvedStepOutput),
                ):
                    has_unresolved_input = True
                    step_inputs.append(
                        UnresolvedMappedStepInput(
                            name=input_name,
                            dagster_type_key=input_def.dagster_type.key,
                            source=step_input_source,
                        )
                    )
                elif isinstance(step_input_source, FromDynamicCollect):
                    has_pending_input = True
                    step_inputs.append(
                        UnresolvedCollectStepInput(
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

                if has_pending_input and has_unresolved_input:
                    check.failed("Can not have pending and unresolved step inputs")

                elif has_unresolved_input:
                    new_step: IExecutionStep = UnresolvedMappedExecutionStep(
                        handle=UnresolvedStepHandle(solid_handle=handle),
                        pipeline_name=self.pipeline_name,
                        step_inputs=cast(
                            List[Union[StepInput, UnresolvedMappedStepInput]], step_inputs
                        ),
                        step_outputs=step_outputs,
                        tags=solid.tags,
                    )
                elif has_pending_input:
                    new_step = UnresolvedCollectExecutionStep(
                        handle=StepHandle(solid_handle=handle),
                        pipeline_name=self.pipeline_name,
                        step_inputs=cast(
                            List[Union[StepInput, UnresolvedCollectStepInput]], step_inputs
                        ),
                        step_outputs=step_outputs,
                        tags=solid.tags,
                    )
                else:
                    new_step = ExecutionStep(
                        handle=StepHandle(solid_handle=handle),
                        pipeline_name=self.pipeline_name,
                        step_inputs=cast(List[StepInput], step_inputs),
                        step_outputs=step_outputs,
                        tags=solid.tags,
                    )

                self.add_step(new_step)

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
                if isinstance(step, (ExecutionStep, UnresolvedCollectExecutionStep)):
                    step_output_handle: Union[
                        StepOutputHandle, UnresolvedStepOutputHandle
                    ] = StepOutputHandle(step.key, resolved_output_def.name)
                elif isinstance(step, UnresolvedMappedExecutionStep):
                    step_output_handle = UnresolvedStepOutputHandle(
                        step.handle,
                        resolved_output_def.name,
                        step.resolved_by_step_key,
                        step.resolved_by_output_name,
                    )
                else:
                    check.failed(f"Unexpected step type {step}")

                self.set_output_handle(output_handle, step_output_handle)


def get_step_input_source(
    plan_builder: _PlanBuilder,
    solid: Solid,
    input_name: str,
    input_def: InputDefinition,
    dependency_structure: DependencyStructure,
    handle: SolidHandle,
    parent_step_inputs: Optional[
        List[Union[StepInput, UnresolvedMappedStepInput, UnresolvedCollectStepInput]]
    ],
):
    check.inst_param(plan_builder, "plan_builder", _PlanBuilder)
    check.inst_param(solid, "solid", Solid)
    check.str_param(input_name, "input_name")
    check.inst_param(input_def, "input_def", InputDefinition)
    check.inst_param(dependency_structure, "dependency_structure", DependencyStructure)
    check.opt_inst_param(handle, "handle", SolidHandle)
    check.opt_list_param(
        parent_step_inputs,
        "parent_step_inputs",
        of_type=(StepInput, UnresolvedMappedStepInput, UnresolvedCollectStepInput),
    )

    input_handle = solid.input_handle(input_name)
    solid_config = plan_builder.environment_config.solids.get(str(handle))

    input_def = solid.definition.input_def_named(input_name)
    if input_def.root_manager_key and not dependency_structure.has_deps(input_handle):
        return FromRootInputManager(solid_handle=handle, input_name=input_name)

    if dependency_structure.has_direct_dep(input_handle):
        solid_output_handle = dependency_structure.get_direct_dep(input_handle)
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

    if dependency_structure.has_fan_in_deps(input_handle):
        sources: List[StepInputSource] = []
        deps = dependency_structure.get_fan_in_deps(input_handle)
        for idx, handle_or_placeholder in enumerate(deps):
            if isinstance(handle_or_placeholder, SolidOutputHandle):
                step_output_handle = plan_builder.get_output_handle(handle_or_placeholder)
                if (
                    isinstance(step_output_handle, UnresolvedStepOutputHandle)
                    or handle_or_placeholder.output_def.is_dynamic
                ):
                    check.failed(
                        "Unexpected dynamic output dependency in regular fan in, "
                        "should have been caught at definition time."
                    )

                sources.append(
                    FromStepOutput(
                        step_output_handle=step_output_handle,
                        solid_handle=handle,
                        input_name=input_name,
                        fan_in=True,
                    )
                )
            else:
                check.invariant(
                    handle_or_placeholder is MappedInputPlaceholder,
                    f"Expected SolidOutputHandle or MappedInputPlaceholder, got {handle_or_placeholder}",
                )
                if parent_step_inputs is None:
                    check.failed("unexpected error in composition descent during plan building")

                parent_name = solid.container_mapped_fan_in_input(input_name, idx).definition.name
                parent_inputs = {step_input.name: step_input for step_input in parent_step_inputs}
                parent_input = parent_inputs[parent_name]
                source = parent_input.source
                if not isinstance(source, StepInputSource):
                    check.failed(f"Unexpected parent mapped input source type {source}")
                sources.append(source)

        return FromMultipleSources(solid_handle=handle, input_name=input_name, sources=sources)

    if dependency_structure.has_dynamic_fan_in_dep(input_handle):
        solid_output_handle = dependency_structure.get_dynamic_fan_in_dep(input_handle)
        step_output_handle = plan_builder.get_output_handle(solid_output_handle)
        if isinstance(step_output_handle, UnresolvedStepOutputHandle):
            return FromDynamicCollect(
                solid_handle=handle,
                input_name=input_name,
                source=FromUnresolvedStepOutput(
                    unresolved_step_output_handle=step_output_handle,
                    solid_handle=handle,
                    input_name=input_name,
                ),
            )
        elif solid_output_handle.output_def.is_dynamic:
            return FromDynamicCollect(
                solid_handle=handle,
                input_name=input_name,
                source=FromPendingDynamicStepOutput(
                    step_output_handle=step_output_handle,
                    solid_handle=handle,
                    input_name=input_name,
                ),
            )

    if solid_config and input_name in solid_config.inputs:
        return FromConfig(solid_handle=handle, input_name=input_name)

    if solid.container_maps_input(input_name):
        if parent_step_inputs is None:
            check.failed("unexpected error in composition descent during plan building")

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
            ("step_dict", Dict[StepHandleUnion, IExecutionStep]),
            ("executable_map", Dict[str, Union[StepHandle, ResolvedFromDynamicStepHandle]]),
            ("resolvable_map", Dict[FrozenSet[str], List[UnresolvedStepHandle]]),
            ("step_handles_to_execute", List[StepHandleUnion]),
            ("known_state", KnownExecutionState),
            ("artifacts_persisted", bool),
        ],
    )
):
    def __new__(
        cls,
        step_dict,
        executable_map,
        resolvable_map,
        step_handles_to_execute,
        known_state=None,
        artifacts_persisted=False,
    ):
        return super(ExecutionPlan, cls).__new__(
            cls,
            step_dict=check.dict_param(
                step_dict,
                "step_dict",
                key_type=StepHandleTypes,
                value_type=(
                    ExecutionStep,
                    UnresolvedMappedExecutionStep,
                    UnresolvedCollectExecutionStep,
                ),
            ),
            executable_map=executable_map,
            resolvable_map=resolvable_map,
            step_handles_to_execute=check.list_param(
                step_handles_to_execute,
                "step_handles_to_execute",
                of_type=(StepHandle, UnresolvedStepHandle, ResolvedFromDynamicStepHandle),
            ),
            known_state=check.opt_inst_param(known_state, "known_state", KnownExecutionState),
            artifacts_persisted=check.bool_param(artifacts_persisted, "artifacts_persisted"),
        )

    @property
    def steps(self) -> List[IExecutionStep]:
        return list(self.step_dict.values())

    @property
    def step_keys_to_execute(self) -> List[str]:
        return [handle.to_key() for handle in self.step_handles_to_execute]

    def get_step_output(self, step_output_handle: StepOutputHandle) -> StepOutput:
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        return _get_step_output(self.step_dict, step_output_handle)

    def get_manager_key(
        self,
        step_output_handle: StepOutputHandle,
        pipeline_def: PipelineDefinition,
    ) -> str:
        return _get_manager_key(self.step_dict, step_output_handle, pipeline_def)

    def has_step(self, handle: StepHandleUnion) -> bool:
        check.inst_param(handle, "handle", StepHandleTypes)
        return handle in self.step_dict

    def get_step(self, handle: StepHandleUnion) -> IExecutionStep:
        check.inst_param(handle, "handle", StepHandleTypes)
        return self.step_dict[handle]

    def get_step_by_key(self, key: str) -> IExecutionStep:
        return _get_step_by_key(self.step_dict, key)

    def get_executable_step_by_key(self, key: str) -> ExecutionStep:
        step = self.get_step_by_key(key)
        return cast(ExecutionStep, check.inst(step, ExecutionStep))

    def get_all_steps_in_topo_order(self) -> List[IExecutionStep]:
        return [step for step_level in self.get_all_steps_by_level() for step in step_level]

    def get_all_steps_by_level(self) -> List[List[IExecutionStep]]:
        return [
            [self.get_step_by_key(step_key) for step_key in sorted(step_key_level)]
            for step_key_level in toposort(self.get_all_step_deps())
        ]

    def get_all_step_deps(self) -> Dict[str, Set[str]]:
        deps = OrderedDict()
        for step in self.step_dict.values():
            if isinstance(step, ExecutionStep):
                deps[step.key] = step.get_execution_dependency_keys()
            elif isinstance(step, UnresolvedMappedExecutionStep):
                deps[step.key] = step.get_all_dependency_keys()
            else:
                check.failed(f"Unexpected execution step type {step}")

        return deps

    def get_steps_to_execute_in_topo_order(self) -> List[ExecutionStep]:
        return [step for step_level in self.get_steps_to_execute_by_level() for step in step_level]

    def get_steps_to_execute_by_level(self) -> List[List[ExecutionStep]]:
        return _get_steps_to_execute_by_level(
            self.step_dict, self.step_handles_to_execute, self.executable_map
        )

    def get_executable_step_deps(self) -> Dict[str, Set[str]]:
        return _get_executable_step_deps(
            self.step_dict, self.step_handles_to_execute, self.executable_map
        )

    def resolve(
        self,
        mappings: Dict[str, Dict[str, List[str]]],
    ) -> Dict[str, Set[str]]:
        """Resolve any dynamic map or collect steps with the resolved dynamic mappings"""

        previous = self.get_executable_step_deps()

        _update_from_resolved_dynamic_outputs(
            self.step_dict,
            self.executable_map,
            self.resolvable_map,
            self.step_handles_to_execute,
            mappings,
        )

        after = self.get_executable_step_deps()

        return {key: deps for key, deps in after.items() if key not in previous}

    def build_subset_plan(
        self,
        step_keys_to_execute: List[str],
        pipeline_def: PipelineDefinition,
        environment_config: EnvironmentConfig,
    ) -> "ExecutionPlan":
        check.list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
        step_handles_to_execute = [StepHandle.parse_from_key(key) for key in step_keys_to_execute]

        bad_keys = []
        for handle in step_handles_to_execute:
            if handle not in self.step_dict:
                bad_keys.append(handle.to_key())

        if bad_keys:
            raise DagsterExecutionStepNotFoundError(
                f"Can not build subset plan from unknown step{'s' if len(bad_keys)> 1 else ''}: {', '.join(bad_keys)}",
                step_keys=bad_keys,
            )

        executable_map, resolvable_map = _compute_step_maps(
            self.step_dict,
            step_handles_to_execute,
            self.known_state,
        )

        return ExecutionPlan(
            self.step_dict,
            executable_map,
            resolvable_map,
            step_handles_to_execute,
            self.known_state,
            _compute_artifacts_persisted(
                self.step_dict,
                step_handles_to_execute,
                pipeline_def,
                environment_config,
                executable_map,
            ),
        )

    def start(
        self,
        retry_mode: RetryMode,
        sort_key_fn: Optional[Callable[[ExecutionStep], float]] = None,
    ) -> "ActiveExecution":
        from .active import ActiveExecution

        return ActiveExecution(
            self,
            retry_mode,
            self.known_state.get_retry_state() if self.known_state else RetryState(),
            sort_key_fn,
        )

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
        step_keys_to_execute: Optional[List[str]] = None,
        known_state=None,
    ) -> "ExecutionPlan":
        """Here we build a new ExecutionPlan from a pipeline definition and the environment config.

        To do this, we iterate through the pipeline's solids in topological order, and hand off the
        execution steps for each solid to a companion _PlanBuilder object.

        Once we've processed the entire pipeline, we invoke _PlanBuilder.build() to construct the
        ExecutionPlan object.
        """
        check.inst_param(pipeline, "pipeline", IPipeline)
        check.inst_param(environment_config, "environment_config", EnvironmentConfig)
        check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
        check.opt_inst_param(known_state, "known_state", KnownExecutionState)

        plan_builder = _PlanBuilder(
            pipeline,
            environment_config=environment_config,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
        )

        # Finally, we build and return the execution plan
        return plan_builder.build()

    @staticmethod
    def rebuild_step_input(step_input_snap):
        from dagster.core.snap.execution_plan_snapshot import ExecutionStepInputSnap

        check.inst_param(step_input_snap, "step_input_snap", ExecutionStepInputSnap)

        step_input_source = step_input_snap.source

        if isinstance(
            step_input_source,
            (FromPendingDynamicStepOutput, FromUnresolvedStepOutput),
        ):
            return UnresolvedMappedStepInput(
                step_input_snap.name,
                step_input_snap.dagster_type_key,
                step_input_snap.source,
            )
        elif isinstance(step_input_source, FromDynamicCollect):
            return UnresolvedCollectStepInput(
                step_input_snap.name,
                step_input_snap.dagster_type_key,
                step_input_snap.source,
            )
        else:
            check.inst_param(step_input_source, "step_input_source", StepInputSource)
            return StepInput(
                step_input_snap.name,
                step_input_snap.dagster_type_key,
                step_input_snap.source,
            )

    @staticmethod
    def rebuild_from_snapshot(pipeline_name, execution_plan_snapshot):
        if not execution_plan_snapshot.can_reconstruct_plan:
            raise DagsterInvariantViolationError(
                "Tried to reconstruct an old ExecutionPlanSnapshot that was created before snapshots "
                "had enough information to fully reconstruct the ExecutionPlan"
            )

        step_dict = {}

        for step_snap in execution_plan_snapshot.steps:
            input_snaps = step_snap.inputs
            output_snaps = step_snap.outputs

            step_inputs = [
                ExecutionPlan.rebuild_step_input(step_input_snap) for step_input_snap in input_snaps
            ]

            step_outputs = [
                StepOutput(
                    step_output_snap.solid_handle,
                    step_output_snap.name,
                    step_output_snap.dagster_type_key,
                    step_output_snap.properties,
                )
                for step_output_snap in output_snaps
            ]

            if step_snap.kind == StepKind.COMPUTE:
                step = ExecutionStep(
                    step_snap.step_handle,
                    pipeline_name,
                    step_inputs,
                    step_outputs,
                    step_snap.tags,
                )
            elif step_snap.kind == StepKind.UNRESOLVED_MAPPED:
                step = UnresolvedMappedExecutionStep(
                    step_snap.step_handle,
                    pipeline_name,
                    step_inputs,
                    step_outputs,
                    step_snap.tags,
                )
            elif step_snap.kind == StepKind.UNRESOLVED_COLLECT:
                step = UnresolvedCollectExecutionStep(
                    step_snap.step_handle,
                    pipeline_name,
                    step_inputs,
                    step_outputs,
                    step_snap.tags,
                )
            else:
                raise Exception(f"Unexpected step kind {str(step_snap.kind)}")

            step_dict[step.handle] = step

        step_handles_to_execute = [
            StepHandle.parse_from_key(key) for key in execution_plan_snapshot.step_keys_to_execute
        ]

        executable_map, resolvable_map = _compute_step_maps(
            step_dict,
            step_handles_to_execute,
            execution_plan_snapshot.initial_known_state,
        )

        return ExecutionPlan(
            step_dict,
            executable_map,
            resolvable_map,
            step_handles_to_execute,
            execution_plan_snapshot.initial_known_state,
            execution_plan_snapshot.artifacts_persisted,
        )


def _update_from_resolved_dynamic_outputs(
    step_dict: Dict[StepHandleUnion, IExecutionStep],
    executable_map: Dict[str, Union[StepHandle, ResolvedFromDynamicStepHandle]],
    resolvable_map: Dict[FrozenSet[str], List[UnresolvedStepHandle]],
    step_handles_to_execute: List[StepHandleUnion],
    dynamic_mappings: Dict[str, Dict[str, List[str]]],
) -> None:
    resolved_steps = []
    key_sets_to_clear = []

    # find entries in the resolvable map whose requirements are now all ready
    for required_keys, unresolved_step_handles in resolvable_map.items():
        if not all(key in dynamic_mappings for key in required_keys):
            continue

        key_sets_to_clear.append(required_keys)

        for unresolved_step_handle in unresolved_step_handles:
            # don't resolve steps we are not executing
            if unresolved_step_handle not in step_handles_to_execute:
                continue

            resolvable_step = step_dict[unresolved_step_handle]

            if isinstance(resolvable_step, UnresolvedMappedExecutionStep):
                resolved_steps += resolvable_step.resolve(dynamic_mappings)
            elif isinstance(resolvable_step, UnresolvedCollectExecutionStep):
                resolved_steps.append(resolvable_step.resolve(dynamic_mappings))

    # update structures
    for step in resolved_steps:
        step_dict[step.handle] = step
        executable_map[step.key] = step.handle

    for key_set in key_sets_to_clear:
        del resolvable_map[key_set]


def _all_outputs_non_mem_io_managers(pipeline_def: PipelineDefinition, mode_def: ModeDefinition):
    """Returns true if every output definition in the pipeline uses an IO manager that's not
    the mem_io_manager.

    If true, this indicates that it's OK to execute steps in their own processes, because their
    outputs will be available to other processes.
    """
    # pylint: disable=comparison-with-callable

    output_defs = [
        output_def
        for solid_def in pipeline_def.all_solid_defs
        for output_def in solid_def.output_defs
    ]
    for output_def in output_defs:
        if mode_def.resource_defs[output_def.io_manager_key] == mem_io_manager:
            return False

    return True


def _check_persistent_storage_requirement(
    pipeline: IPipeline,
    mode_def: ModeDefinition,
    environment_config: EnvironmentConfig,
) -> None:
    from dagster.core.execution.context_creation_pipeline import executor_def_from_config

    pipeline_def = pipeline.get_definition()
    executor_def = executor_def_from_config(mode_def, environment_config)
    if ExecutorRequirement.PERSISTENT_OUTPUTS not in executor_def.requirements:
        return

    intermediate_storage_def = environment_config.intermediate_storage_def_for_mode(mode_def)

    if not (
        _all_outputs_non_mem_io_managers(pipeline_def, mode_def)
        or (intermediate_storage_def and intermediate_storage_def.is_persistent)
    ):
        raise DagsterUnmetExecutorRequirementsError(
            "You have attempted to use an executor that uses multiple processes, but your pipeline "
            "includes solid outputs that will not be stored somewhere where other processes can "
            "retrieve them. Please use a persistent IO manager for these outputs. E.g. with\n"
            '    @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})])'
        )


def _check_io_manager_intermediate_storage(
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
        if len(missing_source_handles) > 0 and len(missing_source_handles) == len(
            step_input.get_step_output_handle_dependencies()
        ):
            return True

    return False


def _compute_artifacts_persisted(
    step_dict, step_handles_to_execute, pipeline_def, environment_config, executable_map
):
    """
    Check if all the border steps of the current run have non-in-memory IO managers for reexecution.

    Border steps: all the steps that don't have upstream steps to execute, i.e. indegree is 0).
    """
    # pylint: disable=comparison-with-callable

    # intermediate storage backcomopat
    # https://github.com/dagster-io/dagster/issues/3043

    mode_def = pipeline_def.get_mode_definition(environment_config.mode)

    if mode_def.get_intermediate_storage_def(
        environment_config.intermediate_storage.intermediate_storage_name
    ).is_persistent:
        return True

    if len(step_dict) == 0:
        return False

    steps_by_level = _get_steps_to_execute_by_level(
        step_dict, step_handles_to_execute, executable_map
    )

    if len(steps_by_level) == 0:
        return False

    for step in steps_by_level[0]:
        # check if all its inputs' upstream step outputs have non-in-memory IO manager configured
        for step_input in step.step_inputs:
            for step_output_handle in step_input.get_step_output_handle_dependencies():
                io_manager_key = _get_manager_key(step_dict, step_output_handle, pipeline_def)
                manager_def = mode_def.resource_defs.get(io_manager_key)
                if (
                    # no IO manager is configured
                    not manager_def
                    # IO manager is non persistent
                    or manager_def == mem_io_manager
                ):
                    return False
    return True


def _get_step_by_key(step_dict, key) -> IExecutionStep:
    check.str_param(key, "key")
    for step in step_dict.values():
        if step.key == key:
            return step
    check.failed(f"plan has no step with key {key}")


def _get_steps_to_execute_by_level(step_dict, step_handles_to_execute, executable_map):
    return [
        [
            cast(ExecutionStep, _get_step_by_key(step_dict, step_key))
            for step_key in sorted(step_key_level)
        ]
        for step_key_level in toposort(
            _get_executable_step_deps(step_dict, step_handles_to_execute, executable_map)
        )
    ]


def _get_executable_step_deps(
    step_dict, step_handles_to_execute, executable_map
) -> Dict[str, Set[str]]:
    """
    Returns:
        Dict[str, Set[str]]: Maps step keys to sets of step keys that they depend on. Includes
            only steps that are included in step_handles_to_execute.
    """
    deps = OrderedDict()

    # for things transitively downstream of unresolved collect steps
    unresolved_set = set()

    step_keys_to_execute = [handle.to_key() for handle in step_handles_to_execute]

    for key, handle in executable_map.items():
        step = cast(ExecutionStep, step_dict[handle])
        filtered_deps = []
        depends_on_unresolved = False
        for dep in step.get_execution_dependency_keys():
            if dep in executable_map and dep not in unresolved_set:
                filtered_deps.append(dep)
            elif dep in step_keys_to_execute:
                depends_on_unresolved = True

        if not depends_on_unresolved:
            deps[key] = set(filtered_deps)
        else:
            unresolved_set.add(key)

    return deps


def _get_step_output(step_dict, step_output_handle: StepOutputHandle) -> StepOutput:
    check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
    step = _get_step_by_key(step_dict, step_output_handle.step_key)
    return step.step_output_named(step_output_handle.output_name)


def _get_manager_key(step_dict, step_output_handle, pipeline_def):
    step_output = _get_step_output(step_dict, step_output_handle)
    solid_handle = step_output.solid_handle
    output_def = pipeline_def.get_solid(solid_handle).output_def_named(step_output.name)
    return output_def.io_manager_key


# computes executable_map and resolvable_map and returns them as a tuple. Also
# may modify the passed in step_dict to include resolved step using known_state.
def _compute_step_maps(step_dict, step_handles_to_execute, known_state):
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

    step_keys_to_execute = [step_handle.to_key() for step_handle in step_handles_to_execute]

    executable_map = {}
    resolvable_map: Dict[str, List[UnresolvedStepHandle]] = defaultdict(list)
    for handle in step_handles_to_execute:
        step = step_dict[handle]
        if isinstance(step, ExecutionStep):
            executable_map[step.key] = step.handle
        elif isinstance(step, (UnresolvedMappedExecutionStep, UnresolvedCollectExecutionStep)):
            for key in step.resolved_by_step_keys:
                if key not in step_keys_to_execute:
                    raise DagsterInvariantViolationError(
                        f'Unresolved ExecutionStep "{step.key}" is resolved by "{step.resolved_by_step_key}" '
                        "which is not part of the current step selection"
                    )

            resolvable_map[step.resolved_by_step_keys].append(step.handle)
        else:
            check.invariant(
                step.key in executable_map, "Expect all steps to be executable or resolvable"
            )

    if known_state:
        _update_from_resolved_dynamic_outputs(
            step_dict,
            executable_map,
            resolvable_map,
            step_handles_to_execute,
            known_state.dynamic_mappings,
        )

    return (executable_map, resolvable_map)
