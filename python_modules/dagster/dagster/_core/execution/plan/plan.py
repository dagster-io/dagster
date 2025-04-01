from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Optional, Union, cast

import dagster._check as check
from dagster._core.definitions import (
    GraphDefinition,
    InputDefinition,
    Node,
    NodeHandle,
    NodeOutput,
    OpDefinition,
)
from dagster._core.definitions.asset_layer import AssetLayer
from dagster._core.definitions.composition import MappedInputPlaceholder
from dagster._core.definitions.dependency import (
    BlockingAssetChecksDependencyDefinition,
    DependencyStructure,
    MultiDependencyDefinition,
    NodeInput,
)
from dagster._core.definitions.executor_definition import ExecutorRequirement
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.repository_definition import RepositoryLoadData
from dagster._core.errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvariantViolationError,
    DagsterUnmetExecutorRequirementsError,
)
from dagster._core.execution.plan.compute import create_step_outputs
from dagster._core.execution.plan.handle import (
    ResolvedFromDynamicStepHandle,
    StepHandle,
    UnresolvedStepHandle,
)
from dagster._core.execution.plan.inputs import (
    FromConfig,
    FromDefaultValue,
    FromDirectInputValue,
    FromDynamicCollect,
    FromInputManager,
    FromLoadableAsset,
    FromMultipleSources,
    FromMultipleSourcesLoadSingleSource,
    FromPendingDynamicStepOutput,
    FromStepOutput,
    FromUnresolvedStepOutput,
    StepInput,
    StepInputSource,
    StepInputSourceUnion,
    StepInputUnion,
    UnresolvedCollectStepInput,
    UnresolvedMappedStepInput,
)
from dagster._core.execution.plan.instance_concurrency_context import InstanceConcurrencyContext
from dagster._core.execution.plan.outputs import (
    StepOutput,
    StepOutputHandle,
    UnresolvedStepOutputHandle,
)
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.execution.plan.step import (
    ExecutionStep,
    IExecutionStep,
    StepKind,
    UnresolvedCollectExecutionStep,
    UnresolvedMappedExecutionStep,
)
from dagster._core.execution.retries import RetryMode
from dagster._core.instance import DagsterInstance, InstanceRef
from dagster._core.storage.mem_io_manager import mem_io_manager
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.utils import toposort

if TYPE_CHECKING:
    from dagster._core.execution.plan.active import ActiveExecution
    from dagster._core.snap.execution_plan_snapshot import (
        ExecutionPlanSnapshot,
        ExecutionStepInputSnap,
    )


StepHandleTypes = (StepHandle, UnresolvedStepHandle, ResolvedFromDynamicStepHandle)
StepHandleUnion = Union[StepHandle, UnresolvedStepHandle, ResolvedFromDynamicStepHandle]
ExecutionStepUnion = Union[
    ExecutionStep, UnresolvedCollectExecutionStep, UnresolvedMappedExecutionStep
]


