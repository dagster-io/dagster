from collections import OrderedDict, defaultdict
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    FrozenSet,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Union,
    cast,
)

import dagster._check as check
from dagster._core.definitions import (
    GraphDefinition,
    IPipeline,
    InputDefinition,
    JobDefinition,
    Node,
    NodeHandle,
    SolidDefinition,
    SolidOutputHandle,
)
from dagster._core.definitions.composition import MappedInputPlaceholder
from dagster._core.definitions.dependency import DependencyStructure
from dagster._core.definitions.executor_definition import ExecutorRequirement
from dagster._core.definitions.mode import ModeDefinition
from dagster._core.definitions.pipeline_definition import PipelineDefinition
from dagster._core.definitions.reconstruct import ReconstructablePipeline
from dagster._core.definitions.repository_definition import RepositoryLoadData
from dagster._core.errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvariantViolationError,
    DagsterUnmetExecutorRequirementsError,
)
from dagster._core.execution.plan.handle import (
    ResolvedFromDynamicStepHandle,
    StepHandle,
    UnresolvedStepHandle,
)
from dagster._core.execution.retries import RetryMode
from dagster._core.instance import DagsterInstance, InstanceRef
from dagster._core.storage.mem_io_manager import mem_io_manager
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.utils import toposort

from ..context.output import get_output_context
from ..resolve_versions import resolve_step_output_versions
from .compute import create_step_outputs
from .inputs import (
    FromConfig,
    FromDefaultValue,
    FromDirectInputValue,
    FromDynamicCollect,
    FromMultipleSources,
    FromPendingDynamicStepOutput,
    FromRootInputManager,
    FromSourceAsset,
    FromStepOutput,
    FromUnresolvedStepOutput,
    StepInput,
    StepInputSource,
    UnresolvedCollectStepInput,
    UnresolvedMappedStepInput,
)
from .outputs import StepOutput, StepOutputHandle, UnresolvedStepOutputHandle
from .state import KnownExecutionState, StepOutputVersionData
from .step import (
    ExecutionStep,
    IExecutionStep,
    StepKind,
    UnresolvedCollectExecutionStep,
    UnresolvedMappedExecutionStep,
)

if TYPE_CHECKING:
    from dagster._core.snap.execution_plan_snapshot import ExecutionPlanSnapshot

    from .active import ActiveExecution


