import importlib
import os
import warnings
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from functools import cached_property, update_wrapper
from typing import TYPE_CHECKING, AbstractSet, Any, Optional, Union, cast  # noqa: UP035

import dagster._check as check
from dagster._annotations import deprecated, public
from dagster._config import Field, Shape, StringSource
from dagster._config.config_type import ConfigType
from dagster._config.validate import validate_config
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.job.asset_layer import AssetLayer
from dagster._core.definitions.backfill_policy import BackfillPolicy, resolve_backfill_policy
from dagster._core.definitions.config import ConfigMapping
from dagster._core.definitions.dependency import (
    DependencyMapping,
    DependencyStructure,
    Node,
    NodeHandle,
    NodeInputHandle,
    NodeInvocation,
    OpNode,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.executor_definition import (
    ExecutorDefinition,
    multi_or_in_process_executor,
)
from dagster._core.definitions.graph_definition import GraphDefinition, SubselectedGraphDefinition
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.metadata import MetadataValue, RawMetadataValue, normalize_metadata
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.op_selection import OpSelection, get_graph_subset
from dagster._core.definitions.partitions.context import (
    PartitionLoadingContext,
    partition_loading_context,
)
from dagster._core.definitions.partitions.definition import (
    DynamicPartitionsDefinition,
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.partitioned_config import PartitionedConfig
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.resource_requirement import (
    ResourceKeyRequirement,
    ResourceRequirement,
    ensure_requirements_satisfied,
)
from dagster._core.definitions.utils import DEFAULT_IO_MANAGER_KEY, check_valid_name
from dagster._core.errors import (
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvalidSubsetError,
    DagsterInvariantViolationError,
)
from dagster._core.selector.subset_selector import AssetSelectionData, OpSelectionData
from dagster._core.storage.io_manager import (
    IOManagerDefinition,
    dagster_maintained_io_manager,
    io_manager,
)
from dagster._core.types.dagster_type import DagsterType
from dagster._core.utils import str_format_set
from dagster._utils import IHasInternalInit
from dagster._utils.cached_method import cached_method
from dagster._utils.merger import merge_dicts
from dagster._utils.tags import normalize_tags

if TYPE_CHECKING:
    from dagster._config.snap import ConfigSchemaSnapshot
    from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
    from dagster._core.definitions.run_config import RunConfig
    from dagster._core.definitions.run_config_schema import RunConfigSchema
    from dagster._core.definitions.run_request import RunRequest
    from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
    from dagster._core.execution.resources_init import InitResourceContext
    from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
    from dagster._core.remote_representation.job_index import JobIndex
    from dagster._core.snap import JobSnap

DEFAULT_EXECUTOR_DEF = multi_or_in_process_executor


@public
class JobDefinition(IHasInternalInit):
    """Defines a Dagster job."""

    _name: str
    _graph_def: GraphDefinition
    _description: Optional[str]
    _tags: Mapping[str, str]
    _run_tags: Optional[Mapping[str, str]]
    _metadata: Mapping[str, MetadataValue]
    _current_level_node_defs: Sequence[NodeDefinition]
    _hook_defs: AbstractSet[HookDefinition]
    _op_retry_policy: Optional[RetryPolicy]
    _asset_layer: AssetLayer
    _resource_requirements: Mapping[str, AbstractSet[str]]
    _all_node_defs: Mapping[str, NodeDefinition]
    _cached_run_config_schemas: dict[str, "RunConfigSchema"]
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
        run_tags: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        op_retry_policy: Optional[RetryPolicy] = None,
        _subset_selection_data: Optional[Union[OpSelectionData, AssetSelectionData]] = None,
        asset_layer: Optional[AssetLayer] = None,
        input_values: Optional[Mapping[str, object]] = None,
        _was_explicitly_provided_resources: Optional[bool] = None,
    ):
        from dagster._core.definitions.run_config import RunConfig, convert_config_input

        self._graph_def = graph_def
        self._current_level_node_defs = self._graph_def.node_defs
        # Recursively explore all nodes in this job
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

        self._original_partitions_def_argument = check.opt_inst_param(
            partitions_def, "partitions_def", PartitionsDefinition
        )
        # tags and description can exist on graph as well, but since
        # same graph may be in multiple jobs, keep separate layer
        self._description = check.opt_str_param(description, "description")

        self._tags = normalize_tags(tags)
        self._run_tags = run_tags  # don't normalize to preserve None

        self._metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str)
        )
        self._hook_defs = check.opt_set_param(hook_defs, "hook_defs")
        self._op_retry_policy = check.opt_inst_param(
            op_retry_policy, "op_retry_policy", RetryPolicy
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
        self._was_provided_resources = (
            bool(resource_defs)
            if _was_explicitly_provided_resources is None
            else _was_explicitly_provided_resources
        )
        self._resource_defs = {
            DEFAULT_IO_MANAGER_KEY: default_job_io_manager,
            **resource_defs,
        }
        self._required_resource_keys = self._get_required_resource_keys(
            self._was_provided_resources
        )

        self._config_mapping = None
        self._partitioned_config = None
        self._run_config = None
        self._run_config_schema = None
        self._original_config_argument = config

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
        run_tags: Optional[Mapping[str, Any]],
        metadata: Optional[Mapping[str, RawMetadataValue]],
        hook_defs: Optional[AbstractSet[HookDefinition]],
        op_retry_policy: Optional[RetryPolicy],
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
            run_tags=run_tags,
            metadata=metadata,
            hook_defs=hook_defs,
            op_retry_policy=op_retry_policy,
            _subset_selection_data=_subset_selection_data,
            asset_layer=asset_layer,
            input_values=input_values,
            _was_explicitly_provided_resources=_was_explicitly_provided_resources,
        )

    @staticmethod
    def for_external_job(
        asset_keys: Iterable[AssetKey],
        name: str,
        metadata: Optional[Mapping[str, Any]] = None,
        tags: Optional[Mapping[str, Any]] = None,
    ) -> "JobDefinition":
        from dagster._core.definitions import op

        # We need to create a dummy op in order for the asset graph to be rendered in the UI. It's worth investigating whether
        # we can avoid this.

        @op(name=f"{name}_op_inner")
        def _op():
            pass

        return JobDefinition(
            graph_def=GraphDefinition(name=name, node_defs=[_op]),
            resource_defs={},
            executor_def=None,
            asset_layer=AssetLayer.for_external_job(asset_keys),
            metadata=metadata,
            tags=tags,
        )

    @property
    def name(self) -> str:
        return self._name

    # If `run_tags` is set (not None), then `tags` and `run_tags` are separate specifications of
    # "definition" and "run" tags respectively. Otherwise, `tags` is used for both.
    # This is for backcompat with old behavior prior to the introduction of `run_tags`.
    #
    # We need to preserve the distinction between None and {} values for `run_tags` so that the
    # same logic can be applied in the host process receiving a snapshot of this job. Therefore
    # we store an extra flag `_has_separately_defined_run_tags` which we use to control snapshot
    # generation.
    @cached_property
    def tags(self) -> Mapping[str, str]:
        if self._run_tags is None:
            return {**self._graph_def.tags, **self._tags}
        else:
            return self._tags

    @cached_property
    def run_tags(self) -> Mapping[str, str]:
        if self._run_tags is None:
            return self.tags
        else:
            return normalize_tags({**self._graph_def.tags, **self._run_tags})

    # This property exists for backcompat purposes. If it is False, then we omit run_tags when
    # generating a job snapshot. This lets host processes distinguish between None and {} `run_tags`
    # values, which have different semantics:
    #
    # - run_tags=None (`tags` will be used for run tags)
    # - run_tags={} (empty dict will be used for run tags), which have different semantics.
    @property
    def has_separately_defined_run_tags(self) -> bool:
        return self._run_tags is not None

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
        if self.has_unresolved_configs:
            self._resolve_configs()
        return self._partitioned_config

    @public
    @property
    def config_mapping(self) -> Optional[ConfigMapping]:
        """The config mapping for the job, if it has one.

        A config mapping defines a way to map a top-level config schema to run config for the job.
        """
        if self.has_unresolved_configs:
            self._resolve_configs()
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
        if self.has_unresolved_configs:
            self._resolve_configs()
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

    @cached_property
    def backfill_policy(self) -> BackfillPolicy:
        executable_nodes = {self.asset_layer.get(k) for k in self.asset_layer.executable_asset_keys}
        backfill_policies = {n.backfill_policy for n in executable_nodes if n.is_partitioned}

        # normalize null backfill policy to explicit multi_run(1) policy
        return resolve_backfill_policy(backfill_policies)

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

    @property
    def op_retry_policy(self) -> Optional[RetryPolicy]:
        return self._op_retry_policy

    @property
    def has_unresolved_configs(self) -> bool:
        return (
            self._partitioned_config is None
            and self._run_config is None
            and self._config_mapping is None
        )

    @cached_method
    def _resolve_configs(self) -> None:
        config = self._original_config_argument
        partition_def = self._original_partitions_def_argument
        if partition_def:
            self._partitioned_config = PartitionedConfig.from_flexible_config(config, partition_def)
        else:
            if isinstance(config, ConfigMapping):
                self._config_mapping = config
            elif isinstance(config, PartitionedConfig):
                self._partitioned_config = config
                if self.asset_layer:
                    for asset_key in self._asset_layer.selected_asset_keys:
                        asset_partitions_def = self._asset_layer.get(asset_key).partitions_def
                        check.invariant(
                            asset_partitions_def is None
                            or asset_partitions_def == config.partitions_def,
                            "Can't supply a PartitionedConfig for 'config' with a different PartitionsDefinition"
                            f" than supplied for a target asset 'partitions_def'. Asset: {asset_key.to_user_string()}",
                        )

            elif isinstance(config, dict):
                self._run_config = config
                # Using config mapping here is a trick to make it so that the preset will be used even
                # when no config is supplied for the job.
                self._config_mapping = _config_mapping_with_default_value(
                    get_run_config_schema_for_job(
                        self._graph_def,
                        self.resource_defs,
                        self.executor_def,
                        self.loggers,
                        self._asset_layer,
                        was_explicitly_provided_resources=self._was_provided_resources,
                    ),
                    config,
                    self.name,
                )
            elif config is not None:
                check.failed(
                    "config param must be a ConfigMapping, a PartitionedConfig, or a dictionary,"
                    f" but is an object of type {type(config)}"
                )

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
        assert isinstance(node, OpNode), (
            f"Tried to retrieve node {handle} as op, but it represents a nested graph."
        )
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

    def get_required_resource_defs(self) -> Mapping[str, ResourceDefinition]:
        return {
            resource_key: resource
            for resource_key, resource in self.resource_defs.items()
            if resource_key in self.required_resource_keys
        }

    def _get_required_resource_keys(self, validate_requirements: bool = False) -> AbstractSet[str]:
        from dagster._core.execution.resources_init import get_transitive_required_resource_keys

        requirements = self._get_resource_requirements()
        if validate_requirements:
            ensure_requirements_satisfied(self.resource_defs, requirements)
        required_keys = {req.key for req in requirements if isinstance(req, ResourceKeyRequirement)}
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
                for req in hook_def.get_resource_requirements(attached_to=f"job '{self._name}'")
            ],
            *[
                req
                for assets_def in self.asset_layer.asset_graph.assets_defs
                for hook_def in assets_def.hook_defs
                for req in hook_def.get_resource_requirements(
                    attached_to=f"asset '{assets_def.node_def.name}'"
                )
            ],
        ]

    def validate_resource_requirements_satisfied(self) -> None:
        resource_requirements = self._get_resource_requirements()
        ensure_requirements_satisfied(self.resource_defs, resource_requirements)

    def is_missing_required_resources(self) -> bool:
        requirements = self._get_resource_requirements()
        for requirement in requirements:
            if not requirement.is_satisfied(self.resource_defs):
                return True
        return False

    def get_all_hooks_for_handle(self, handle: NodeHandle) -> AbstractSet[HookDefinition]:
        """Gather all the hooks for the given node from all places possibly attached with a hook.

        A hook can be attached to any of the following objects
        * Node (node invocation)
        * AssetsDefinition
        * JobDefinition

        Args:
            handle (NodeHandle): The node's handle

        Returns:
            FrozenSet[HookDefinition]
        """
        check.inst_param(handle, "handle", NodeHandle)
        assets_def = self.asset_layer.get_assets_def_for_node(handle)
        hook_defs = set(assets_def.hook_defs) if assets_def else set()

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
            definition = cast("GraphDefinition", node.definition)
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
            run_config (Optional[Mapping[str, Any]]):
                The configuration for the run
            instance (Optional[DagsterInstance]):
                The instance to execute against, an ephemeral one will be used if none provided.
            partition_key (Optional[str]):
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
        from dagster._core.definitions.job_base import InMemoryJob
        from dagster._core.execution.execute_in_process import (
            core_execute_in_process,
            merge_run_tags,
            type_check_and_normalize_args,
        )

        run_config, op_selection, asset_selection, resource_defs, partition_key, input_values = (
            type_check_and_normalize_args(
                run_config=run_config,
                partition_key=partition_key,
                op_selection=op_selection,
                asset_selection=asset_selection,
                input_values=input_values,
                resources=resources,
            )
        )

        ephemeral_job = self.as_ephemeral_job(
            resource_defs=resource_defs,
            input_values=input_values,
            op_selection=op_selection,
            asset_selection=asset_selection,
        )
        if partition_key and ephemeral_job.partitions_def:
            with partition_loading_context(dynamic_partitions_store=instance) as ctx:
                ephemeral_job.validate_partition_key(
                    partition_key=partition_key,
                    selected_asset_keys=set(asset_selection),
                    context=ctx,
                )

        wrapped_job = InMemoryJob(job_def=ephemeral_job)

        if not run_config and ephemeral_job.partitioned_config and partition_key:
            run_config = ephemeral_job.partitioned_config.get_run_config_for_partition_key(
                partition_key
            )

        return core_execute_in_process(
            job=wrapped_job,
            run_config=run_config,
            instance=instance,
            output_capturing_enabled=True,
            raise_on_error=raise_on_error,
            run_tags=merge_run_tags(
                job_def=self,
                partition_key=partition_key,
                tags=tags,
                asset_selection=asset_selection,
                instance=instance,
                run_config=run_config,
            ),
            run_id=run_id,
            asset_selection=frozenset(asset_selection),
        )

    def as_ephemeral_job(
        self,
        resource_defs: Mapping[str, ResourceDefinition],
        input_values: Mapping[str, object],
        op_selection: Optional[Sequence[str]] = None,
        asset_selection: Optional[Sequence[AssetKey]] = None,
    ) -> "JobDefinition":
        from dagster._core.definitions.executor_definition import execute_in_process_executor

        bound_resource_defs = dict(self.resource_defs)
        return JobDefinition.dagster_internal_init(
            name=self._name,
            graph_def=self._graph_def,
            resource_defs={**_swap_default_io_man(bound_resource_defs, self), **resource_defs},
            executor_def=execute_in_process_executor,
            logger_defs=self._loggers,
            hook_defs=self.hook_defs,
            config=self.config_mapping or self.partitioned_config or self.run_config,
            tags=self.tags,
            run_tags=self._run_tags,
            op_retry_policy=self._op_retry_policy,
            asset_layer=self.asset_layer,
            input_values=merge_dicts(self.input_values, input_values),
            description=self.description,
            partitions_def=self.partitions_def,
            metadata=self.metadata,
            _subset_selection_data=None,  # this is added below
            _was_explicitly_provided_resources=True,
        ).get_subset(
            op_selection=op_selection,
            asset_selection=frozenset(asset_selection) if asset_selection else None,
        )

    def _get_partitions_def(
        self, selected_asset_keys: Optional[Iterable[AssetKey]]
    ) -> PartitionsDefinition:
        if self.partitions_def:
            return self.partitions_def
        elif self.asset_layer:
            if selected_asset_keys:
                resolved_selected_asset_keys = selected_asset_keys
            elif self.asset_selection:
                resolved_selected_asset_keys = self.asset_selection
            else:
                resolved_selected_asset_keys = self.asset_layer.selected_asset_keys

            unique_partitions_defs: set[PartitionsDefinition] = set()
            for asset_key in resolved_selected_asset_keys:
                partitions_def = self.asset_layer.get(asset_key).partitions_def
                if partitions_def is not None:
                    unique_partitions_defs.add(partitions_def)

            if len(unique_partitions_defs) == 1:
                return check.not_none(next(iter(unique_partitions_defs)))

        if selected_asset_keys is not None:
            check.failed("There is no PartitionsDefinition shared by all the provided assets")
        else:
            check.failed("Job has no PartitionsDefinition")

    def get_partition_keys(
        self, selected_asset_keys: Optional[Iterable[AssetKey]]
    ) -> Sequence[str]:
        partitions_def = self._get_partitions_def(selected_asset_keys)
        return partitions_def.get_partition_keys()

    def validate_partition_key(
        self,
        partition_key: str,
        selected_asset_keys: Optional[Iterable[AssetKey]],
        context: PartitionLoadingContext,
    ) -> None:
        """Ensures that the given partition_key is a member of the PartitionsDefinition
        corresponding to every asset in the selection.
        """
        partitions_def = self._get_partitions_def(selected_asset_keys)
        partitions_def.validate_partition_key(partition_key, context=context)

    def get_tags_for_partition_key(
        self, partition_key: str, selected_asset_keys: Optional[Iterable[AssetKey]]
    ) -> Mapping[str, str]:
        """Gets tags for the given partition key."""
        if self._partitioned_config is not None:
            return self._partitioned_config.get_tags_for_partition_key(partition_key, self.name)

        partitions_def = self._get_partitions_def(selected_asset_keys)
        return partitions_def.get_tags_for_partition_key(partition_key)

    def get_run_config_for_partition_key(self, partition_key: str) -> Mapping[str, Any]:
        if self._partitioned_config:
            return self._partitioned_config.get_run_config_for_partition_key(partition_key)
        else:
            return {}

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
                    asset_selection=asset_selection or set(),
                    asset_check_selection=asset_check_selection,
                    parent_job_def=self,
                )
            )
        else:
            return self

    def _get_job_def_for_asset_selection(
        self, selection_data: AssetSelectionData
    ) -> "JobDefinition":
        from dagster._core.definitions.assets.job.asset_job import (
            build_asset_job,
            get_asset_graph_for_job,
        )

        # If a non-null check selection is provided, use that. Otherwise the selection will resolve
        # to all checks matching a selected asset by default.
        selection = AssetSelection.assets(*selection_data.asset_selection)
        if selection_data.asset_check_selection is not None:
            selection = selection.without_checks() | AssetSelection.checks(
                *selection_data.asset_check_selection
            )

        job_asset_graph = get_asset_graph_for_job(
            self.asset_layer.asset_graph.source_asset_graph,
            selection,
            allow_different_partitions_defs=True,
        )

        return build_asset_job(
            name=self.name,
            asset_graph=job_asset_graph,
            executor_def=self.executor_def,
            resource_defs=self.resource_defs,
            description=self.description,
            tags=self.tags,
            config=self.config_mapping or self.partitioned_config,
            _asset_selection_data=selection_data,
            allow_different_partitions_defs=True,
        )

    def _get_job_def_for_op_selection(self, op_selection: Iterable[str]) -> "JobDefinition":
        try:
            sub_graph = get_graph_subset(self.graph, op_selection, selected_outputs_by_op_handle={})

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
    ) -> "RunRequest":
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
        from dagster._core.definitions.run_request import RunRequest

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

        with partition_loading_context(current_time, dynamic_partitions_store) as ctx:
            self.partitions_def.validate_partition_key(partition_key, context=ctx)

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

    def get_job_snapshot(self) -> "JobSnap":
        return self.get_job_index().job_snapshot

    @cached_method
    def get_job_index(self) -> "JobIndex":
        from dagster._core.remote_representation.job_index import JobIndex
        from dagster._core.snap import JobSnap

        return JobIndex(JobSnap.from_job_def(self), self.get_parent_job_snapshot())

    def get_job_snapshot_id(self) -> str:
        return self.get_job_index().job_snapshot_id

    def get_parent_job_snapshot(self) -> Optional["JobSnap"]:
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
            run_tags=self._run_tags,
            metadata=self._metadata,
            hook_defs=self.hook_defs,
            op_retry_policy=self._op_retry_policy,
            _subset_selection_data=self._subset_selection_data,
            asset_layer=self.asset_layer,
            input_values=self.input_values,
            partitions_def=self._original_partitions_def_argument,
            _was_explicitly_provided_resources=(
                "resource_defs" in kwargs or self._was_provided_resources
            ),
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

    def with_metadata(self, metadata: Mapping[str, RawMetadataValue]) -> "JobDefinition":
        return self._copy(metadata=normalize_metadata(metadata))

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

    if resources.get(DEFAULT_IO_MANAGER_KEY) in [default_job_io_manager]:
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
    """For non-asset jobs that have some inputs that are fed from assets, constructs an
    AssetLayer that includes these assets as loadables.
    """
    from dagster._core.definitions.assets.graph.asset_graph import AssetGraph

    keys_by_input_handle: dict[NodeInputHandle, AssetKey] = {}
    assets_defs_by_key: dict[AssetKey, AssetsDefinition] = {}

    # each entry is a graph definition and its handle relative to the job root
    stack: list[tuple[GraphDefinition, Optional[NodeHandle]]] = [(job_graph_def, None)]

    while stack:
        graph_def, parent_node_handle = stack.pop()

        # iterate through the input_assets mapping on the graph definition, which
        # maps from node name to the set of assets definitions associated with each
        # input of that node
        for node_name, input_assets in graph_def.input_assets.items():
            node_handle = NodeHandle(node_name, parent_node_handle)
            for input_name, assets_def in input_assets.items():
                key = assets_def.key
                assets_defs_by_key[key] = assets_def

                # we know what key is associated with the outer input handle, so we
                # store that in the mapping and then calculate which inner input handles
                # this outer input handle is connected to, storing those as well
                outer_input_handle = NodeInputHandle(node_handle=node_handle, input_name=input_name)
                keys_by_input_handle[outer_input_handle] = key
                inner_node_def = graph_def.node_dict[node_name].definition
                for inner_input_handle in inner_node_def.resolve_input_to_destinations(
                    outer_input_handle
                ):
                    keys_by_input_handle[inner_input_handle] = key

        # add all subgraphs to the stack
        for node_def in graph_def.node_defs:
            if isinstance(node_def, GraphDefinition):
                stack.append((node_def, NodeHandle(node_def.name, parent_node_handle)))

    return AssetLayer(
        asset_graph=AssetGraph.from_assets(list(assets_defs_by_key.values())),
        # the AssetsDefinitions we have do not have any NodeDefinition explicitly
        # associated with them (they are not part of the actual execution, they're
        # just markers), so we don't pass them in through the data field and instead
        # pass this mapping information directly
        data=[],
        mapped_source_asset_keys_by_input_handle=keys_by_input_handle,
    )


def _build_all_node_defs(node_defs: Sequence[NodeDefinition]) -> Mapping[str, NodeDefinition]:
    all_defs: dict[str, NodeDefinition] = {}
    for current_level_node_def in node_defs:
        for node_def in current_level_node_def.iterate_node_defs():
            if node_def.name in all_defs:
                if all_defs[node_def.name] != node_def:
                    raise DagsterInvalidDefinitionError(
                        f'Detected conflicting node definitions with the same name "{node_def.name}"'
                    )
            else:
                all_defs[node_def.name] = node_def

    return all_defs


def _create_run_config_schema(
    job_def: JobDefinition,
    required_resources: AbstractSet[str],
) -> "RunConfigSchema":
    from dagster._core.definitions.run_config import (
        RunConfigSchemaCreationData,
        construct_config_type_dictionary,
        define_run_config_schema_type,
    )
    from dagster._core.definitions.run_config_schema import RunConfigSchema

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