class _PlanBuilder:
    """This is the state that is built up during the execution plan build process."""

    def __init__(
        self,
        job_def: JobDefinition,
        resolved_run_config: ResolvedRunConfig,
        step_keys_to_execute: Optional[Sequence[str]],
        known_state: KnownExecutionState,
        instance_ref: Optional[InstanceRef],
        tags: Mapping[str, str],
        repository_load_data: Optional[RepositoryLoadData],
    ):
        self.job_def = check.inst_param(job_def, "job", JobDefinition)
        self.resolved_run_config = check.inst_param(
            resolved_run_config, "resolved_run_config", ResolvedRunConfig
        )
        self.step_keys_to_execute = check.opt_nullable_sequence_param(
            step_keys_to_execute, "step_keys_to_execute", str
        )
        self.known_state = check.inst_param(known_state, "known_state", KnownExecutionState)
        self._instance_ref = instance_ref
        self._tags = check.mapping_param(tags, "tags", key_type=str, value_type=str)
        self.repository_load_data = check.opt_inst_param(
            repository_load_data, "repository_load_data", RepositoryLoadData
        )

        self._steps: dict[str, IExecutionStep] = {}
        self.step_output_map: dict[
            NodeOutput, Union[StepOutputHandle, UnresolvedStepOutputHandle]
        ] = {}
        self._seen_handles: set[StepHandleUnion] = set()

    def add_step(self, step: IExecutionStep) -> None:
        # Keep track of the step keys we've seen so far to ensure we don't add duplicates
        if step.handle in self._seen_handles:
            keys = list(self._steps.keys())
            check.failed(f"Duplicated key {step.key}. Full list seen so far: {keys}.")
        self._seen_handles.add(step.handle)
        self._steps[str(step.node_handle)] = step

    def get_step_by_node_handle(self, handle: NodeHandle) -> IExecutionStep:
        check.inst_param(handle, "handle", NodeHandle)
        return self._steps[str(handle)]

    def build(self) -> "ExecutionPlan":
        """Builds the execution plan."""
        _check_persistent_storage_requirement(
            self.job_def,
            self.resolved_run_config,
        )

        root_inputs: list[
            Union[StepInput, UnresolvedMappedStepInput, UnresolvedCollectStepInput]
        ] = []
        # Recursively build the execution plan starting at the root pipeline
        for input_def in self.job_def.graph.input_defs:
            input_name = input_def.name

            input_source = self.get_root_graph_input_source(
                job_def=self.job_def,
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

        self._build_from_sorted_nodes(
            self.job_def.nodes_in_topological_order,
            self.job_def.dependency_structure,
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
                self.job_def,
                self.resolved_run_config,
                executable_map,
            ),
            executor_name=executor_name,
            repository_load_data=self.repository_load_data,
        )

        if (
            self.step_keys_to_execute is not None
            # no need to subset if plan already matches request
            and self.step_keys_to_execute != plan.step_keys_to_execute
        ):
            plan = plan.build_subset_plan(
                self.step_keys_to_execute, self.job_def, self.resolved_run_config
            )

        return plan

    def _build_from_sorted_nodes(
        self,
        nodes: Sequence[Node],
        dependency_structure: DependencyStructure,
        parent_handle: Optional[NodeHandle] = None,
        parent_step_inputs: Optional[Sequence[StepInputUnion]] = None,
    ) -> None:
        asset_layer = self.job_def.asset_layer
        step_output_map: dict[NodeOutput, Union[StepOutputHandle, UnresolvedStepOutputHandle]] = {}
        for node in nodes:
            handle = NodeHandle(node.name, parent_handle)

            ### 1. INPUTS
            # Create and add execution plan steps for node inputs
            has_unresolved_input = False
            has_pending_input = False
            step_inputs: list[StepInputUnion] = []
            for input_name, input_def in node.definition.input_dict.items():
                step_input_source = get_step_input_source(
                    self.job_def,
                    node,
                    input_name,
                    input_def,
                    dependency_structure,
                    handle,
                    self.resolved_run_config.ops.get(str(handle)),
                    step_output_map,
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
            # Create and add execution plan step for the op compute function
            if isinstance(node.definition, OpDefinition):
                step_outputs = create_step_outputs(
                    node, handle, self.resolved_run_config, asset_layer
                )

                if has_pending_input and has_unresolved_input:
                    check.failed("Can not have pending and unresolved step inputs")

                elif has_unresolved_input:
                    new_step = UnresolvedMappedExecutionStep(
                        handle=UnresolvedStepHandle(node_handle=handle),
                        job_name=self.job_def.name,
                        step_inputs=cast(
                            list[Union[StepInput, UnresolvedMappedStepInput]], step_inputs
                        ),
                        step_outputs=step_outputs,
                        tags=node.tags,
                        pool=node.definition.pool,
                    )
                elif has_pending_input:
                    new_step = UnresolvedCollectExecutionStep(
                        handle=StepHandle(node_handle=handle),
                        job_name=self.job_def.name,
                        step_inputs=cast(
                            list[Union[StepInput, UnresolvedCollectStepInput]], step_inputs
                        ),
                        step_outputs=step_outputs,
                        tags=node.tags,
                        pool=node.definition.pool,
                    )
                else:
                    new_step = ExecutionStep(
                        handle=StepHandle(node_handle=handle),
                        job_name=self.job_def.name,
                        step_inputs=cast(list[StepInput], step_inputs),
                        step_outputs=step_outputs,
                        tags=node.tags,
                        pool=node.definition.pool,
                    )

                self.add_step(new_step)

            ### 2b. RECURSE
            # Recurse over the nodes contained in an instance of GraphDefinition
            elif isinstance(node.definition, GraphDefinition):
                self._build_from_sorted_nodes(
                    node.definition.nodes_in_topological_order,
                    node.definition.dependency_structure,
                    parent_handle=handle,
                    parent_step_inputs=step_inputs,
                )

            else:
                check.invariant(
                    False,
                    f"Unexpected node type {type(node.definition)} encountered during execution"
                    " planning",
                )

            ### 3. OUTPUTS
            # Create output handles for node outputs
            for name, output_def in node.definition.output_dict.items():
                node_output = node.get_output(name)

                # Punch through layers of composition scope to map to the output of the
                # actual compute step
                resolved_output_def, resolved_handle = node.definition.resolve_output_to_origin(
                    output_def.name, handle
                )
                step = self.get_step_by_node_handle(check.not_none(resolved_handle))
                if isinstance(step, (ExecutionStep, UnresolvedCollectExecutionStep)):
                    step_output_handle: Union[StepOutputHandle, UnresolvedStepOutputHandle] = (
                        StepOutputHandle(step.key, resolved_output_def.name)
                    )
                elif isinstance(step, UnresolvedMappedExecutionStep):
                    step_output_handle = UnresolvedStepOutputHandle(
                        step.handle,
                        resolved_output_def.name,
                        step.resolved_by_step_key,
                        step.resolved_by_output_name,
                    )
                else:
                    check.failed(f"Unexpected step type {step}")

                step_output_map[node_output] = step_output_handle

    def get_root_graph_input_source(
        self,
        input_name: str,
        input_def: InputDefinition,
        job_def: JobDefinition,
    ) -> Optional[Union[FromConfig, FromDirectInputValue]]:
        input_values = job_def.input_values
        if input_values and input_name in input_values:
            return FromDirectInputValue(input_name=input_name)

        input_config = self.resolved_run_config.inputs

        if input_config and input_name in input_config:
            return FromConfig(input_name=input_name, node_handle=None)

        if input_def.dagster_type.is_nothing:
            return None

        # Otherwise we throw an error.
        raise DagsterInvariantViolationError(
            f"In top-level graph of {self.job_def.describe_target()}, input {input_name} "
            "must get a value from the inputs section of its configuration."
        )


def get_step_input_source(
    job_def: JobDefinition,
    node: Node,
    input_name: str,
    input_def: InputDefinition,
    dependency_structure: DependencyStructure,
    handle: NodeHandle,
    node_config: Any,
    step_output_map: dict[NodeOutput, Union[StepOutputHandle, UnresolvedStepOutputHandle]],
    parent_step_inputs: Optional[Sequence[StepInputUnion]],
) -> Optional[StepInputSourceUnion]:
    input_handle = node.get_input(input_name)
    input_def = node.definition.input_def_named(input_name)
    asset_layer = job_def.asset_layer

    if (
        # input is unconnected inside the current dependency structure
        not dependency_structure.has_deps(input_handle)
        and
        #  make sure input is unconnected in the outer dependency structure too
        not node.container_maps_input(input_handle.input_name)
    ):
        # can only load from source asset if assets defs are available
        if asset_layer.asset_key_for_input(handle, input_handle.input_name):
            return FromLoadableAsset()
        elif input_def.input_manager_key:
            return FromInputManager(node_handle=handle, input_name=input_name)

    if dependency_structure.has_direct_dep(input_handle):
        node_output_handle = dependency_structure.get_direct_dep(input_handle)
        step_output_handle = step_output_map[node_output_handle]
        if isinstance(step_output_handle, UnresolvedStepOutputHandle):
            return FromUnresolvedStepOutput(
                unresolved_step_output_handle=step_output_handle,
            )

        if node_output_handle.output_def.is_dynamic:
            return FromPendingDynamicStepOutput(
                step_output_handle=step_output_handle,
            )

        return FromStepOutput(
            step_output_handle=step_output_handle,
            fan_in=False,
        )

    if dependency_structure.has_fan_in_deps(input_handle):
        dep_def = dependency_structure.get_dependency_definition(input_handle)
        if isinstance(dep_def, MultiDependencyDefinition):
            return _step_input_source_from_multi_dep_def(
                dependency_structure=dependency_structure,
                input_handle=input_handle,
                step_output_map=step_output_map,
                parent_step_inputs=parent_step_inputs,
                node=node,
                input_name=input_name,
            )
        elif isinstance(dep_def, BlockingAssetChecksDependencyDefinition):
            return _step_input_source_from_blocking_asset_checks_dep_def(
                dep_def=dep_def,
                node_handle=handle,
                dependency_structure=dependency_structure,
                input_handle=input_handle,
                step_output_map=step_output_map,
                parent_step_inputs=parent_step_inputs,
                input_name=input_name,
                asset_layer=asset_layer,
            )
        else:
            check.failed(
                "Expected fan-in deps to correspond to a MultiDependencyDefinition or"
                f" BlockingAssetChecksDependencyDefinition, but was {type(dep_def)}"
            )
    if dependency_structure.has_dynamic_fan_in_dep(input_handle):
        node_output_handle = dependency_structure.get_dynamic_fan_in_dep(input_handle)
        step_output_handle = step_output_map[node_output_handle]
        if isinstance(step_output_handle, UnresolvedStepOutputHandle):
            return FromDynamicCollect(
                source=FromUnresolvedStepOutput(
                    unresolved_step_output_handle=step_output_handle,
                ),
            )
        elif node_output_handle.output_def.is_dynamic:
            return FromDynamicCollect(
                source=FromPendingDynamicStepOutput(
                    step_output_handle=step_output_handle,
                ),
            )

    if node_config and input_name in node_config.inputs:
        return FromConfig(node_handle=handle, input_name=input_name)

    if node.container_maps_input(input_name):
        if parent_step_inputs is None:
            check.failed("unexpected error in composition descent during plan building")

        parent_name = node.container_mapped_input(input_name).graph_input_name
        parent_inputs = {step_input.name: step_input for step_input in parent_step_inputs}
        if parent_name in parent_inputs:
            parent_input = parent_inputs[parent_name]
            return parent_input.source
        # else fall through to Nothing case or raise

    if node.definition.input_has_default(input_name):
        return FromDefaultValue(node_handle=handle, input_name=input_name)

    # At this point we have an input that is not hooked up to
    # the output of another op or provided via run config.

    # We will allow this for "Nothing" type inputs and continue.
    if input_def.dagster_type.is_nothing:
        return None

    # Otherwise we throw an error.
    raise DagsterInvariantViolationError(
        f"In {job_def.describe_target()} {node.describe_node()}, input {input_name} "
        "must get a value either (a) from a dependency or (b) from the "
        "inputs section of its configuration."
    )


def _step_input_source_from_multi_dep_def(
    dependency_structure: DependencyStructure,
    input_handle: NodeInput,
    step_output_map: dict[NodeOutput, Union[StepOutputHandle, UnresolvedStepOutputHandle]],
    parent_step_inputs: Optional[Sequence[StepInputUnion]],
    node: Node,
    input_name: str,
) -> FromMultipleSources:
    sources: list[StepInputSource] = []
    deps = dependency_structure.get_fan_in_deps(input_handle)

    for idx, handle_or_placeholder in enumerate(deps):
        if isinstance(handle_or_placeholder, NodeOutput):
            step_output_handle = step_output_map[handle_or_placeholder]
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
                f"Expected NodeOutput or MappedInputPlaceholder, got {handle_or_placeholder}",
            )
            if parent_step_inputs is None:
                check.failed("unexpected error in composition descent during plan building")

            parent_name = node.container_mapped_fan_in_input(input_name, idx).graph_input_name
            parent_inputs = {step_input.name: step_input for step_input in parent_step_inputs}
            parent_input = parent_inputs[parent_name]
            source = parent_input.source
            if not isinstance(source, StepInputSource):
                check.failed(f"Unexpected parent mapped input source type {source}")
            sources.append(source)

    return FromMultipleSources(sources=sources)


