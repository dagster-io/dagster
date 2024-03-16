import importlib
import os
import warnings
from datetime import datetime
from functools import update_wrapper
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

import dagster._check as check
from dagster._annotations import deprecated, experimental_param, public
from dagster._config import Field, Shape, StringSource
from dagster._config.config_type import ConfigType
from dagster._config.validate import validate_config
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.dependency import (
    Node,
    NodeHandle,
    NodeInputHandle,
    NodeInvocation,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.op_selection import OpSelection, get_graph_subset
from dagster._core.definitions.partition import DynamicPartitionsDefinition
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_requirement import (
    ResourceRequirement,
    ensure_requirements_satisfied,
)
from dagster._core.definitions.utils import check_valid_name
from dagster._core.errors import (
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvalidSubsetError,
    DagsterInvariantViolationError,
)
from dagster._core.selector.subset_selector import (
    AssetSelectionData,
    OpSelectionData,
)
from dagster._core.storage.io_manager import (
    IOManagerDefinition,
    dagster_maintained_io_manager,
    io_manager,
)
from dagster._core.storage.tags import MEMOIZED_RUN_TAG
from dagster._core.types.dagster_type import DagsterType
from dagster._core.utils import str_format_set
from dagster._utils import IHasInternalInit
from dagster._utils.merger import merge_dicts

from .asset_layer import AssetLayer
from .config import ConfigMapping
from .dependency import (
    DependencyMapping,
    DependencyStructure,
    OpNode,
)
from .executor_definition import ExecutorDefinition, multi_or_in_process_executor
from .graph_definition import GraphDefinition, SubselectedGraphDefinition
from .hook_definition import HookDefinition
from .logger_definition import LoggerDefinition
from .metadata import MetadataValue, RawMetadataValue, normalize_metadata
from .partition import PartitionedConfig, PartitionsDefinition
from .resource_definition import ResourceDefinition
from .run_request import RunRequest
from .utils import DEFAULT_IO_MANAGER_KEY, validate_tags
from .version_strategy import VersionStrategy

if TYPE_CHECKING:
    from dagster._config.snap import ConfigSchemaSnapshot
    from dagster._core.definitions.run_config import RunConfig
    from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
    from dagster._core.execution.resources_init import InitResourceContext
    from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
    from dagster._core.remote_representation.job_index import JobIndex
    from dagster._core.snap import JobSnapshot

    from .run_config_schema import RunConfigSchema

DEFAULT_EXECUTOR_DEF = multi_or_in_process_executor


@experimental_param(param="version_strategy")
class JobDefinition(IHasInternalInit):
    """Defines a Dagster job."""

    _name: str
    _graph_def: GraphDefinition
    _description: Optional[str]
    _tags: Mapping[str, str]
    _metadata: Mapping[str, MetadataValue]
    _current_level_node_defs: Sequence[NodeDefinition]
    _hook_defs: AbstractSet[HookDefinition]
    _op_retry_policy: Optional[RetryPolicy]
    _asset_layer: AssetLayer
    _resource_requirements: Mapping[str, AbstractSet[str]]
    _all_node_defs: Mapping[str, NodeDefinition]
    _cached_run_config_schemas: Dict[str, "RunConfigSchema"]
    _version_strategy: VersionStrategy
    _subset_selection_data: Optional[Union[OpSelectionData, AssetSelectionData]]
    input_values: Mapping[str, object]

    def __init__(
        self,
        *,
        graph_def: GraphDefinition,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
        logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
        name: Optional[str] = None,
        config: Optional[
            Union[ConfigMapping, Mapping[str, object], PartitionedConfig, "RunConfig"]
        ] = None,
        description: Optional[str] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        tags: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        op_retry_policy: Optional[RetryPolicy] = None,
        version_strategy: Optional[VersionStrategy] = None,
        _subset_selection_data: Optional[Union[OpSelectionData, AssetSelectionData]] = None,
        asset_layer: Optional[AssetLayer] = None,
        input_values: Optional[Mapping[str, object]] = None,
        _was_explicitly_provided_resources: Optional[bool] = None,
    ):
        from dagster._core.definitions.run_config import RunConfig, convert_config_input

        self._graph_def = graph_def
        self._current_level_node_defs = self._graph_def.node_defs
        # Recursively explore all nodes in the this job
        self._all_node_defs = _build_all_node_defs(self._current_level_node_defs)
        self._asset_layer = check.opt_inst_param(
            asset_layer, "asset_layer", AssetLayer
        ) or _infer_asset_layer_from_source_asset_deps(graph_def)

        # validates
        self._graph_def.get_inputs_must_be_resolved_top_level(self._asset_layer)

        self._name = check_valid_name(check.str_param(name, "name")) if name else graph_def.name
        self._executor_def = check.opt_inst_param(executor_def, "executor_def", ExecutorDefinition)
        self._loggers = check.opt_nullable_mapping_param(
            logger_defs,
            "logger_defs",
            key_type=str,
            value_type=LoggerDefinition,
        )

        config = check.opt_inst_param(
            config, "config", (Mapping, ConfigMapping, PartitionedConfig, RunConfig)
        )
        config = convert_config_input(config)

        partitions_def = check.opt_inst_param(
            partitions_def, "partitions_def", PartitionsDefinition
        )
        # tags and description can exist on graph as well, but since
        # same graph may be in multiple jobs, keep separate layer
        self._description = check.opt_str_param(description, "description")
        self._tags = validate_tags(tags)
        self._metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str)
        )
        self._hook_defs = check.opt_set_param(hook_defs, "hook_defs")
        self._op_retry_policy = check.opt_inst_param(
            op_retry_policy, "op_retry_policy", RetryPolicy
        )
        self.version_strategy = check.opt_inst_param(
            version_strategy, "version_strategy", VersionStrategy
        )

        _subset_selection_data = check.opt_inst_param(
            _subset_selection_data, "_subset_selection_data", (OpSelectionData, AssetSelectionData)
        )
        input_values = check.opt_mapping_param(input_values, "input_values", key_type=str)

        resource_defs = check.opt_mapping_param(
            resource_defs, "resource_defs", key_type=str, value_type=ResourceDefinition
        )
        for key in resource_defs.keys():
            if not key.isidentifier():
                check.failed(f"Resource key '{key}' must be a valid Python identifier.")
        was_provided_resources = (
            bool(resource_defs)
            if _was_explicitly_provided_resources is None
            else _was_explicitly_provided_resources
        )
        self._resource_defs = {
            DEFAULT_IO_MANAGER_KEY: default_job_io_manager,
            **resource_defs,
        }
        self._required_resource_keys = self._get_required_resource_keys(was_provided_resources)

        self._config_mapping = None
        self._partitioned_config = None
        self._run_config = None
        self._run_config_schema = None
        self._original_config_argument = config

        if partitions_def:
            self._partitioned_config = PartitionedConfig.from_flexible_config(
                config, partitions_def
            )
        else:
            if isinstance(config, ConfigMapping):
                self._config_mapping = config
            elif isinstance(config, PartitionedConfig):
                self._partitioned_config = config
            elif isinstance(config, dict):
                self._run_config = config
                # Using config mapping here is a trick to make it so that the preset will be used even
                # when no config is supplied for the job.
                self._config_mapping = _config_mapping_with_default_value(
                    get_run_config_schema_for_job(
                        graph_def,
                        self.resource_defs,
                        self.executor_def,
                        self.loggers,
                        asset_layer,
                        was_explicitly_provided_resources=was_provided_resources,
                    ),
                    config,
                    self.name,
                )
            elif config is not None:
                check.failed(
                    "config param must be a ConfigMapping, a PartitionedConfig, or a dictionary,"
                    f" but is an object of type {type(config)}"
                )

        self._subset_selection_data = _subset_selection_data
        self.input_values = input_values
        for input_name in sorted(list(self.input_values.keys())):
            if not graph_def.has_input(input_name):
                raise DagsterInvalidDefinitionError(
                    f"Error when constructing JobDefinition '{self.name}': Input value provided for"
                    f" key '{input_name}', but job has no top-level input with that name."
                )

    def dagster_internal_init(
        *,
        graph_def: GraphDefinition,
        resource_defs: Optional[Mapping[str, ResourceDefinition]],
        executor_def: Optional[ExecutorDefinition],
        logger_defs: Optional[Mapping[str, LoggerDefinition]],
        name: Optional[str],
        config: Optional[
            Union[ConfigMapping, Mapping[str, object], PartitionedConfig, "RunConfig"]
        ],
        description: Optional[str],
        partitions_def: Optional[PartitionsDefinition],
        tags: Optional[Mapping[str, Any]],
        metadata: Optional[Mapping[str, RawMetadataValue]],
        hook_defs: Optional[AbstractSet[HookDefinition]],
        op_retry_policy: Optional[RetryPolicy],
        version_strategy: Optional[VersionStrategy],
        _subset_selection_data: Optional[Union[OpSelectionData, AssetSelectionData]],
        asset_layer: Optional[AssetLayer],
        input_values: Optional[Mapping[str, object]],
        _was_explicitly_provided_resources: Optional[bool],
    ) -> "JobDefinition":
        return JobDefinition(
            graph_def=graph_def,
            resource_defs=resource_defs,
            executor_def=executor_def,
            logger_defs=logger_defs,
            name=name,
            config=config,
            description=description,
            partitions_def=partitions_def,
            tags=tags,
            metadata=metadata,
            hook_defs=hook_defs,
            op_retry_policy=op_retry_policy,
            version_strategy=version_strategy,
            _subset_selection_data=_subset_selection_data,
            asset_layer=asset_layer,
            input_values=input_values,
            _was_explicitly_provided_resources=_was_explicitly_provided_resources,
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def tags(self) -> Mapping[str, str]:
        return merge_dicts(self._graph_def.tags, self._tags)

    @property
    def metadata(self) -> Mapping[str, MetadataValue]:
        return self._metadata

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def graph(self) -> GraphDefinition:
        return self._graph_def

    @property
    def dependency_structure(self) -> DependencyStructure:
        return self._graph_def.dependency_structure

    @property
    def dependencies(self) -> DependencyMapping[NodeInvocation]:
        return self._graph_def.dependencies

    @public
    @property
    def executor_def(self) -> ExecutorDefinition:
        """Returns the default :py:class:`ExecutorDefinition` for the job.

        If the user has not specified an executor definition, then this will default to the
        :py:func:`multi_or_in_process_executor`. If a default is specified on the
        :py:class:`Definitions` object the job was provided to, then that will be used instead.
        """
        return self._executor_def or DEFAULT_EXECUTOR_DEF

    @public
    @property
    def has_specified_executor(self) -> bool:
        """Returns True if this job has explicitly specified an executor, and False if the executor
        was inherited through defaults or the :py:class:`Definitions` object the job was provided to.
        """
        return self._executor_def is not None

    @public
    @property
    def resource_defs(self) -> Mapping[str, ResourceDefinition]:
        """Returns the set of ResourceDefinition objects specified on the job.

        This may not be the complete set of resources required by the job, since those can also be
        provided on the :py:class:`Definitions` object the job may be provided to.
        """
        return self._resource_defs

    @public
    @property
    def partitioned_config(self) -> Optional[PartitionedConfig]:
        """The partitioned config for the job, if it has one.

        A partitioned config defines a way to map partition keys to run config for the job.
        """
        return self._partitioned_config

    @public
    @property
    def config_mapping(self) -> Optional[ConfigMapping]:
        """The config mapping for the job, if it has one.

        A config mapping defines a way to map a top-level config schema to run config for the job.
        """
        return self._config_mapping

    @public
    @property
    def loggers(self) -> Mapping[str, LoggerDefinition]:
        """Returns the set of LoggerDefinition objects specified on the job.

        If the user has not specified a mapping of :py:class:`LoggerDefinition` objects, then this
        will default to the :py:func:`colored_console_logger` under the key `console`. If a default
        is specified on the :py:class:`Definitions` object the job was provided to, then that will
        be used instead.
        """
        from dagster._loggers import default_loggers

        return self._loggers or default_loggers()

    @public
    @property
    def has_specified_loggers(self) -> bool:
        """Returns true if the job explicitly set loggers, and False if loggers were inherited
        through defaults or the :py:class:`Definitions` object the job was provided to.
        """
        return self._loggers is not None

    @property
    def required_resource_keys(self) -> AbstractSet[str]:
        return self._required_resource_keys

    @property
    def run_config(self) -> Optional[Mapping[str, Any]]:
        return self._run_config

    @property
    def run_config_schema(self) -> "RunConfigSchema":
        if self._run_config_schema is None:
            self._run_config_schema = _create_run_config_schema(self, self.required_resource_keys)
        return self._run_config_schema

    @public
    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        """Returns the :py:class:`PartitionsDefinition` for the job, if it has one.

        A partitions definition defines the set of partition keys the job operates on.
        """
        return None if not self.partitioned_config else self.partitioned_config.partitions_def

    @property
    def hook_defs(self) -> AbstractSet[HookDefinition]:
        return self._hook_defs

    @property
    def asset_layer(self) -> AssetLayer:
        return self._asset_layer

    @property
    def all_node_defs(self) -> Sequence[NodeDefinition]:
        return list(self._all_node_defs.values())

    @property
    def top_level_node_defs(self) -> Sequence[NodeDefinition]:
        return self._current_level_node_defs

    def node_def_named(self, name: str) -> NodeDefinition:
        check.str_param(name, "name")

        check.invariant(name in self._all_node_defs, f"{name} not found")
        return self._all_node_defs[name]

    def has_node(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self._all_node_defs

    def get_node(self, handle: NodeHandle) -> Node:
        return self._graph_def.get_node(handle)

    def get_op(self, handle: NodeHandle) -> OpNode:
        node = self.get_node(handle)
        assert isinstance(
            node, OpNode
        ), f"Tried to retrieve node {handle} as op, but it represents a nested graph."
        return node

    def has_node_named(self, name: str) -> bool:
        return self._graph_def.has_node_named(name)

    def get_node_named(self, name: str) -> Node:
        return self._graph_def.node_named(name)

    @property
    def nodes(self) -> Sequence[Node]:
        return self._graph_def.nodes

    @property
    def nodes_in_topological_order(self) -> Sequence[Node]:
        return self._graph_def.nodes_in_topological_order

    def all_dagster_types(self) -> Iterable[DagsterType]:
        return self._graph_def.all_dagster_types()

    def has_dagster_type(self, name: str) -> bool:
        return self._graph_def.has_dagster_type(name)

    def dagster_type_named(self, name: str) -> DagsterType:
        return self._graph_def.dagster_type_named(name)

    def describe_target(self) -> str:
        return f"job '{self.name}'"

    def is_using_memoization(self, run_tags: Mapping[str, str]) -> bool:
        tags = merge_dicts(self.tags, run_tags)
        # If someone provides a false value for memoized run tag, then they are intentionally
        # switching off memoization.
        if tags.get(MEMOIZED_RUN_TAG) == "false":
            return False
        return (
            MEMOIZED_RUN_TAG in tags and tags.get(MEMOIZED_RUN_TAG) == "true"
        ) or self.version_strategy is not None

    def get_required_resource_defs(self) -> Mapping[str, ResourceDefinition]:
        return {
            resource_key: resource
            for resource_key, resource in self.resource_defs.items()
            if resource_key in self.required_resource_keys
        }

    def _get_required_resource_keys(self, validate_requirements: bool = False) -> AbstractSet[str]:
        from ..execution.resources_init import get_transitive_required_resource_keys

        requirements = self._get_resource_requirements()
        if validate_requirements:
            ensure_requirements_satisfied(self.resource_defs, requirements)
        required_keys = {req.key for req in requirements}
        if validate_requirements:
            return required_keys.union(
                get_transitive_required_resource_keys(required_keys, self.resource_defs)
            )
        else:
            return required_keys

    def _get_resource_requirements(self) -> Sequence[ResourceRequirement]:
        return [
            *self._graph_def.get_resource_requirements(self.asset_layer),
            *[
                req
                for hook_def in self._hook_defs
                for req in hook_def.get_resource_requirements(outer_context=f"job '{self._name}'")
            ],
        ]

    def validate_resource_requirements_satisfied(self) -> None:
        resource_requirements = self._get_resource_requirements()
        ensure_requirements_satisfied(self.resource_defs, resource_requirements)

    def is_missing_required_resources(self) -> bool:
        requirements = self._get_resource_requirements()
        for requirement in requirements:
            if not requirement.resources_contain_key(self.resource_defs):
                return True
        return False

    def get_all_hooks_for_handle(self, handle: NodeHandle) -> AbstractSet[HookDefinition]:
        """Gather all the hooks for the given node from all places possibly attached with a hook.

        A hook can be attached to any of the following objects
        * Node (node invocation)
        * JobDefinition

        Args:
            handle (NodeHandle): The node's handle

        Returns:
            FrozenSet[HookDefinition]
        """
        check.inst_param(handle, "handle", NodeHandle)
        hook_defs: Set[HookDefinition] = set()

        current = handle
        lineage = []
        while current:
            lineage.append(current.name)
            current = current.parent

        # hooks on top-level node
        name = lineage.pop()
        node = self._graph_def.node_named(name)
        hook_defs = hook_defs.union(node.hook_defs)

        # hooks on non-top-level nodes
        while lineage:
            name = lineage.pop()
            # While lineage is non-empty, definition is guaranteed to be a graph
            definition = cast(GraphDefinition, node.definition)
            node = definition.node_named(name)
            hook_defs = hook_defs.union(node.hook_defs)

        # hooks applied to a job definition will run on every node
        hook_defs = hook_defs.union(self.hook_defs)

        return frozenset(hook_defs)

    def get_retry_policy_for_handle(self, handle: NodeHandle) -> Optional[RetryPolicy]:
        node = self.get_node(handle)
        definition = node.definition

        if node.retry_policy:
            return node.retry_policy
        elif isinstance(definition, OpDefinition) and definition.retry_policy:
            return definition.retry_policy

        # could be expanded to look in graph containers
        else:
            return self._op_retry_policy

    # make Callable for decorator reference updates
    def __call__(self, *args, **kwargs):
        raise DagsterInvariantViolationError(
            f"Attempted to call job '{self.name}' directly. Jobs should be invoked by "
            "using an execution API function (e.g. `job.execute_in_process`)."
        )

    @public
    def execute_in_process(
        self,
        run_config: Optional[Union[Mapping[str, Any], "RunConfig"]] = None,
        instance: Optional["DagsterInstance"] = None,
        partition_key: Optional[str] = None,
        raise_on_error: bool = True,
        op_selection: Optional[Sequence[str]] = None,
        asset_selection: Optional[Sequence[AssetKey]] = None,
        run_id: Optional[str] = None,
        input_values: Optional[Mapping[str, object]] = None,
        tags: Optional[Mapping[str, str]] = None,
        resources: Optional[Mapping[str, object]] = None,
    ) -> "ExecuteInProcessResult":
        """Execute the Job in-process, gathering results in-memory.

        The `executor_def` on the Job will be ignored, and replaced with the in-process executor.
        If using the default `io_manager`, it will switch from filesystem to in-memory.


        Args:
            run_config (Optional[Mapping[str, Any]]:
                The configuration for the run
            instance (Optional[DagsterInstance]):
                The instance to execute against, an ephemeral one will be used if none provided.
            partition_key: (Optional[str])
                The string partition key that specifies the run config to execute. Can only be used
                to select run config for jobs with partitioned config.
            raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
                Defaults to ``True``.
            op_selection (Optional[Sequence[str]]): A list of op selection queries (including single op
                names) to execute. For example:
                * ``['some_op']``: selects ``some_op`` itself.
                * ``['*some_op']``: select ``some_op`` and all its ancestors (upstream dependencies).
                * ``['*some_op+++']``: select ``some_op``, all its ancestors, and its descendants
                (downstream dependencies) within 3 levels down.
                * ``['*some_op', 'other_op_a', 'other_op_b+']``: select ``some_op`` and all its
                ancestors, ``other_op_a`` itself, and ``other_op_b`` and its direct child ops.
            input_values (Optional[Mapping[str, Any]]):
                A dictionary that maps python objects to the top-level inputs of the job. Input
                values provided here will override input values that have been provided to the job
                directly.
            resources (Optional[Mapping[str, Any]]):
                The resources needed if any are required. Can provide resource instances directly,
                or resource definitions.

        Returns:
            :py:class:`~dagster.ExecuteInProcessResult`

        """
        from dagster._core.definitions.executor_definition import execute_in_process_executor
        from dagster._core.definitions.run_config import convert_config_input
        from dagster._core.execution.build_resources import wrap_resources_for_execution
        from dagster._core.execution.execute_in_process import core_execute_in_process

        run_config = check.opt_mapping_param(convert_config_input(run_config), "run_config")
        op_selection = check.opt_sequence_param(op_selection, "op_selection", str)
        asset_selection = check.opt_sequence_param(asset_selection, "asset_selection", AssetKey)
        resources = check.opt_mapping_param(resources, "resources", key_type=str)

        resource_defs = wrap_resources_for_execution(resources)

        check.invariant(
            not (op_selection and asset_selection),
            "op_selection and asset_selection cannot both be provided as args to"
            " execute_in_process",
        )

        partition_key = check.opt_str_param(partition_key, "partition_key")
        input_values = check.opt_mapping_param(input_values, "input_values")

        # Combine provided input values at execute_in_process with input values
        # provided to the definition. Input values provided at
        # execute_in_process will override those provided on the definition.
        input_values = merge_dicts(self.input_values, input_values)

        bound_resource_defs = dict(self.resource_defs)
        ephemeral_job = JobDefinition.dagster_internal_init(
            name=self._name,
            graph_def=self._graph_def,
            resource_defs={**_swap_default_io_man(bound_resource_defs, self), **resource_defs},
            executor_def=execute_in_process_executor,
            logger_defs=self._loggers,
            hook_defs=self.hook_defs,
            config=self.config_mapping or self.partitioned_config or self.run_config,
            tags=self.tags,
            op_retry_policy=self._op_retry_policy,
            version_strategy=self.version_strategy,
            asset_layer=self.asset_layer,
            input_values=input_values,
            description=self.description,
            partitions_def=self.partitions_def,
            metadata=self.metadata,
            _subset_selection_data=None,  # this is added below
            _was_explicitly_provided_resources=True,
        )

        ephemeral_job = ephemeral_job.get_subset(
            op_selection=op_selection,
            asset_selection=frozenset(asset_selection) if asset_selection else None,
        )

        merged_tags = merge_dicts(self.tags, tags or {})
        if partition_key:
            if not (self.partitions_def and self.partitioned_config):
                check.failed("Attempted to execute a partitioned run for a non-partitioned job")
            self.partitions_def.validate_partition_key(
                partition_key, dynamic_partitions_store=instance
            )

            run_config = (
                run_config
                if run_config
                else self.partitioned_config.get_run_config_for_partition_key(partition_key)
            )
            merged_tags.update(
                self.partitioned_config.get_tags_for_partition_key(
                    partition_key, job_name=self.name
                )
            )

        return core_execute_in_process(
            ephemeral_job=ephemeral_job,
            run_config=run_config,
            instance=instance,
            output_capturing_enabled=True,
            raise_on_error=raise_on_error,
            run_tags=merged_tags,
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

    @property
    def is_subset(self) -> bool:
        return bool(self._subset_selection_data)

    def get_subset(
        self,
        *,
        op_selection: Optional[Iterable[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
        asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None,
    ) -> "JobDefinition":
        check.invariant(
            not (op_selection and (asset_selection or asset_check_selection)),
            "op_selection cannot be provided with asset_selection or asset_check_selection to"
            " execute_in_process",
        )
        if op_selection:
            return self._get_job_def_for_op_selection(op_selection)
        if asset_selection or asset_check_selection:
            return self._get_job_def_for_asset_selection(
                AssetSelectionData(
                    asset_selection=asset_selection,
                    asset_check_selection=asset_check_selection,
                    parent_job_def=self,
                )
            )
        else:
            return self

    def _get_job_def_for_asset_selection(
        self, selection_data: AssetSelectionData
    ) -> "JobDefinition":
        from dagster._core.definitions.assets_job import (
            build_assets_job,
            get_asset_graph_for_job,
        )

        # If a non-null check selection is provided, use that. Otherwise the selection will resolve
        # to all checks matching a selected asset by default.
        selection = AssetSelection.keys(*selection_data.asset_selection)
        if selection_data.asset_check_selection is not None:
            selection = selection.without_checks() | AssetSelection.checks(
                *selection_data.asset_check_selection
            )

        job_asset_graph = get_asset_graph_for_job(self.asset_layer.asset_graph, selection)

        return build_assets_job(
            name=self.name,
            asset_graph=job_asset_graph,
            executor_def=self.executor_def,
            resource_defs=self.resource_defs,
            description=self.description,
            tags=self.tags,
            config=self.config_mapping or self.partitioned_config,
            _asset_selection_data=selection_data,
        )

    def _get_job_def_for_op_selection(self, op_selection: Iterable[str]) -> "JobDefinition":
        try:
            sub_graph = get_graph_subset(self.graph, op_selection)

            # if explicit config was passed the config_mapping that resolves the defaults implicitly is
            # very unlikely to work. The job will still present the default config in the Dagster UI.
            config = (
                None
                if self.run_config is not None
                else self.config_mapping or self.partitioned_config
            )

            return self._copy(
                config=config,
                graph_def=sub_graph,
                _subset_selection_data=OpSelectionData(
                    op_selection=list(op_selection),
                    resolved_op_selection=OpSelection(op_selection).resolve(self.graph),
                    parent_job_def=self,  # used by job snapshot lineage
                ),
                # TODO: subset this structure.
                # https://github.com/dagster-io/dagster/issues/7541
                asset_layer=self.asset_layer,
            )
        except DagsterInvalidDefinitionError as exc:
            # This handles the case when you construct a subset such that an unsatisfied
            # input cannot be loaded from config. Instead of throwing a DagsterInvalidDefinitionError,
            # we re-raise a DagsterInvalidSubsetError.
            node_paths = OpSelection(op_selection).resolve(self.graph)
            raise DagsterInvalidSubsetError(
                f"The attempted subset {str_format_set(node_paths)} for graph "
                f"{self.graph.name} results in an invalid graph."
            ) from exc

    @public
    @deprecated(
        breaking_version="2.0.0",
        additional_warn_text="Directly instantiate `RunRequest(partition_key=...)` instead.",
    )
    def run_request_for_partition(
        self,
        partition_key: str,
        run_key: Optional[str] = None,
        tags: Optional[Mapping[str, str]] = None,
        asset_selection: Optional[Sequence[AssetKey]] = None,
        run_config: Optional[Mapping[str, Any]] = None,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> RunRequest:
        """Creates a RunRequest object for a run that processes the given partition.

        Args:
            partition_key: The key of the partition to request a run for.
            run_key (Optional[str]): A string key to identify this launched run. For sensors, ensures that
                only one run is created per run key across all sensor evaluations.  For schedules,
                ensures that one run is created per tick, across failure recoveries. Passing in a `None`
                value means that a run will always be launched per evaluation.
            tags (Optional[Dict[str, str]]): A dictionary of tags (string key-value pairs) to attach
                to the launched run.
            run_config (Optional[Mapping[str, Any]]: Configuration for the run. If the job has
                a :py:class:`PartitionedConfig`, this value will override replace the config
                provided by it.
            current_time (Optional[datetime]): Used to determine which time-partitions exist.
                Defaults to now.
            dynamic_partitions_store (Optional[DynamicPartitionsStore]): The DynamicPartitionsStore
                object that is responsible for fetching dynamic partitions. Required when the
                partitions definition is a DynamicPartitionsDefinition with a name defined. Users
                can pass the DagsterInstance fetched via `context.instance` to this argument.


        Returns:
            RunRequest: an object that requests a run to process the given partition.
        """
        if not (self.partitions_def and self.partitioned_config):
            check.failed("Called run_request_for_partition on a non-partitioned job")

        if (
            isinstance(self.partitions_def, DynamicPartitionsDefinition)
            and self.partitions_def.name
        ):
            # Do not support using run_request_for_partition with dynamic partitions,
            # since this requires querying the instance once per run request for the
            # existent dynamic partitions
            check.failed(
                "run_request_for_partition is not supported for dynamic partitions. Instead, use"
                " RunRequest(partition_key=...)"
            )

        self.partitions_def.validate_partition_key(
            partition_key,
            current_time=current_time,
            dynamic_partitions_store=dynamic_partitions_store,
        )

        run_config = (
            run_config
            if run_config is not None
            else self.partitioned_config.get_run_config_for_partition_key(partition_key)
        )
        run_request_tags = {
            **(tags or {}),
            **self.partitioned_config.get_tags_for_partition_key(
                partition_key,
                job_name=self.name,
            ),
        }

        return RunRequest(
            run_key=run_key,
            run_config=run_config,
            tags=run_request_tags,
            job_name=self.name,
            asset_selection=asset_selection,
            partition_key=partition_key,
        )

    def get_config_schema_snapshot(self) -> "ConfigSchemaSnapshot":
        return self.get_job_snapshot().config_schema_snapshot

    def get_job_snapshot(self) -> "JobSnapshot":
        return self.get_job_index().job_snapshot

    def get_job_index(self) -> "JobIndex":
        from dagster._core.remote_representation import JobIndex
        from dagster._core.snap import JobSnapshot

        return JobIndex(JobSnapshot.from_job_def(self), self.get_parent_job_snapshot())

    def get_job_snapshot_id(self) -> str:
        return self.get_job_index().job_snapshot_id

    def get_parent_job_snapshot(self) -> Optional["JobSnapshot"]:
        if self.op_selection_data:
            return self.op_selection_data.parent_job_def.get_job_snapshot()
        elif self.asset_selection_data:
            return self.asset_selection_data.parent_job_def.get_job_snapshot()
        else:
            return None

    def has_direct_input_value(self, input_name: str) -> bool:
        return input_name in self.input_values

    def get_direct_input_value(self, input_name: str) -> object:
        if input_name not in self.input_values:
            raise DagsterInvalidInvocationError(
                f"On job '{self.name}', attempted to retrieve input value for input named"
                f" '{input_name}', but no value was provided. Provided input values:"
                f" {sorted(list(self.input_values.keys()))}"
            )
        return self.input_values[input_name]

    def _copy(self, **kwargs: Any) -> "JobDefinition":
        # dict() calls copy dict props
        base_kwargs = dict(
            graph_def=self.graph,
            resource_defs=dict(self.resource_defs),
            executor_def=self._executor_def,
            logger_defs=self._loggers,
            config=self._original_config_argument,
            name=self._name,
            description=self.description,
            tags=self.tags,
            metadata=self._metadata,
            hook_defs=self.hook_defs,
            op_retry_policy=self._op_retry_policy,
            version_strategy=self.version_strategy,
            _subset_selection_data=self._subset_selection_data,
            asset_layer=self.asset_layer,
            input_values=self.input_values,
            partitions_def=self.partitions_def,
            _was_explicitly_provided_resources=None,
        )
        resolved_kwargs = {**base_kwargs, **kwargs}  # base kwargs overwritten for conflicts
        job_def = JobDefinition.dagster_internal_init(**resolved_kwargs)
        update_wrapper(job_def, self, updated=())
        return job_def

    @public
    def with_top_level_resources(
        self, resource_defs: Mapping[str, ResourceDefinition]
    ) -> "JobDefinition":
        """Apply a set of resources to all op instances within the job."""
        resource_defs = check.mapping_param(resource_defs, "resource_defs", key_type=str)
        return self._copy(resource_defs=resource_defs)

    @public
    def with_hooks(self, hook_defs: AbstractSet[HookDefinition]) -> "JobDefinition":
        """Apply a set of hooks to all op instances within the job."""
        hook_defs = check.set_param(hook_defs, "hook_defs", of_type=HookDefinition)
        return self._copy(hook_defs=(hook_defs | self.hook_defs))

    def with_executor_def(self, executor_def: ExecutorDefinition) -> "JobDefinition":
        return self._copy(executor_def=executor_def)

    def with_logger_defs(self, logger_defs: Mapping[str, LoggerDefinition]) -> "JobDefinition":
        return self._copy(logger_defs=logger_defs)

    @property
    def op_selection(self) -> Optional[AbstractSet[str]]:
        return set(self.op_selection_data.op_selection) if self.op_selection_data else None

    @property
    def asset_selection(self) -> Optional[AbstractSet[AssetKey]]:
        return self.asset_selection_data.asset_selection if self.asset_selection_data else None

    @property
    def asset_check_selection(self) -> Optional[AbstractSet[AssetCheckKey]]:
        return (
            self.asset_selection_data.asset_check_selection if self.asset_selection_data else None
        )

    @property
    def resolved_op_selection(self) -> Optional[AbstractSet[str]]:
        return self.op_selection_data.resolved_op_selection if self.op_selection_data else None


def _swap_default_io_man(resources: Mapping[str, ResourceDefinition], job: JobDefinition):
    """Used to create the user facing experience of the default io_manager
    switching to in-memory when using execute_in_process.
    """
    from dagster._core.storage.mem_io_manager import mem_io_manager

    if (
        resources.get(DEFAULT_IO_MANAGER_KEY) in [default_job_io_manager]
        and job.version_strategy is None
    ):
        updated_resources = dict(resources)
        updated_resources[DEFAULT_IO_MANAGER_KEY] = mem_io_manager
        return updated_resources

    return resources


@dagster_maintained_io_manager
@io_manager(
    description="Built-in filesystem IO manager that stores and retrieves values using pickling."
)
def default_job_io_manager(init_context: "InitResourceContext"):
    # support overriding the default io manager via environment variables
    module_name = os.getenv("DAGSTER_DEFAULT_IO_MANAGER_MODULE")
    attribute_name = os.getenv("DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE")
    silence_failures = os.getenv("DAGSTER_DEFAULT_IO_MANAGER_SILENCE_FAILURES")

    if module_name and attribute_name:
        from dagster._core.execution.build_resources import build_resources

        try:
            module = importlib.import_module(module_name)
            attr = getattr(module, attribute_name)
            check.invariant(
                isinstance(attr, IOManagerDefinition),
                "DAGSTER_DEFAULT_IO_MANAGER_MODULE and DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE"
                " must specify an IOManagerDefinition",
            )
            with build_resources({"io_manager": attr}, instance=init_context.instance) as resources:
                return resources.io_manager
        except Exception as e:
            if not silence_failures:
                raise
            else:
                warnings.warn(
                    f"Failed to load io manager override with module: {module_name} attribute:"
                    f" {attribute_name}: {e}\nFalling back to default io manager."
                )

    # normally, default to the fs_io_manager
    from dagster._core.storage.fs_io_manager import PickledObjectFilesystemIOManager

    instance = check.not_none(init_context.instance)
    return PickledObjectFilesystemIOManager(base_dir=instance.storage_directory())


@dagster_maintained_io_manager
@io_manager(
    description="Built-in filesystem IO manager that stores and retrieves values using pickling.",
    config_schema={"base_dir": Field(StringSource, is_required=False)},
)
def default_job_io_manager_with_fs_io_manager_schema(init_context: "InitResourceContext"):
    # support overriding the default io manager via environment variables
    module_name = os.getenv("DAGSTER_DEFAULT_IO_MANAGER_MODULE")
    attribute_name = os.getenv("DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE")
    silence_failures = os.getenv("DAGSTER_DEFAULT_IO_MANAGER_SILENCE_FAILURES")

    if module_name and attribute_name:
        from dagster._core.execution.build_resources import build_resources

        try:
            module = importlib.import_module(module_name)
            attr = getattr(module, attribute_name)
            check.invariant(
                isinstance(attr, IOManagerDefinition),
                "DAGSTER_DEFAULT_IO_MANAGER_MODULE and DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE"
                " must specify an IOManagerDefinition",
            )
            with build_resources({"io_manager": attr}, instance=init_context.instance) as resources:
                return resources.io_manager
        except Exception as e:
            if not silence_failures:
                raise
            else:
                warnings.warn(
                    f"Failed to load io manager override with module: {module_name} attribute:"
                    f" {attribute_name}: {e}\nFalling back to default io manager."
                )
    from dagster._core.storage.fs_io_manager import PickledObjectFilesystemIOManager

    # normally, default to the fs_io_manager
    base_dir = init_context.resource_config.get(
        "base_dir", init_context.instance.storage_directory() if init_context.instance else None
    )

    return PickledObjectFilesystemIOManager(base_dir=base_dir)


def _config_mapping_with_default_value(
    inner_schema: ConfigType,
    default_config: Mapping[str, Any],
    job_name: str,
) -> ConfigMapping:
    if not isinstance(inner_schema, Shape):
        check.failed("Only Shape (dictionary) config_schema allowed on Job ConfigMapping")

    def config_fn(x):
        return x

    updated_fields = {}
    field_aliases = inner_schema.field_aliases
    for name, field in inner_schema.fields.items():
        if name in default_config:
            updated_fields[name] = Field(
                config=field.config_type,
                default_value=default_config[name],
                description=field.description,
            )
        elif name in field_aliases and field_aliases[name] in default_config:
            updated_fields[name] = Field(
                config=field.config_type,
                default_value=default_config[field_aliases[name]],
                description=field.description,
            )
        else:
            updated_fields[name] = field

    config_schema = Shape(
        fields=updated_fields,
        description=(
            "This run config schema was automatically populated with default values "
            "from `default_config`."
        ),
        field_aliases=inner_schema.field_aliases,
    )

    config_evr = validate_config(config_schema, default_config)
    if not config_evr.success:
        raise DagsterInvalidConfigError(
            f"Error in config when building job '{job_name}' ",
            config_evr.errors,
            default_config,
        )

    return ConfigMapping(
        config_fn=config_fn, config_schema=config_schema, receive_processed_config_values=False
    )


def get_run_config_schema_for_job(
    graph_def: GraphDefinition,
    resource_defs: Mapping[str, ResourceDefinition],
    executor_def: "ExecutorDefinition",
    logger_defs: Mapping[str, LoggerDefinition],
    asset_layer: Optional[AssetLayer],
    was_explicitly_provided_resources: bool = False,
) -> ConfigType:
    return JobDefinition(
        name=graph_def.name,
        graph_def=graph_def,
        resource_defs=resource_defs,
        executor_def=executor_def,
        logger_defs=logger_defs,
        asset_layer=asset_layer,
        _was_explicitly_provided_resources=was_explicitly_provided_resources,
    ).run_config_schema.run_config_schema_type


def _infer_asset_layer_from_source_asset_deps(job_graph_def: GraphDefinition) -> AssetLayer:
    """For non-asset jobs that have some inputs that are fed from SourceAssets, constructs an
    AssetLayer that includes those SourceAssets.
    """
    from dagster._core.definitions.asset_graph import (
        AssetGraph,
    )

    asset_keys_by_node_input_handle: Dict[NodeInputHandle, AssetKey] = {}
    source_assets_list = []
    source_asset_keys_set = set()

    # each entry is a graph definition and its handle relative to the job root
    stack: List[Tuple[GraphDefinition, Optional[NodeHandle]]] = [(job_graph_def, None)]

    while stack:
        graph_def, parent_node_handle = stack.pop()

        for node_name, input_source_assets in graph_def.node_input_source_assets.items():
            node_handle = NodeHandle(node_name, parent_node_handle)
            for input_name, source_asset in input_source_assets.items():
                if source_asset.key not in source_asset_keys_set:
                    source_asset_keys_set.add(source_asset.key)
                    source_assets_list.append(source_asset)

                input_handle = NodeInputHandle(node_handle, input_name)
                asset_keys_by_node_input_handle[input_handle] = source_asset.key
                for resolved_input_handle in graph_def.node_dict[
                    node_name
                ].definition.resolve_input_to_destinations(input_handle):
                    asset_keys_by_node_input_handle[resolved_input_handle] = source_asset.key

        for node_name, node in graph_def.node_dict.items():
            if isinstance(node.definition, GraphDefinition):
                stack.append((node.definition, NodeHandle(node_name, parent_node_handle)))

    return AssetLayer(
        asset_graph=AssetGraph.from_assets(source_assets_list),
        assets_defs_by_node_handle={},
        asset_keys_by_node_input_handle=asset_keys_by_node_input_handle,
        asset_info_by_node_output_handle={},
        asset_deps={},
        dependency_node_handles_by_asset_key={},
        dep_asset_keys_by_node_output_handle={},
        partition_mappings_by_asset_dep={},
        node_output_handles_by_asset_check_key={},
        check_names_by_asset_key_by_node_handle={},
        check_key_by_node_output_handle={},
        assets_defs_by_check_key={},
    )


def _build_all_node_defs(node_defs: Sequence[NodeDefinition]) -> Mapping[str, NodeDefinition]:
    all_defs: Dict[str, NodeDefinition] = {}
    for current_level_node_def in node_defs:
        for node_def in current_level_node_def.iterate_node_defs():
            if node_def.name in all_defs:
                if all_defs[node_def.name] != node_def:
                    raise DagsterInvalidDefinitionError(
                        'Detected conflicting node definitions with the same name "{name}"'.format(
                            name=node_def.name
                        )
                    )
            else:
                all_defs[node_def.name] = node_def

    return all_defs


def _create_run_config_schema(
    job_def: JobDefinition,
    required_resources: AbstractSet[str],
) -> "RunConfigSchema":
    from .run_config import (
        RunConfigSchemaCreationData,
        construct_config_type_dictionary,
        define_run_config_schema_type,
    )
    from .run_config_schema import RunConfigSchema

    # When executing with a subset job, include the missing nodes
    # from the original job as ignored to allow execution with
    # run config that is valid for the original
    ignored_nodes: Sequence[Node] = []
    if job_def.is_subset:
        if isinstance(job_def.graph, SubselectedGraphDefinition):  # op selection provided
            ignored_nodes = job_def.graph.get_top_level_omitted_nodes()
        elif job_def.asset_selection_data:
            parent_job = job_def
            while parent_job.asset_selection_data:
                parent_job = parent_job.asset_selection_data.parent_job_def

            ignored_nodes = [
                node for node in parent_job.graph.nodes if not job_def.has_node_named(node.name)
            ]
    else:
        ignored_nodes = []

    run_config_schema_type = define_run_config_schema_type(
        RunConfigSchemaCreationData(
            job_name=job_def.name,
            nodes=job_def.graph.nodes,
            graph_def=job_def.graph,
            dependency_structure=job_def.graph.dependency_structure,
            executor_def=job_def.executor_def,
            resource_defs=job_def.resource_defs,
            logger_defs=job_def.loggers,
            ignored_nodes=ignored_nodes,
            required_resources=required_resources,
            direct_inputs=job_def.input_values,
            asset_layer=job_def.asset_layer,
        )
    )

    if job_def.config_mapping:
        outer_config_type = job_def.config_mapping.config_schema.config_type
    else:
        outer_config_type = run_config_schema_type

    if outer_config_type is None:
        check.failed("Unexpected outer_config_type value of None")

    config_type_dict_by_name, config_type_dict_by_key = construct_config_type_dictionary(
        job_def.all_node_defs,
        outer_config_type,
    )

    return RunConfigSchema(
        run_config_schema_type=run_config_schema_type,
        config_type_dict_by_name=config_type_dict_by_name,
        config_type_dict_by_key=config_type_dict_by_key,
        config_mapping=job_def.config_mapping,
    )
