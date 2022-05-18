from functools import update_wrapper
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    FrozenSet,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

import dagster._check as check
from dagster.core.definitions.composition import MappedInputPlaceholder
from dagster.core.definitions.dependency import (
    DependencyDefinition,
    DynamicCollectDependencyDefinition,
    IDependencyDefinition,
    MultiDependencyDefinition,
    Node,
    NodeHandle,
    NodeInvocation,
    SolidOutputHandle,
)
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.node_definition import NodeDefinition
from dagster.core.definitions.policy import RetryPolicy
from dagster.core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvalidSubsetError,
)
from dagster.core.selector.subset_selector import (
    AssetSelectionData,
    LeafNodeSelection,
    OpSelectionData,
    parse_op_selection,
)
from dagster.core.storage.fs_asset_io_manager import fs_asset_io_manager
from dagster.core.utils import str_format_set
from dagster.utils import merge_dicts

from .asset_layer import AssetLayer, build_asset_selection_job
from .config import ConfigMapping
from .executor_definition import ExecutorDefinition
from .graph_definition import GraphDefinition, SubselectedGraphDefinition
from .hook_definition import HookDefinition
from .logger_definition import LoggerDefinition
from .mode import ModeDefinition
from .partition import PartitionSetDefinition, PartitionedConfig, PartitionsDefinition
from .pipeline_definition import PipelineDefinition
from .preset import PresetDefinition
from .resource_definition import ResourceDefinition
from .run_request import RunRequest
from .version_strategy import VersionStrategy

if TYPE_CHECKING:
    from dagster.core.execution.execute_in_process_result import ExecuteInProcessResult
    from dagster.core.instance import DagsterInstance
    from dagster.core.snap import PipelineSnapshot