StepHandleTypes = (StepHandle, UnresolvedStepHandle, ResolvedFromDynamicStepHandle)
StepHandleUnion = Union[StepHandle, UnresolvedStepHandle, ResolvedFromDynamicStepHandle]
ExecutionStepUnion = Union[
    ExecutionStep, UnresolvedCollectExecutionStep, UnresolvedMappedExecutionStep
]


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
        resolved_run_config: ResolvedRunConfig,
        step_keys_to_execute: Optional[List[str]],
        known_state: KnownExecutionState,
        instance_ref: Optional[InstanceRef],
        tags: Dict[str, str],
        repository_load_data: Optional[RepositoryLoadData],
    ):
        if isinstance(pipeline, ReconstructablePipeline) and repository_load_data is not None:
            check.invariant(
                pipeline.repository.repository_load_data == repository_load_data,
                "When building an ExecutionPlan with explicit repository_load_data and a "
                "ReconstructablePipeline, the repository_load_data on the pipeline must be identical "
                "to passed-in repository_load_data.",
            )
        self.pipeline = check.inst_param(pipeline, "pipeline", IPipeline)
        self.resolved_run_config = check.inst_param(
            resolved_run_config, "resolved_run_config", ResolvedRunConfig
        )
        check.opt_nullable_list_param(step_keys_to_execute, "step_keys_to_execute", str)
        self.step_keys_to_execute = step_keys_to_execute
        self.mode_definition = (
            pipeline.get_definition().get_mode_definition(resolved_run_config.mode)
            if resolved_run_config.mode is not None
            else pipeline.get_definition().get_default_mode()
        )
        self._steps: Dict[str, IExecutionStep] = OrderedDict()
        self.step_output_map: Dict[
            SolidOutputHandle, Union[StepOutputHandle, UnresolvedStepOutputHandle]
        ] = dict()
        self.known_state = check.inst_param(known_state, "known_state", KnownExecutionState)
        self._instance_ref = instance_ref
        self._seen_handles: Set[StepHandleUnion] = set()
        self._tags = check.dict_param(tags, "tags", key_type=str, value_type=str)
        self.repository_load_data = check.opt_inst_param(
            repository_load_data, "repository_load_data", RepositoryLoadData
        )

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

    def get_step_by_solid_handle(self, handle: NodeHandle) -> IExecutionStep:
        check.inst_param(handle, "handle", NodeHandle)
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

        _check_persistent_storage_requirement(
            self.pipeline,
            self.mode_definition,
            self.resolved_run_config,
        )

        pipeline_def = self.pipeline.get_definition()
        root_inputs: List[
            Union[StepInput, UnresolvedMappedStepInput, UnresolvedCollectStepInput]
        ] = []
        # Recursively build the execution plan starting at the root pipeline
        for input_def in pipeline_def.graph.input_defs:
            input_name = input_def.name

            input_source = get_root_graph_input_source(
                plan_builder=self,
                pipeline_def=pipeline_def,
                input_name=input_name,
                input_def=input_def,
            )

            # If an input with dagster_type "Nothing" doesn't have a value
            # we don't create a StepInput
            if input_source is None:
                continue

            root_inputs.append(
                StepInput(
                    name=input_name,
                    dagster_type_key=input_def.dagster_type.key,
                    source=input_source,
                )
            )

        self._build_from_sorted_solids(
            pipeline_def.solids_in_topological_order,
            pipeline_def.dependency_structure,
            parent_step_inputs=root_inputs,
        )

        step_dict = {step.handle: step for step in self._steps.values()}
        step_dict_by_key = {step.key: step for step in self._steps.values()}
        step_handles_to_execute = [step.handle for step in self._steps.values()]

        executable_map, resolvable_map = _compute_step_maps(
            step_dict,
            step_dict_by_key,
            step_handles_to_execute,
            self.known_state,
        )

        executor_name = self.resolved_run_config.execution.execution_engine_name
        step_output_versions = self.known_state.step_output_versions if self.known_state else []

        plan = ExecutionPlan(
            step_dict,
            executable_map,
            resolvable_map,
            step_handles_to_execute,
            self.known_state,
            _compute_artifacts_persisted(
                step_dict,
                step_dict_by_key,
                step_handles_to_execute,
                pipeline_def,
                self.resolved_run_config,
                executable_map,
            ),
            executor_name=executor_name,
            repository_load_data=self.repository_load_data,
        )

        if self.step_keys_to_execute is not None:
            plan = plan.build_subset_plan(
                self.step_keys_to_execute, pipeline_def, self.resolved_run_config
            )

        # Expects that if step_keys_to_execute was set, that the `plan` variable will have the
        # reflected step_keys_to_execute
        if pipeline_def.is_using_memoization(self._tags) and len(step_output_versions) == 0:
            if self._instance_ref is None:
                raise DagsterInvariantViolationError(
                    "Attempted to build memoized execution plan without providing a persistent "
                    "DagsterInstance to create_execution_plan."
                )
            instance = DagsterInstance.from_ref(self._instance_ref)
            plan = plan.build_memoized_plan(
                pipeline_def, self.resolved_run_config, instance, self.step_keys_to_execute
            )

        return plan

    def _build_from_sorted_solids(
        self,
        solids: Sequence[Node],
        dependency_structure: DependencyStructure,
        parent_handle: Optional[NodeHandle] = None,
        parent_step_inputs: Optional[
            List[Union[StepInput, UnresolvedMappedStepInput, UnresolvedCollectStepInput]]
        ] = None,
    ) -> None:
        asset_layer = self.pipeline.get_definition().asset_layer
        for solid in solids:
            handle = NodeHandle(solid.name, parent_handle)

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
                    check.inst_param(
                        step_input_source,
                        "step_input_source",
                        StepInputSource,
                    )
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
                step_outputs = create_step_outputs(
                    solid, handle, self.resolved_run_config, asset_layer
                )

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
                step = self.get_step_by_solid_handle(check.not_none(resolved_handle))
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