def _step_input_source_from_blocking_asset_checks_dep_def(
    dep_def: BlockingAssetChecksDependencyDefinition,
    dependency_structure: DependencyStructure,
    input_handle: NodeInput,
    step_output_map: dict[NodeOutput, Union[StepOutputHandle, UnresolvedStepOutputHandle]],
    parent_step_inputs: Optional[Sequence[StepInputUnion]],
    node_handle: NodeHandle,
    input_name: str,
    asset_layer: AssetLayer,
) -> FromMultipleSourcesLoadSingleSource:
    sources: list[StepInputSource] = []
    source_to_load_from: Optional[StepInputSource] = None
    deps = dependency_structure.get_fan_in_deps(input_handle)

    for idx, node_output in enumerate(deps):
        if isinstance(node_output, NodeOutput):
            step_output_handle = step_output_map[node_output]
            if (
                isinstance(step_output_handle, UnresolvedStepOutputHandle)
                or node_output.output_def.is_dynamic
            ):
                check.failed(
                    "Unexpected dynamic output dependency in regular fan in, "
                    "should have been caught at definition time."
                )

            source = FromStepOutput(step_output_handle=step_output_handle, fan_in=True)
            sources.append(source)
            if (
                dep_def.other_dependency is not None
                and dep_def.other_dependency.node == node_output.node_name
                and dep_def.other_dependency.output == node_output.output_name
            ):
                source_to_load_from = source
        else:
            check.invariant(f"Expected NodeOutput, got {node_output}")

    if source_to_load_from is None:
        asset_key_for_input = asset_layer.asset_key_for_input(node_handle, input_handle.input_name)
        if asset_key_for_input:
            source_to_load_from = FromLoadableAsset(node_handle=node_handle, input_name=input_name)
            sources.append(source_to_load_from)
        else:
            check.failed("Unexpected: no sources to load from and no asset key to load from")

    return FromMultipleSourcesLoadSingleSource(
        sources=sources, source_to_load_from=source_to_load_from
    )