class JobDefinition(PipelineDefinition):
    def __init__(
        self,
        graph_def: GraphDefinition,
        resource_defs: Optional[Dict[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
        logger_defs: Optional[Dict[str, LoggerDefinition]] = None,
        config_mapping: Optional[ConfigMapping] = None,
        partitioned_config: Optional[PartitionedConfig] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        preset_defs: Optional[List[PresetDefinition]] = None,
        tags: Optional[Dict[str, Any]] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        op_retry_policy: Optional[RetryPolicy] = None,
        version_strategy: Optional[VersionStrategy] = None,
        _subset_selection_data: Optional[Union[OpSelectionData, AssetSelectionData]] = None,
        asset_layer: Optional[AssetLayer] = None,
        _input_values: Optional[Mapping[str, object]] = None,
    ):

        # Exists for backcompat - JobDefinition is implemented as a single-mode pipeline.
        mode_def = ModeDefinition(
            resource_defs=resource_defs,
            logger_defs=logger_defs,
            executor_defs=[executor_def] if executor_def else None,
            _config_mapping=config_mapping,
            _partitioned_config=partitioned_config,
        )

        self._cached_partition_set: Optional["PartitionSetDefinition"] = None
        self._subset_selection_data = check.opt_inst_param(
            _subset_selection_data,
            "_subset_selection_data",
            (OpSelectionData, AssetSelectionData),
        )
        self._input_values: Mapping[str, object] = check.opt_mapping_param(
            _input_values, "_input_values"
        )
        for input_name in sorted(list(self._input_values.keys())):
            if not graph_def.has_input(input_name):
                job_name = name or graph_def.name
                raise DagsterInvalidDefinitionError(
                    f"Error when constructing JobDefinition '{job_name}': Input value provided for key '{input_name}', but job has no top-level input with that name."
                )

        super(JobDefinition, self).__init__(
            name=name,
            description=description,
            mode_defs=[mode_def],
            preset_defs=preset_defs,
            tags=tags,
            hook_defs=hook_defs,
            solid_retry_policy=op_retry_policy,
            graph_def=graph_def,
            version_strategy=version_strategy,
            asset_layer=asset_layer,
        )

    @property
    def target_type(self) -> str:
        return "job"

    @property
    def is_job(self) -> bool:
        return True

    def describe_target(self):
        return f"{self.target_type} '{self.name}'"

    @property
    def executor_def(self) -> ExecutorDefinition:
        return self.get_mode_definition().executor_defs[0]

    @property
    def resource_defs(self) -> Mapping[str, ResourceDefinition]:
        return self.get_mode_definition().resource_defs

    @property
    def partitioned_config(self) -> Optional[PartitionedConfig]:
        return self.get_mode_definition().partitioned_config

    @property
    def config_mapping(self) -> Optional[ConfigMapping]:
        return self.get_mode_definition().config_mapping

    @property
    def loggers(self) -> Mapping[str, LoggerDefinition]:
        return self.get_mode_definition().loggers

    def execute_in_process(
        self,
        run_config: Optional[Dict[str, Any]] = None,
        instance: Optional["DagsterInstance"] = None,
        partition_key: Optional[str] = None,
        raise_on_error: bool = True,
        op_selection: Optional[List[str]] = None,
        asset_selection: Optional[List[AssetKey]] = None,
        run_id: Optional[str] = None,
        input_values: Optional[Mapping[str, object]] = None,
    ) -> "ExecuteInProcessResult":
        """
        Execute the Job in-process, gathering results in-memory.

        The `executor_def` on the Job will be ignored, and replaced with the in-process executor.
        If using the default `io_manager`, it will switch from filesystem to in-memory.


        Args:
            run_config (Optional[Dict[str, Any]]:
                The configuration for the run
            instance (Optional[DagsterInstance]):
                The instance to execute against, an ephemeral one will be used if none provided.
            partition_key: (Optional[str])
                The string partition key that specifies the run config to execute. Can only be used
                to select run config for jobs with partitioned config.
            raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
                Defaults to ``True``.
            op_selection (Optional[List[str]]): A list of op selection queries (including single op
                names) to execute. For example:
                * ``['some_op']``: selects ``some_op`` itself.
                * ``['*some_op']``: select ``some_op`` and all its ancestors (upstream dependencies).
                * ``['*some_op+++']``: select ``some_op``, all its ancestors, and its descendants
                (downstream dependencies) within 3 levels down.
                * ``['*some_op', 'other_op_a', 'other_op_b+']``: select ``some_op`` and all its
                ancestors, ``other_op_a`` itself, and ``other_op_b`` and its direct child ops.
            input_values (Optional[Mapping[str, Any]]):
                A dictionary that maps python objects to the top-level inputs of the job. Input values provided here will override input values that have been provided to the job directly.
        Returns:
            :py:class:`~dagster.ExecuteInProcessResult`

        """
        from dagster.core.definitions.executor_definition import execute_in_process_executor
        from dagster.core.execution.execute_in_process import core_execute_in_process

        run_config = check.opt_dict_param(run_config, "run_config")
        op_selection = check.opt_list_param(op_selection, "op_selection", str)
        asset_selection = check.opt_list_param(asset_selection, "asset_selection", AssetKey)

        check.invariant(
            not (op_selection and asset_selection),
            "op_selection and asset_selection cannot both be provided as args to execute_in_process",
        )

        partition_key = check.opt_str_param(partition_key, "partition_key")
        input_values = check.opt_mapping_param(input_values, "input_values")

        # Combine provided input values at execute_in_process with input values
        # provided to the definition. Input values provided at
        # execute_in_process will override those provided on the definition.
        input_values = merge_dicts(self._input_values, input_values)

        resource_defs = dict(self.resource_defs)
        logger_defs = dict(self.loggers)
        ephemeral_job = JobDefinition(
            name=self._name,
            graph_def=self._graph_def,
            resource_defs=_swap_default_io_man(resource_defs, self),
            executor_def=execute_in_process_executor,
            logger_defs=logger_defs,
            hook_defs=self.hook_defs,
            config_mapping=self.config_mapping,
            partitioned_config=self.partitioned_config,
            tags=self.tags,
            op_retry_policy=self._solid_retry_policy,
            version_strategy=self.version_strategy,
            asset_layer=self.asset_layer,
            _input_values=input_values,
        )

        ephemeral_job = ephemeral_job.get_job_def_for_subset_selection(
            op_selection, frozenset(asset_selection) if asset_selection else None
        )

        tags = None
        if partition_key:
            if not self.partitioned_config:
                check.failed(
                    f"Provided partition key `{partition_key}` for job `{self._name}` without a partitioned config"
                )
            check.invariant(
                not run_config,
                "Cannot provide both run_config and partition_key arguments to `execute_in_process`",
            )
            partition_set = self.get_partition_set_def()
            if not partition_set:
                check.failed(
                    f"Provided partition key `{partition_key}` for job `{self._name}` without a partitioned config"
                )

            partition = partition_set.get_partition(partition_key)
            run_config = partition_set.run_config_for_partition(partition)
            tags = partition_set.tags_for_partition(partition)

        return core_execute_in_process(
            node=self._graph_def,
            ephemeral_pipeline=ephemeral_job,
            run_config=run_config,
            instance=instance,
            output_capturing_enabled=True,
            raise_on_error=raise_on_error,
            run_tags=tags,
            run_id=run_id,
            asset_selection=frozenset(asset_selection),
        )

    @property
    def op_selection_data(self) -> Optional[OpSelectionData]:
        return (
            self._subset_selection_data
            if isinstance(self._subset_selection_data, OpSelectionData)
            else None
        )

    @property
    def asset_selection_data(self) -> Optional[AssetSelectionData]:
        return (
            self._subset_selection_data
            if isinstance(self._subset_selection_data, AssetSelectionData)
            else None
        )

    def get_job_def_for_subset_selection(
        self,
        op_selection: Optional[List[str]] = None,
        asset_selection: Optional[FrozenSet[AssetKey]] = None,
    ):
        check.invariant(
            not (op_selection and asset_selection),
            "op_selection and asset_selection cannot both be provided as args to execute_in_process",
        )
        if op_selection:
            return self._get_job_def_for_op_selection(op_selection)
        if asset_selection:  # asset_selection:
            return self._get_job_def_for_asset_selection(asset_selection)
        else:
            return self

    def _get_job_def_for_asset_selection(
        self,
        asset_selection: Optional[FrozenSet[AssetKey]] = None,
    ) -> "JobDefinition":
        asset_selection = check.opt_set_param(asset_selection, "asset_selection", AssetKey)

        for asset in asset_selection:
            nonexistent_assets = [
                asset for asset in asset_selection if asset not in self.asset_layer.asset_keys
            ]
            nonexistent_asset_strings = [
                asset_str
                for asset_str in (asset.to_string() for asset in nonexistent_assets)
                if asset_str
            ]
            if nonexistent_assets:
                raise DagsterInvalidSubsetError(
                    "Assets provided in asset_selection argument "
                    f"{', '.join(nonexistent_asset_strings)} do not exist in parent asset group or job."
                )
        asset_selection_data = AssetSelectionData(
            asset_selection=asset_selection,
            parent_job_def=self,
        )
        new_job = build_asset_selection_job(
            job_to_subselect=self,
            asset_selection=asset_selection,
            asset_layer=self.asset_layer,
            asset_selection_data=asset_selection_data,
        )
        return new_job

    def _get_job_def_for_op_selection(
        self,
        op_selection: Optional[List[str]] = None,
    ) -> "JobDefinition":
        if not op_selection:
            return self

        op_selection = check.opt_list_param(op_selection, "op_selection", str)

        resolved_op_selection_dict = parse_op_selection(self, op_selection)

        try:
            sub_graph = get_subselected_graph_definition(self.graph, resolved_op_selection_dict)

            return JobDefinition(
                name=self.name,
                description=self.description,
                resource_defs=dict(self.resource_defs),
                logger_defs=dict(self.loggers),
                executor_def=self.executor_def,
                config_mapping=self.config_mapping,
                partitioned_config=self.partitioned_config,
                preset_defs=self.preset_defs,
                tags=self.tags,
                hook_defs=self.hook_defs,
                op_retry_policy=self._solid_retry_policy,
                graph_def=sub_graph,
                version_strategy=self.version_strategy,
                _subset_selection_data=OpSelectionData(
                    op_selection=op_selection,
                    resolved_op_selection=set(
                        resolved_op_selection_dict.keys()
                    ),  # equivalent to solids_to_execute. currently only gets top level nodes.
                    parent_job_def=self,  # used by pipeline snapshot lineage
                ),
                # TODO: subset this structure.
                # https://github.com/dagster-io/dagster/issues/7541
                asset_layer=self.asset_layer,
            )
        except DagsterInvalidDefinitionError as exc:
            # This handles the case when you construct a subset such that an unsatisfied
            # input cannot be loaded from config. Instead of throwing a DagsterInvalidDefinitionError,
            # we re-raise a DagsterInvalidSubsetError.
            raise DagsterInvalidSubsetError(
                f"The attempted subset {str_format_set(resolved_op_selection_dict)} for graph "
                f"{self.graph.name} results in an invalid graph."
            ) from exc

    def get_partition_set_def(self) -> Optional["PartitionSetDefinition"]:

        mode = self.get_mode_definition()
        if not mode.partitioned_config:
            return None

        if not self._cached_partition_set:

            tags_fn = mode.partitioned_config.tags_for_partition_fn
            if not tags_fn:
                tags_fn = lambda _: {}
            self._cached_partition_set = PartitionSetDefinition(
                job_name=self.name,
                name=f"{self.name}_partition_set",
                partitions_def=mode.partitioned_config.partitions_def,
                run_config_fn_for_partition=mode.partitioned_config.run_config_for_partition_fn,
                tags_fn_for_partition=tags_fn,
                mode=mode.name,
            )

        return self._cached_partition_set

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        mode = self.get_mode_definition()
        if not mode.partitioned_config:
            return None

        return mode.partitioned_config.partitions_def

    def run_request_for_partition(self, partition_key: str, run_key: Optional[str]) -> RunRequest:
        partition_set = self.get_partition_set_def()
        if not partition_set:
            check.failed("Called run_request_for_partition on a non-partitioned job")

        partition = partition_set.get_partition(partition_key)
        run_config = partition_set.run_config_for_partition(partition)
        tags = partition_set.tags_for_partition(partition)
        return RunRequest(run_key=run_key, run_config=run_config, tags=tags)

    def with_hooks(self, hook_defs: AbstractSet[HookDefinition]) -> "JobDefinition":
        """Apply a set of hooks to all op instances within the job."""

        hook_defs = check.set_param(hook_defs, "hook_defs", of_type=HookDefinition)

        job_def = JobDefinition(
            name=self.name,
            graph_def=self._graph_def,
            resource_defs=dict(self.resource_defs),
            logger_defs=dict(self.loggers),
            executor_def=self.executor_def,
            partitioned_config=self.partitioned_config,
            config_mapping=self.config_mapping,
            preset_defs=self.preset_defs,
            tags=self.tags,
            hook_defs=hook_defs | self.hook_defs,
            description=self._description,
            op_retry_policy=self._solid_retry_policy,
            asset_layer=self.asset_layer,
            _subset_selection_data=self._subset_selection_data,
        )

        update_wrapper(job_def, self, updated=())

        return job_def

    def get_parent_pipeline_snapshot(self) -> Optional["PipelineSnapshot"]:
        if self.op_selection_data:
            return self.op_selection_data.parent_job_def.get_pipeline_snapshot()
        elif self.asset_selection_data:
            return self.asset_selection_data.parent_job_def.get_pipeline_snapshot()
        else:
            return None

    def has_direct_input_value(self, input_name: str) -> bool:
        return input_name in self._input_values

    def get_direct_input_value(self, input_name: str) -> object:
        if input_name not in self._input_values:
            raise DagsterInvalidInvocationError(
                f"On job '{self.name}', attempted to retrieve input value for input named '{input_name}', but no value was provided. Provided input values: {sorted(list(self._input_values.keys()))}"
            )
        return self._input_values[input_name]


def _swap_default_io_man(resources: Dict[str, ResourceDefinition], job: PipelineDefinition):
    """
    Used to create the user facing experience of the default io_manager
    switching to in-memory when using execute_in_process.
    """
    from dagster.core.storage.mem_io_manager import mem_io_manager

    from .graph_definition import default_job_io_manager

    if (
        # pylint: disable=comparison-with-callable
        resources.get("io_manager") in [default_job_io_manager, fs_asset_io_manager]
        and job.version_strategy is None
    ):
        updated_resources = dict(resources)
        updated_resources["io_manager"] = mem_io_manager
        return updated_resources

    return resources


def _dep_key_of(node: Node) -> NodeInvocation:
    return NodeInvocation(
        name=node.definition.name,
        alias=node.name,
        tags=node.tags,
        hook_defs=node.hook_defs,
        retry_policy=node.retry_policy,
    )


def get_subselected_graph_definition(
    graph: GraphDefinition,
    resolved_op_selection_dict: Dict,
    parent_handle: Optional[NodeHandle] = None,
) -> SubselectedGraphDefinition:
    deps: Dict[
        Union[str, NodeInvocation],
        Dict[str, IDependencyDefinition],
    ] = {}

    selected_nodes: List[Tuple[str, NodeDefinition]] = []

    for node in graph.solids_in_topological_order:
        node_handle = NodeHandle(node.name, parent=parent_handle)
        # skip if the node isn't selected
        if node.name not in resolved_op_selection_dict:
            continue

        # rebuild graph if any nodes inside the graph are selected
        if node.is_graph and resolved_op_selection_dict[node.name] is not LeafNodeSelection:
            definition = get_subselected_graph_definition(
                node.definition,
                resolved_op_selection_dict[node.name],
                parent_handle=node_handle,
            )
        # use definition if the node as a whole is selected. this includes selecting the entire graph
        else:
            definition = node.definition
        selected_nodes.append((node.name, definition))

        # build dependencies for the node. we do it for both cases because nested graphs can have
        # inputs and outputs too
        deps[_dep_key_of(node)] = {}
        for input_handle in node.input_handles():
            if graph.dependency_structure.has_direct_dep(input_handle):
                output_handle = graph.dependency_structure.get_direct_dep(input_handle)
                if output_handle.solid.name in resolved_op_selection_dict:
                    deps[_dep_key_of(node)][input_handle.input_def.name] = DependencyDefinition(
                        solid=output_handle.solid.name, output=output_handle.output_def.name
                    )
            elif graph.dependency_structure.has_dynamic_fan_in_dep(input_handle):
                output_handle = graph.dependency_structure.get_dynamic_fan_in_dep(input_handle)
                if output_handle.solid.name in resolved_op_selection_dict:
                    deps[_dep_key_of(node)][
                        input_handle.input_def.name
                    ] = DynamicCollectDependencyDefinition(
                        solid_name=output_handle.solid.name,
                        output_name=output_handle.output_def.name,
                    )
            elif graph.dependency_structure.has_fan_in_deps(input_handle):
                output_handles = graph.dependency_structure.get_fan_in_deps(input_handle)
                multi_dependencies = [
                    DependencyDefinition(
                        solid=output_handle.solid.name, output=output_handle.output_def.name
                    )
                    for output_handle in output_handles
                    if (
                        isinstance(output_handle, SolidOutputHandle)
                        and output_handle.solid.name in resolved_op_selection_dict
                    )
                ]
                deps[_dep_key_of(node)][input_handle.input_def.name] = MultiDependencyDefinition(
                    cast(
                        List[Union[DependencyDefinition, Type[MappedInputPlaceholder]]],
                        multi_dependencies,
                    )
                )
            # else input is unconnected

    # filter out unselected input/output mapping
    new_input_mappings = list(
        filter(
            lambda input_mapping: input_mapping.maps_to.solid_name
            in [name for name, _ in selected_nodes],
            graph._input_mappings,  # pylint: disable=protected-access
        )
    )
    new_output_mappings = list(
        filter(
            lambda output_mapping: output_mapping.maps_from.solid_name
            in [name for name, _ in selected_nodes],
            graph._output_mappings,  # pylint: disable=protected-access
        )
    )

    return SubselectedGraphDefinition(
        parent_graph_def=graph,
        dependencies=deps,
        node_defs=[definition for _, definition in selected_nodes],
        input_mappings=new_input_mappings,
        output_mappings=new_output_mappings,
    )


def get_direct_input_values_from_job(target: PipelineDefinition) -> Mapping[str, Any]:
    if target.is_job:
        return cast(JobDefinition, target)._input_values  # pylint: disable=protected-access
    else:
        return {}