def get_root_graph_input_source(
    plan_builder: _PlanBuilder,
    input_name: str,
    input_def: InputDefinition,
    pipeline_def: PipelineDefinition,
) -> Optional[Union[FromConfig, FromDirectInputValue]]:
    from dagster._core.definitions.job_definition import get_direct_input_values_from_job

    input_values = get_direct_input_values_from_job(pipeline_def)
    if input_values and input_name in input_values:
        return FromDirectInputValue(input_name=input_name)

    input_config = plan_builder.resolved_run_config.inputs

    if input_config and input_name in input_config:
        return FromConfig(input_name=input_name, solid_handle=None)

    if input_def.dagster_type.is_nothing:
        return None

    # Otherwise we throw an error.
    raise DagsterInvariantViolationError(
        (
            "In top-level graph of {described_target}, input {input_name} "
            "must get a value from the inputs section of its configuration."
        ).format(
            described_target=plan_builder.pipeline.get_definition().describe_target(),
            input_name=input_name,
        )
    )


def get_step_input_source(
    plan_builder: _PlanBuilder,
    solid: Node,
    input_name: str,
    input_def: InputDefinition,
    dependency_structure: DependencyStructure,
    handle: NodeHandle,
    parent_step_inputs: Optional[
        List[Union[StepInput, UnresolvedMappedStepInput, UnresolvedCollectStepInput]]
    ],
):
    check.inst_param(plan_builder, "plan_builder", _PlanBuilder)
    check.inst_param(solid, "solid", Node)
    check.str_param(input_name, "input_name")
    check.inst_param(input_def, "input_def", InputDefinition)
    check.inst_param(dependency_structure, "dependency_structure", DependencyStructure)
    check.opt_inst_param(handle, "handle", NodeHandle)
    check.opt_list_param(
        parent_step_inputs,
        "parent_step_inputs",
        of_type=(StepInput, UnresolvedMappedStepInput, UnresolvedCollectStepInput),
    )

    input_handle = solid.input_handle(input_name)
    solid_config = plan_builder.resolved_run_config.solids.get(str(handle))

    input_def = solid.definition.input_def_named(input_name)
    asset_layer = plan_builder.pipeline.get_definition().asset_layer

    if (
        # input is unconnected inside the current dependency structure
        not dependency_structure.has_deps(input_handle)
        and
        #  make sure input is unconnected in the outer dependency structure too
        not solid.container_maps_input(input_handle.input_name)
    ):
        if input_def.root_manager_key or input_def.input_manager_key:
            return FromRootInputManager(solid_handle=handle, input_name=input_name)
        # can only load from source asset if assets defs are available
        elif asset_layer.has_assets_defs and asset_layer.asset_key_for_input(
            handle, input_handle.input_name
        ):
            return FromSourceAsset(solid_handle=handle, input_name=input_name)

    if dependency_structure.has_direct_dep(input_handle):
        solid_output_handle = dependency_structure.get_direct_dep(input_handle)
        step_output_handle = plan_builder.get_output_handle(solid_output_handle)
        if isinstance(step_output_handle, UnresolvedStepOutputHandle):
            return FromUnresolvedStepOutput(
                unresolved_step_output_handle=step_output_handle,
            )

        if solid_output_handle.output_def.is_dynamic:
            return FromPendingDynamicStepOutput(
                step_output_handle=step_output_handle,
            )

        return FromStepOutput(
            step_output_handle=step_output_handle,
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

                parent_name = solid.container_mapped_fan_in_input(input_name, idx).graph_input_name
                parent_inputs = {step_input.name: step_input for step_input in parent_step_inputs}
                parent_input = parent_inputs[parent_name]
                source = parent_input.source
                if not isinstance(source, StepInputSource):
                    check.failed(f"Unexpected parent mapped input source type {source}")
                sources.append(source)

        return FromMultipleSources(sources=sources)

    if dependency_structure.has_dynamic_fan_in_dep(input_handle):
        solid_output_handle = dependency_structure.get_dynamic_fan_in_dep(input_handle)
        step_output_handle = plan_builder.get_output_handle(solid_output_handle)
        if isinstance(step_output_handle, UnresolvedStepOutputHandle):
            return FromDynamicCollect(
                source=FromUnresolvedStepOutput(
                    unresolved_step_output_handle=step_output_handle,
                ),
            )
        elif solid_output_handle.output_def.is_dynamic:
            return FromDynamicCollect(
                source=FromPendingDynamicStepOutput(
                    step_output_handle=step_output_handle,
                ),
            )

    if solid_config and input_name in solid_config.inputs:
        return FromConfig(solid_handle=handle, input_name=input_name)

    if solid.container_maps_input(input_name):
        if parent_step_inputs is None:
            check.failed("unexpected error in composition descent during plan building")

        parent_name = solid.container_mapped_input(input_name).graph_input_name
        parent_inputs = {step_input.name: step_input for step_input in parent_step_inputs}
        if parent_name in parent_inputs:
            parent_input = parent_inputs[parent_name]
            return parent_input.source
        # else fall through to Nothing case or raise

    if solid.definition.input_has_default(input_name):
        return FromDefaultValue(solid_handle=handle, input_name=input_name)

    # At this point we have an input that is not hooked up to
    # the output of another solid or provided via run config.

    # We will allow this for "Nothing" type inputs and continue.
    if input_def.dagster_type.is_nothing:
        return None

    # Otherwise we throw an error.
    raise DagsterInvariantViolationError(
        (
            "In {described_target} {described_node}, input {input_name} "
            "must get a value either (a) from a dependency or (b) from the "
            "inputs section of its configuration."
        ).format(
            described_target=plan_builder.pipeline.get_definition().describe_target(),
            described_node=solid.describe_node(),
            input_name=input_name,
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
            ("step_dict_by_key", Dict[str, IExecutionStep]),
            ("executor_name", Optional[str]),
            ("repository_load_data", Optional[RepositoryLoadData]),
        ],
    )
):
    def __new__(
        cls,
        step_dict: Dict[StepHandleUnion, IExecutionStep],
        executable_map: Dict[str, Union[StepHandle, ResolvedFromDynamicStepHandle]],
        resolvable_map: Dict[FrozenSet[str], List[UnresolvedStepHandle]],
        step_handles_to_execute: List[StepHandleUnion],
        known_state: KnownExecutionState,
        artifacts_persisted: bool = False,
        step_dict_by_key: Optional[Dict[str, IExecutionStep]] = None,
        executor_name: Optional[str] = None,
        repository_load_data: Optional[RepositoryLoadData] = None,
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
            known_state=check.inst_param(known_state, "known_state", KnownExecutionState),
            artifacts_persisted=check.bool_param(artifacts_persisted, "artifacts_persisted"),
            step_dict_by_key={step.key: step for step in step_dict.values()}
            if step_dict_by_key is None
            else check.dict_param(
                step_dict_by_key,
                "step_dict_by_key",
                key_type=str,
                value_type=(
                    ExecutionStep,
                    UnresolvedMappedExecutionStep,
                    UnresolvedCollectExecutionStep,
                ),
            ),
            executor_name=check.opt_str_param(executor_name, "executor_name"),
            repository_load_data=check.opt_inst_param(
                repository_load_data, "repository_load_data", RepositoryLoadData
            ),
        )

    @property
    def steps(self) -> List[IExecutionStep]:
        return list(self.step_dict.values())

    @property
    def step_output_versions(self) -> Dict[StepOutputHandle, str]:
        return StepOutputVersionData.get_version_dict_from_list(
            self.known_state.step_output_versions if self.known_state else []
        )

    @property
    def step_keys_to_execute(self) -> List[str]:
        return [handle.to_key() for handle in self.step_handles_to_execute]

    def get_step_output(self, step_output_handle: StepOutputHandle) -> StepOutput:
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        return _get_step_output(self.step_dict_by_key, step_output_handle)

    def get_manager_key(
        self,
        step_output_handle: StepOutputHandle,
        pipeline_def: PipelineDefinition,
    ) -> str:
        return _get_manager_key(self.step_dict_by_key, step_output_handle, pipeline_def)

    def has_step(self, handle: StepHandleUnion) -> bool:
        check.inst_param(handle, "handle", StepHandleTypes)
        return handle in self.step_dict

    def get_step(self, handle: StepHandleUnion) -> IExecutionStep:
        check.inst_param(handle, "handle", StepHandleTypes)
        return self.step_dict[handle]

    def get_step_by_key(self, key: str) -> IExecutionStep:
        check.str_param(key, "key")
        if not key in self.step_dict_by_key:
            check.failed(f"plan has no step with key {key}")
        return self.step_dict_by_key[key]

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
            self.step_dict, self.step_dict_by_key, self.step_handles_to_execute, self.executable_map
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
            self.step_dict_by_key,
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
        resolved_run_config: ResolvedRunConfig,
        step_output_versions=None,
    ) -> "ExecutionPlan":
        check.list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
        step_output_versions = check.opt_dict_param(
            step_output_versions, "step_output_versions", key_type=StepOutputHandle, value_type=str
        )

        step_handles_to_validate_set: Set[StepHandleUnion] = {
            StepHandle.parse_from_key(key) for key in step_keys_to_execute
        }
        step_handles_to_execute: List[StepHandleUnion] = []
        bad_keys = []

        for handle in step_handles_to_validate_set:

            if handle not in self.step_dict:
                # Ok if the entire dynamic step is selected to execute.
                # https://github.com/dagster-io/dagster/issues/8000
                # Note: the assumption here is when the entire dynamic step is selected,
                # the step_keys_to_execute will include both unresolved step (i.e. [?])
                # and all the resolved steps (i.e. [0], ... [n]). Given that at this point
                # we no longer track the parent known state (we don't know what "n" was),
                # solely from the resolved handles, we can't tell if an entire dynamic
                # node is being selected, so the best bet here is to check both unresolved
                # and resolved handles exist. Examples:
                # * `generate_subtasks, subtask[?], subtask[0], subtask[1], subtask[2]` will pass
                # * `generate_subtasks, subtask[0], subtask[1], subtask[2]` will result in 3 bad
                #   keys `subtask[0], subtask[1], subtask[2]`
                if isinstance(handle, ResolvedFromDynamicStepHandle):
                    unresolved_handle = handle.unresolved_form
                    if (
                        unresolved_handle in self.step_dict
                        and unresolved_handle in step_handles_to_validate_set
                    ):
                        continue

                bad_keys.append(handle.to_key())

            # Add the handle to the ready-to-execute list once it's validated
            step_handles_to_execute.append(handle)

        if bad_keys:
            raise DagsterExecutionStepNotFoundError(
                f"Can not build subset plan from unknown step{'s' if len(bad_keys)> 1 else ''}: {', '.join(bad_keys)}",
                step_keys=bad_keys,
            )

        executable_map, resolvable_map = _compute_step_maps(
            self.step_dict,
            self.step_dict_by_key,
            step_handles_to_execute,
            self.known_state,
        )

        # If step output versions were provided when constructing the subset plan, add them to the
        # known state.
        if len(step_output_versions) > 0:
            versions = StepOutputVersionData.get_version_list_from_dict(step_output_versions)
            if self.known_state:
                known_state = self.known_state._replace(step_output_versions=versions)
            else:
                known_state = KnownExecutionState(step_output_versions=versions)
        else:
            known_state = self.known_state

        return ExecutionPlan(
            self.step_dict,
            executable_map,
            resolvable_map,
            step_handles_to_execute,
            known_state,
            _compute_artifacts_persisted(
                self.step_dict,
                self.step_dict_by_key,
                step_handles_to_execute,
                pipeline_def,
                resolved_run_config,
                executable_map,
            ),
            executor_name=self.executor_name,
            repository_load_data=self.repository_load_data,
        )

    def get_version_for_step_output_handle(
        self, step_output_handle: StepOutputHandle
    ) -> Optional[str]:
        return self.step_output_versions.get(step_output_handle)

    def build_memoized_plan(
        self,
        pipeline_def: PipelineDefinition,
        resolved_run_config: ResolvedRunConfig,
        instance: DagsterInstance,
        selected_step_keys: Optional[List[str]],
    ) -> "ExecutionPlan":
        """
        Returns:
            ExecutionPlan: Execution plan that runs only unmemoized steps.
        """
        from ...storage.memoizable_io_manager import MemoizableIOManager
        from ..build_resources import build_resources, initialize_console_manager
        from ..resources_init import get_dependencies, resolve_resource_dependencies

        mode = resolved_run_config.mode
        mode_def = pipeline_def.get_mode_definition(mode)

        # Memoization cannot be used with dynamic orchestration yet.
        # Tracking: https://github.com/dagster-io/dagster/issues/4451
        for node_def in pipeline_def.all_node_defs:
            if pipeline_def.dependency_structure.is_dynamic_mapped(
                node_def.name
            ) or pipeline_def.dependency_structure.has_dynamic_downstreams(node_def.name):
                raise DagsterInvariantViolationError(
                    "Attempted to use memoization with dynamic orchestration, which is not yet "
                    "supported."
                )

        unmemoized_step_keys = set()

        log_manager = initialize_console_manager(None)

        step_output_versions = resolve_step_output_versions(pipeline_def, self, resolved_run_config)

        resource_defs_to_init = {}
        io_manager_keys = {}  # Map step output handles to io manager keys

        for step in self.steps:
            for output_name in cast(ExecutionStepUnion, step).step_output_dict.keys():
                step_output_handle = StepOutputHandle(step.key, output_name)

                io_manager_key = self.get_manager_key(step_output_handle, pipeline_def)
                io_manager_keys[step_output_handle] = io_manager_key

                resource_deps = resolve_resource_dependencies(mode_def.resource_defs)
                resource_keys_to_init = get_dependencies(io_manager_key, resource_deps)
                for resource_key in resource_keys_to_init:
                    resource_defs_to_init[resource_key] = mode_def.resource_defs[resource_key]

        all_resources_config = resolved_run_config.to_dict().get("resources", {})
        resource_config = {
            resource_key: config_val
            for resource_key, config_val in all_resources_config.items()
            if resource_key in resource_defs_to_init
        }

        with build_resources(
            resources=resource_defs_to_init,
            instance=instance,
            resource_config=resource_config,
            log_manager=log_manager,
        ) as resources:
            for step_output_handle, io_manager_key in io_manager_keys.items():
                io_manager = getattr(resources, io_manager_key)
                if not isinstance(io_manager, MemoizableIOManager):
                    raise DagsterInvariantViolationError(
                        f"{pipeline_def.describe_target().capitalize()} uses memoization, but IO manager "
                        f"'{io_manager_key}' is not a MemoizableIOManager. In order to use "
                        "memoization, all io managers need to subclass MemoizableIOManager. "
                        "Learn more about MemoizableIOManagers here: "
                        "https://docs.dagster.io/_apidocs/internals#memoizable-io-manager-experimental."
                    )
                context = get_output_context(
                    execution_plan=self,
                    pipeline_def=pipeline_def,
                    resolved_run_config=resolved_run_config,
                    step_output_handle=step_output_handle,
                    run_id=None,
                    log_manager=log_manager,
                    step_context=None,
                    resources=resources,
                    version=step_output_versions[step_output_handle],
                )
                if not io_manager.has_output(context):
                    unmemoized_step_keys.add(step_output_handle.step_key)

        if selected_step_keys is not None:
            # Take the intersection unmemoized steps and selected steps
            step_keys_to_execute = list(unmemoized_step_keys & set(selected_step_keys))
        else:
            step_keys_to_execute = list(unmemoized_step_keys)
        return self.build_subset_plan(
            step_keys_to_execute,
            pipeline_def,
            resolved_run_config,
            step_output_versions=step_output_versions,
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
        resolved_run_config: ResolvedRunConfig,
        step_keys_to_execute: Optional[List[str]] = None,
        known_state: Optional[KnownExecutionState] = None,
        instance_ref: Optional[InstanceRef] = None,
        tags: Optional[Dict[str, str]] = None,
        repository_load_data: Optional[RepositoryLoadData] = None,
    ) -> "ExecutionPlan":
        """Here we build a new ExecutionPlan from a pipeline definition and the resolved run config.

        To do this, we iterate through the pipeline's solids in topological order, and hand off the
        execution steps for each solid to a companion _PlanBuilder object.

        Once we've processed the entire pipeline, we invoke _PlanBuilder.build() to construct the
        ExecutionPlan object.
        """
        check.inst_param(pipeline, "pipeline", IPipeline)
        check.inst_param(resolved_run_config, "resolved_run_config", ResolvedRunConfig)
        check.opt_nullable_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
        known_state = check.opt_inst_param(
            known_state,
            "known_state",
            KnownExecutionState,
            # may be good to force call sites to specify instead of defaulting to unknown
            default=KnownExecutionState(),
        )
        tags = check.opt_dict_param(tags, "tags", key_type=str, value_type=str)
        repository_load_data = check.opt_inst_param(
            repository_load_data, "repository_load_data", RepositoryLoadData
        )

        plan_builder = _PlanBuilder(
            pipeline,
            resolved_run_config=resolved_run_config,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
            instance_ref=instance_ref,
            tags=tags,
            repository_load_data=repository_load_data,
        )

        # Finally, we build and return the execution plan
        return plan_builder.build()

    @staticmethod
    def rebuild_step_input(step_input_snap):
        from dagster._core.snap.execution_plan_snapshot import ExecutionStepInputSnap

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
    def rebuild_from_snapshot(
        pipeline_name: str,
        execution_plan_snapshot: "ExecutionPlanSnapshot",
    ):
        if not execution_plan_snapshot.can_reconstruct_plan:
            raise DagsterInvariantViolationError(
                "Tried to reconstruct an old ExecutionPlanSnapshot that was created before snapshots "
                "had enough information to fully reconstruct the ExecutionPlan"
            )

        step_dict = {}
        step_dict_by_key = {}

        for step_snap in execution_plan_snapshot.steps:
            input_snaps = step_snap.inputs
            output_snaps = step_snap.outputs

            step_inputs = [
                ExecutionPlan.rebuild_step_input(step_input_snap) for step_input_snap in input_snaps
            ]

            step_outputs = [
                StepOutput(
                    check.not_none(step_output_snap.solid_handle),
                    step_output_snap.name,
                    step_output_snap.dagster_type_key,
                    check.not_none(step_output_snap.properties),
                )
                for step_output_snap in output_snaps
            ]

            if step_snap.kind == StepKind.COMPUTE:
                step: IExecutionStep = ExecutionStep(
                    check.inst(
                        cast(
                            Union[StepHandle, ResolvedFromDynamicStepHandle],
                            step_snap.step_handle,
                        ),
                        ttype=(StepHandle, ResolvedFromDynamicStepHandle),
                    ),
                    pipeline_name,
                    step_inputs,
                    step_outputs,
                    step_snap.tags,
                )
            elif step_snap.kind == StepKind.UNRESOLVED_MAPPED:
                step = UnresolvedMappedExecutionStep(
                    check.inst(
                        cast(UnresolvedStepHandle, step_snap.step_handle),
                        ttype=UnresolvedStepHandle,
                    ),
                    pipeline_name,
                    step_inputs,
                    step_outputs,
                    step_snap.tags,
                )
            elif step_snap.kind == StepKind.UNRESOLVED_COLLECT:
                step = UnresolvedCollectExecutionStep(
                    check.inst(cast(StepHandle, step_snap.step_handle), ttype=StepHandle),
                    pipeline_name,
                    step_inputs,
                    step_outputs,
                    step_snap.tags,
                )
            else:
                raise Exception(f"Unexpected step kind {str(step_snap.kind)}")

            step_dict[step.handle] = step
            step_dict_by_key[step.key] = step

        step_handles_to_execute = [
            StepHandle.parse_from_key(key) for key in execution_plan_snapshot.step_keys_to_execute
        ]

        executable_map, resolvable_map = _compute_step_maps(
            step_dict,
            step_dict_by_key,
            step_handles_to_execute,
            execution_plan_snapshot.initial_known_state,
        )

        return ExecutionPlan(
            step_dict,
            executable_map,
            resolvable_map,
            step_handles_to_execute,
            # default to empty known execution state if initial was not persisted
            execution_plan_snapshot.initial_known_state or KnownExecutionState(),
            execution_plan_snapshot.artifacts_persisted,
            executor_name=execution_plan_snapshot.executor_name,
            repository_load_data=execution_plan_snapshot.repository_load_data,
        )