class ExecutionPlan(
    NamedTuple(
        "_ExecutionPlan",
        [
            ("step_dict", dict[StepHandleUnion, IExecutionStep]),
            ("executable_map", dict[str, Union[StepHandle, ResolvedFromDynamicStepHandle]]),
            (
                "resolvable_map",
                dict[frozenset[str], Sequence[Union[StepHandle, UnresolvedStepHandle]]],
            ),
            ("step_handles_to_execute", Sequence[StepHandleUnion]),
            ("known_state", KnownExecutionState),
            ("artifacts_persisted", bool),
            ("step_dict_by_key", dict[str, IExecutionStep]),
            ("executor_name", Optional[str]),
            ("repository_load_data", Optional[RepositoryLoadData]),
        ],
    )
):
    def __new__(
        cls,
        step_dict: dict[StepHandleUnion, IExecutionStep],
        executable_map: dict[str, Union[StepHandle, ResolvedFromDynamicStepHandle]],
        resolvable_map: dict[frozenset[str], Sequence[Union[StepHandle, UnresolvedStepHandle]]],
        step_handles_to_execute: Sequence[StepHandleUnion],
        known_state: KnownExecutionState,
        artifacts_persisted: bool = False,
        step_dict_by_key: Optional[dict[str, IExecutionStep]] = None,
        executor_name: Optional[str] = None,
        repository_load_data: Optional[RepositoryLoadData] = None,
    ):
        return super().__new__(
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
            step_handles_to_execute=check.sequence_param(
                step_handles_to_execute,
                "step_handles_to_execute",
                of_type=(StepHandle, UnresolvedStepHandle, ResolvedFromDynamicStepHandle),
            ),
            known_state=check.inst_param(known_state, "known_state", KnownExecutionState),
            artifacts_persisted=check.bool_param(artifacts_persisted, "artifacts_persisted"),
            step_dict_by_key=(
                {step.key: step for step in step_dict.values()}
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
                )
            ),
            executor_name=check.opt_str_param(executor_name, "executor_name"),
            repository_load_data=check.opt_inst_param(
                repository_load_data, "repository_load_data", RepositoryLoadData
            ),
        )

    @property
    def steps(self) -> Sequence[IExecutionStep]:
        return list(self.step_dict.values())

    @property
    def step_output_versions(self) -> Mapping[StepOutputHandle, str]:
        return self.known_state.step_output_versions if self.known_state else {}

    @property
    def step_keys_to_execute(self) -> Sequence[str]:
        return [handle.to_key() for handle in self.step_handles_to_execute]

    def get_step_output(self, step_output_handle: StepOutputHandle) -> StepOutput:
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        return _get_step_output(self.step_dict_by_key, step_output_handle)

    def get_manager_key(
        self,
        step_output_handle: StepOutputHandle,
        job_def: JobDefinition,
    ) -> str:
        return _get_manager_key(self.step_dict_by_key, step_output_handle, job_def)

    def has_step(self, handle: StepHandleUnion) -> bool:
        check.inst_param(handle, "handle", StepHandleTypes)
        return handle in self.step_dict

    def get_step(self, handle: StepHandleUnion) -> IExecutionStep:
        check.inst_param(handle, "handle", StepHandleTypes)
        return self.step_dict[handle]

    def get_step_by_key(self, key: str) -> IExecutionStep:
        check.str_param(key, "key")
        if key not in self.step_dict_by_key:
            check.failed(f"plan has no step with key {key}")
        return self.step_dict_by_key[key]

    def get_executable_step_by_key(self, key: str) -> ExecutionStep:
        step = self.get_step_by_key(key)
        return check.inst(step, ExecutionStep)

    def get_all_steps_in_topo_order(self) -> Sequence[IExecutionStep]:
        return [step for step_level in self.get_all_steps_by_level() for step in step_level]

    def get_all_steps_by_level(self) -> Sequence[Sequence[IExecutionStep]]:
        return [
            [self.get_step_by_key(step_key) for step_key in sorted(step_key_level)]
            for step_key_level in toposort(self.get_all_step_deps())
        ]

    def get_all_step_deps(self) -> Mapping[str, set[str]]:
        deps = {}
        for step in self.step_dict.values():
            if isinstance(step, ExecutionStep):
                deps[step.key] = step.get_execution_dependency_keys()
            elif isinstance(step, (UnresolvedMappedExecutionStep, UnresolvedCollectExecutionStep)):
                deps[step.key] = step.get_all_dependency_keys()
            else:
                check.failed(f"Unexpected execution step type {step}")

        return deps

    def get_steps_to_execute_in_topo_order(self) -> Sequence[ExecutionStep]:
        return [step for step_level in self.get_steps_to_execute_by_level() for step in step_level]

    def get_steps_to_execute_by_level(self) -> Sequence[Sequence[ExecutionStep]]:
        return _get_steps_to_execute_by_level(
            self.step_dict, self.step_dict_by_key, self.step_handles_to_execute, self.executable_map
        )

    def get_executable_step_deps(self) -> Mapping[str, set[str]]:
        return _get_executable_step_deps(
            self.step_dict, self.step_handles_to_execute, self.executable_map
        )

    def resolve(
        self,
        mappings: Mapping[str, Mapping[str, Optional[Sequence[str]]]],
    ) -> Mapping[str, set[str]]:
        """Resolve any dynamic map or collect steps with the resolved dynamic mappings."""
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
        step_keys_to_execute: Sequence[str],
        job_def: JobDefinition,
        resolved_run_config: ResolvedRunConfig,
        step_output_versions: Optional[Mapping[StepOutputHandle, Optional[str]]] = None,
    ) -> "ExecutionPlan":
        check.sequence_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
        step_output_versions = check.opt_mapping_param(
            step_output_versions, "step_output_versions", key_type=StepOutputHandle, value_type=str
        )

        step_handles_to_validate: Sequence[StepHandleUnion] = []
        step_handles_to_validate_set: set[StepHandleUnion] = set()

        # preserve order of step_keys_to_execute since we build the new step_keys_to_execute
        # from iterating step_handles_to_validate
        for key in step_keys_to_execute:
            handle = StepHandle.parse_from_key(key)
            if handle not in step_handles_to_validate_set:
                step_handles_to_validate_set.add(handle)
                step_handles_to_validate.append(handle)

        step_handles_to_execute: list[StepHandleUnion] = []
        bad_keys = []

        for handle in step_handles_to_validate:
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
                f"Can not build subset plan from unknown step{'s' if len(bad_keys)> 1 else ''}:"
                f" {', '.join(bad_keys)}",
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
        known_state = self.known_state
        if len(step_output_versions) > 0:
            known_state = self.known_state._replace(step_output_versions=step_output_versions)

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
                job_def,
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

    def start(
        self,
        retry_mode: RetryMode,
        sort_key_fn: Optional[Callable[[ExecutionStep], float]] = None,
        max_concurrent: Optional[int] = None,
        tag_concurrency_limits: Optional[list[dict[str, Any]]] = None,
        instance_concurrency_context: Optional[InstanceConcurrencyContext] = None,
    ) -> "ActiveExecution":
        from dagster._core.execution.plan.active import ActiveExecution

        return ActiveExecution(
            self,
            retry_mode,
            sort_key_fn,
            max_concurrent,
            tag_concurrency_limits,
            instance_concurrency_context=instance_concurrency_context,
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
            if not isinstance(only_step, ExecutionStep):
                return None

            return cast(ExecutionStep, only_step).handle

        return None

    @staticmethod
    def build(
        job_def: JobDefinition,
        resolved_run_config: ResolvedRunConfig,
        step_keys_to_execute: Optional[Sequence[str]] = None,
        known_state: Optional[KnownExecutionState] = None,
        instance_ref: Optional[InstanceRef] = None,
        tags: Optional[Mapping[str, str]] = None,
        repository_load_data: Optional[RepositoryLoadData] = None,
    ) -> "ExecutionPlan":
        """Here we build a new ExecutionPlan from a job definition and the resolved run config.

        To do this, we iterate through the job's nodes in topological order, and hand off the
        execution steps for each node to a companion _PlanBuilder object.

        Once we've processed the entire job, we invoke _PlanBuilder.build() to construct the
        ExecutionPlan object.
        """
        return _PlanBuilder(
            job_def,
            resolved_run_config=resolved_run_config,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state or KnownExecutionState(),
            instance_ref=instance_ref,
            tags=tags or {},
            repository_load_data=repository_load_data,
        ).build()

    @staticmethod
    def rebuild_step_input(
        step_input_snap: "ExecutionStepInputSnap",
    ) -> Union["StepInput", "UnresolvedMappedStepInput", "UnresolvedCollectStepInput"]:
        from dagster._core.snap.execution_plan_snapshot import ExecutionStepInputSnap

        check.inst_param(step_input_snap, "step_input_snap", ExecutionStepInputSnap)

        step_input_source = step_input_snap.source

        if isinstance(
            step_input_source,
            (FromPendingDynamicStepOutput, FromUnresolvedStepOutput),
        ):
            return UnresolvedMappedStepInput(
                name=step_input_snap.name,
                dagster_type_key=step_input_snap.dagster_type_key,
                source=step_input_source,
            )
        elif isinstance(step_input_source, FromDynamicCollect):
            return UnresolvedCollectStepInput(
                name=step_input_snap.name,
                dagster_type_key=step_input_snap.dagster_type_key,
                source=step_input_source,
            )
        else:
            check.inst_param(step_input_source, "step_input_source", StepInputSource)
            return StepInput(
                name=step_input_snap.name,
                dagster_type_key=step_input_snap.dagster_type_key,
                source=step_input_snap.source,  # type: ignore  # (possible none)
            )

    @staticmethod
    def rebuild_from_snapshot(
        job_name: str,
        execution_plan_snapshot: "ExecutionPlanSnapshot",
    ) -> "ExecutionPlan":
        if not execution_plan_snapshot.can_reconstruct_plan:
            raise DagsterInvariantViolationError(
                "Tried to reconstruct an old ExecutionPlanSnapshot that was created before"
                " snapshots had enough information to fully reconstruct the ExecutionPlan"
            )

        step_dict: dict[StepHandleUnion, IExecutionStep] = {}
        step_dict_by_key: dict[str, IExecutionStep] = {}

        for step_snap in execution_plan_snapshot.steps:
            input_snaps = step_snap.inputs
            output_snaps = step_snap.outputs

            step_inputs = [
                ExecutionPlan.rebuild_step_input(step_input_snap) for step_input_snap in input_snaps
            ]

            step_outputs = [
                StepOutput(
                    check.not_none(step_output_snap.node_handle),
                    step_output_snap.name,
                    step_output_snap.dagster_type_key,
                    check.not_none(step_output_snap.properties),
                )
                for step_output_snap in output_snaps
            ]

            if step_snap.kind == StepKind.COMPUTE:
                step: IExecutionStep = ExecutionStep(
                    check.inst(
                        step_snap.step_handle,
                        (StepHandle, ResolvedFromDynamicStepHandle),
                    ),
                    job_name,
                    step_inputs,  # type: ignore  # (plain StepInput only)
                    step_outputs,
                    step_snap.tags,
                    step_snap.pool,
                )
            elif step_snap.kind == StepKind.UNRESOLVED_MAPPED:
                step = UnresolvedMappedExecutionStep(
                    check.inst(
                        step_snap.step_handle,
                        UnresolvedStepHandle,
                    ),
                    job_name,
                    step_inputs,  # type: ignore  # (StepInput or UnresolvedMappedStepInput only)
                    step_outputs,
                    step_snap.tags,
                    step_snap.pool,
                )
            elif step_snap.kind == StepKind.UNRESOLVED_COLLECT:
                step = UnresolvedCollectExecutionStep(
                    check.inst(step_snap.step_handle, StepHandle),
                    job_name,
                    step_inputs,  # type: ignore  # (StepInput or UnresolvedCollectStepInput only)
                    step_outputs,
                    step_snap.tags,
                    step_snap.pool,
                )
            else:
                raise Exception(f"Unexpected step kind {step_snap.kind}")

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
    step_dict: dict[StepHandleUnion, IExecutionStep],
    step_dict_by_key: dict[str, IExecutionStep],
    executable_map: dict[str, Union[StepHandle, ResolvedFromDynamicStepHandle]],
    resolvable_map: dict[frozenset[str], Sequence[Union[StepHandle, UnresolvedStepHandle]]],
    step_handles_to_execute: Sequence[StepHandleUnion],
    dynamic_mappings: Mapping[str, Mapping[str, Optional[Sequence[str]]]],
) -> None:
    resolved_steps: list[ExecutionStep] = []
    key_sets_to_clear: list[frozenset[str]] = []

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