def _update_from_resolved_dynamic_outputs(
    step_dict: Dict[StepHandleUnion, IExecutionStep],
    step_dict_by_key: Dict[str, IExecutionStep],
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
        step_dict_by_key[step.key] = step

    for key_set in key_sets_to_clear:
        del resolvable_map[key_set]


def can_isolate_steps(pipeline_def: PipelineDefinition, mode_def: ModeDefinition):
    """Returns true if every output definition in the pipeline uses an IO manager that's not
    the mem_io_manager.

    If true, this indicates that it's OK to execute steps in their own processes, because their
    outputs will be available to other processes.
    """
    # pylint: disable=comparison-with-callable

    output_defs = [
        output_def
        for solid_def in pipeline_def.all_node_defs
        for output_def in solid_def.output_defs
    ]
    for output_def in output_defs:
        if mode_def.resource_defs[output_def.io_manager_key] == mem_io_manager:
            return False

    return True


def _check_persistent_storage_requirement(
    pipeline: IPipeline,
    mode_def: ModeDefinition,
    resolved_run_config: ResolvedRunConfig,
) -> None:
    from dagster._core.execution.context_creation_pipeline import executor_def_from_config

    pipeline_def = pipeline.get_definition()
    executor_def = executor_def_from_config(mode_def, resolved_run_config)
    requirements_lst = executor_def.get_requirements(
        resolved_run_config.execution.execution_engine_config
    )
    if ExecutorRequirement.PERSISTENT_OUTPUTS not in requirements_lst:
        return

    if not can_isolate_steps(pipeline_def, mode_def):
        if isinstance(pipeline_def, JobDefinition):
            target = "job"
            node = "op"
            suggestion = 'the_graph.to_job(resource_defs={"io_manager": fs_io_manager})'
        else:
            target = "pipeline"
            node = "solid"
            suggestion = (
                '@pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})])'
            )
        raise DagsterUnmetExecutorRequirementsError(
            f"You have attempted to use an executor that uses multiple processes, but your {target} "
            f"includes {node} outputs that will not be stored somewhere where other processes can "
            "retrieve them. Please use a persistent IO manager for these outputs. E.g. with\n"
            f"    {suggestion}"
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
    step_dict,
    step_dict_by_key,
    step_handles_to_execute,
    pipeline_def,
    resolved_run_config,
    executable_map,
):
    """
    Check if all the border steps of the current run have non-in-memory IO managers for reexecution.

    Border steps: all the steps that don't have upstream steps to execute, i.e. indegree is 0).
    """
    # pylint: disable=comparison-with-callable

    mode_def = pipeline_def.get_mode_definition(resolved_run_config.mode)

    if len(step_dict) == 0:
        return False

    steps_by_level = _get_steps_to_execute_by_level(
        step_dict, step_dict_by_key, step_handles_to_execute, executable_map
    )

    if len(steps_by_level) == 0:
        return False

    for step in steps_by_level[0]:
        # check if all its inputs' upstream step outputs have non-in-memory IO manager configured
        for step_input in step.step_inputs:
            for step_output_handle in step_input.get_step_output_handle_dependencies():
                io_manager_key = _get_manager_key(
                    step_dict_by_key, step_output_handle, pipeline_def
                )
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


def _get_steps_to_execute_by_level(
    step_dict, step_dict_by_key, step_handles_to_execute, executable_map
):
    return [
        [cast(ExecutionStep, step_dict_by_key[step_key]) for step_key in sorted(step_key_level)]
        for step_key_level in toposort(
            _get_executable_step_deps(step_dict, step_handles_to_execute, executable_map)
        )
    ]


def _get_executable_step_deps(
    step_dict,
    step_handles_to_execute,
    executable_map,
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
            if dep in executable_map:
                if dep not in unresolved_set:
                    filtered_deps.append(dep)
                else:
                    depends_on_unresolved = True
            elif dep in step_keys_to_execute:
                depends_on_unresolved = True

        if not depends_on_unresolved:
            deps[key] = set(filtered_deps)
        else:
            unresolved_set.add(key)

    return deps


def _get_step_output(step_dict_by_key, step_output_handle: StepOutputHandle) -> StepOutput:
    check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
    step = step_dict_by_key[step_output_handle.step_key]
    return step.step_output_named(step_output_handle.output_name)


def _get_manager_key(step_dict_by_key, step_output_handle, pipeline_def):
    step_output = _get_step_output(step_dict_by_key, step_output_handle)
    solid_handle = step_output.solid_handle
    output_def = pipeline_def.get_solid(solid_handle).output_def_named(step_output.name)
    return output_def.io_manager_key


# computes executable_map and resolvable_map and returns them as a tuple. Also
# may modify the passed in step_dict to include resolved step using known_state.
def _compute_step_maps(step_dict, step_dict_by_key, step_handles_to_execute, known_state):
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
                        f'Unresolved ExecutionStep "{step.key}" is resolved by "{key}" '
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
            step_dict_by_key,
            executable_map,
            resolvable_map,
            step_handles_to_execute,
            known_state.dynamic_mappings,
        )

    return (executable_map, resolvable_map)