def can_isolate_steps(job_def: JobDefinition) -> bool:
    """Returns true if every output definition in the pipeline uses an IO manager that's not
    the mem_io_manager.

    If true, this indicates that it's OK to execute steps in their own processes, because their
    outputs will be available to other processes.
    """
    output_defs = [
        output_def for node_def in job_def.all_node_defs for output_def in node_def.output_defs
    ]
    for output_def in output_defs:
        if job_def.resource_defs[output_def.io_manager_key] == mem_io_manager:
            return False

    return True


def _check_persistent_storage_requirement(
    job_def: JobDefinition,
    resolved_run_config: ResolvedRunConfig,
) -> None:
    executor_def = job_def.executor_def
    requirements_lst = executor_def.get_requirements(
        resolved_run_config.execution.execution_engine_config
    )
    if ExecutorRequirement.PERSISTENT_OUTPUTS not in requirements_lst:
        return

    if not can_isolate_steps(job_def):
        raise DagsterUnmetExecutorRequirementsError(
            "You have attempted to use an executor that uses multiple processes, but your"
            " job includes op outputs that will not be stored somewhere where other"
            " processes can retrieve them. Please use a persistent IO manager for these outputs."
            ' E.g. with\n   the_graph.to_job(resource_defs={"io_manager": fs_io_manager})'
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
                event_record.dagster_event.event_specific_data.step_output_handle  # type: ignore
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
    step_dict: dict[StepHandleUnion, IExecutionStep],
    step_dict_by_key: dict[str, IExecutionStep],
    step_handles_to_execute: Sequence[StepHandleUnion],
    job_def: JobDefinition,
    resolved_run_config: ResolvedRunConfig,
    executable_map: Mapping[str, Union[StepHandle, ResolvedFromDynamicStepHandle]],
) -> bool:
    """Check if all the border steps of the current run have non-in-memory IO managers for reexecution.

    Border steps: all the steps that don't have upstream steps to execute, i.e. indegree is 0).
    """
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
                io_manager_key = _get_manager_key(step_dict_by_key, step_output_handle, job_def)
                manager_def = job_def.resource_defs.get(io_manager_key)
                if (
                    # no IO manager is configured
                    not manager_def
                    # IO manager is non persistent
                    or manager_def == mem_io_manager
                ):
                    return False
    return True


def _get_steps_to_execute_by_level(
    step_dict: Mapping[StepHandleUnion, IExecutionStep],
    step_dict_by_key: Mapping[str, IExecutionStep],
    step_handles_to_execute: Sequence[StepHandleUnion],
    executable_map: Mapping[str, Union[StepHandle, ResolvedFromDynamicStepHandle]],
) -> Sequence[Sequence[ExecutionStep]]:
    return [
        [cast(ExecutionStep, step_dict_by_key[step_key]) for step_key in sorted(step_key_level)]
        for step_key_level in toposort(
            _get_executable_step_deps(step_dict, step_handles_to_execute, executable_map)
        )
    ]


def _get_executable_step_deps(
    step_dict: Mapping[StepHandleUnion, IExecutionStep],
    step_handles_to_execute: Sequence[StepHandleUnion],
    executable_map: Mapping[str, Union[StepHandle, ResolvedFromDynamicStepHandle]],
) -> Mapping[str, set[str]]:
    """Returns:
    Dict[str, Set[str]]: Maps step keys to sets of step keys that they depend on. Includes
        only steps that are included in step_handles_to_execute.
    """
    deps = {}

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


def _get_manager_key(
    step_dict_by_key: Mapping[str, IExecutionStep],
    step_output_handle: StepOutputHandle,
    pipeline_def: JobDefinition,
) -> str:
    step_output = _get_step_output(step_dict_by_key, step_output_handle)
    node_handle = step_output.node_handle
    output_def = pipeline_def.get_node(node_handle).output_def_named(step_output.name)
    return output_def.io_manager_key


# computes executable_map and resolvable_map and returns them as a tuple. Also
# may modify the passed in step_dict to include resolved step using known_state.
def _compute_step_maps(
    step_dict: dict[StepHandleUnion, IExecutionStep],
    step_dict_by_key: dict[str, IExecutionStep],
    step_handles_to_execute: Sequence[StepHandleUnion],
    known_state: Optional[KnownExecutionState],
) -> tuple[
    dict[str, Union[StepHandle, ResolvedFromDynamicStepHandle]],
    dict[frozenset[str], Sequence[Union[StepHandle, UnresolvedStepHandle]]],
]:
    check.sequence_param(
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
    past_mappings = known_state.dynamic_mappings if known_state else {}

    executable_map: dict[str, Union[StepHandle, ResolvedFromDynamicStepHandle]] = {}
    resolvable_map: dict[frozenset[str], list[Union[StepHandle, UnresolvedStepHandle]]] = (
        defaultdict(list)
    )
    for handle in step_handles_to_execute:
        step = step_dict[handle]
        if isinstance(step, ExecutionStep):
            executable_map[step.key] = step.handle
        elif isinstance(step, (UnresolvedMappedExecutionStep, UnresolvedCollectExecutionStep)):
            for key in step.resolved_by_step_keys:
                if key not in step_keys_to_execute and key not in past_mappings:
                    raise DagsterInvariantViolationError(
                        f'Unresolved ExecutionStep "{step.key}" is resolved by "{key}" which is not'
                        " part of the current step selection or known state from parent run."
                    )

            resolvable_map[step.resolved_by_step_keys].append(step.handle)
        else:
            check.invariant(
                step.key in executable_map, "Expect all steps to be executable or resolvable"
            )

    if past_mappings:
        _update_from_resolved_dynamic_outputs(
            step_dict,
            step_dict_by_key,
            executable_map,
            dict(resolvable_map),
            step_handles_to_execute,
            past_mappings,
        )

    return (executable_map, dict(resolvable_map))
