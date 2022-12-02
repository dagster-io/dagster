import importlib
import os
import warnings
from functools import update_wrapper
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

import dagster._check as check
from dagster._annotations import public
from dagster._config import Field, Shape, StringSource
from dagster._config.config_type import ConfigType
from dagster._config.validate import validate_config
from dagster._core.definitions.composition import MappedInputPlaceholder
from dagster._core.definitions.dependency import (
    DependencyDefinition,
    DynamicCollectDependencyDefinition,
    IDependencyDefinition,
    MultiDependencyDefinition,
    Node,
    NodeHandle,
    NodeInvocation,
    NodeOutput,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.utils import check_valid_name
from dagster._core.errors import (
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvalidSubsetError,
)
from dagster._core.selector.subset_selector import (
    AssetSelectionData,
    LeafNodeSelection,
    OpSelectionData,
    parse_op_selection,
)
from dagster._core.storage.io_manager import IOManagerDefinition, io_manager
from dagster._core.utils import str_format_set
from dagster._utils import merge_dicts

from .asset_layer import AssetLayer, build_asset_selection_job
from .config import ConfigMapping
from .dependency import DependencyDefinition
from .executor_definition import ExecutorDefinition, multi_or_in_process_executor
from .graph_definition import GraphDefinition, SubselectedGraphDefinition
from .hook_definition import HookDefinition
from .logger_definition import LoggerDefinition
from .metadata import MetadataEntry, PartitionMetadataEntry, RawMetadataValue
from .mode import ModeDefinition
from .partition import PartitionSetDefinition, PartitionedConfig, PartitionsDefinition
from .pipeline_definition import PipelineDefinition
from .preset import PresetDefinition
from .resource_definition import ResourceDefinition
from .run_request import RunRequest
from .utils import DEFAULT_IO_MANAGER_KEY
from .version_strategy import VersionStrategy

if TYPE_CHECKING:
    from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
    from dagster._core.execution.resources_init import InitResourceContext
    from dagster._core.instance import DagsterInstance
    from dagster._core.snap import PipelineSnapshot


class JobDefinition(PipelineDefinition):

    _cached_partition_set: Optional["PartitionSetDefinition"]
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
        config: Optional[Union[ConfigMapping, Mapping[str, object], PartitionedConfig]] = None,
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
        _metadata_entries: Optional[Sequence[Union[MetadataEntry, PartitionMetadataEntry]]] = None,
        _executor_def_specified: Optional[bool] = None,
        _logger_defs_specified: Optional[bool] = None,
        _preset_defs: Optional[Sequence[PresetDefinition]] = None,
    ):
        from dagster._loggers import default_loggers

        check.inst_param(graph_def, "graph_def", GraphDefinition)
        resource_defs = check.opt_mapping_param(
            resource_defs, "resource_defs", key_type=str, value_type=ResourceDefinition
        )
        # We need to check whether an actual executor/logger def was passed in
        # before we set a default executor/logger defs. This is so we can
        # determine if someone passed in the default executor vs the system set
        # it directly. Once JobDefinition no longer subclasses
        # PipelineDefinition, we can change the default executor to be set
        # elsewhere to avoid the need for this check.
        self._executor_def_specified = (
            _executor_def_specified
            if _executor_def_specified is not None
            else executor_def is not None
        )
        self._logger_defs_specified = (
            _logger_defs_specified
            if _logger_defs_specified is not None
            else logger_defs is not None
        )
        executor_def = check.opt_inst_param(
            executor_def, "executor_def", ExecutorDefinition, default=multi_or_in_process_executor
        )
        check.opt_mapping_param(
            logger_defs,
            "logger_defs",
            key_type=str,
            value_type=LoggerDefinition,
        )
        logger_defs = logger_defs or default_loggers()
        name = check_valid_name(check.opt_str_param(name, "name", default=graph_def.name))

        config = check.opt_inst_param(config, "config", (Mapping, ConfigMapping, PartitionedConfig))
        description = check.opt_str_param(description, "description")
        partitions_def = check.opt_inst_param(
            partitions_def, "partitions_def", PartitionsDefinition
        )
        tags = check.opt_mapping_param(tags, "tags", key_type=str)
        metadata = check.opt_mapping_param(metadata, "metadata", key_type=str)
        hook_defs = check.opt_set_param(hook_defs, "hook_defs")
        op_retry_policy = check.opt_inst_param(op_retry_policy, "op_retry_policy", RetryPolicy)
        version_strategy = check.opt_inst_param(
            version_strategy, "version_strategy", VersionStrategy
        )
        _subset_selection_data = check.opt_inst_param(
            _subset_selection_data, "_subset_selection_data", (OpSelectionData, AssetSelectionData)
        )
        asset_layer = check.opt_inst_param(asset_layer, "asset_layer", AssetLayer)
        input_values = check.opt_mapping_param(input_values, "input_values", key_type=str)
        _metadata_entries = check.opt_sequence_param(_metadata_entries, "_metadata_entries")
        _preset_defs = check.opt_sequence_param(
            _preset_defs, "preset_defs", of_type=PresetDefinition
        )

        if resource_defs and DEFAULT_IO_MANAGER_KEY in resource_defs:
            resource_defs_with_defaults = resource_defs
        else:
            resource_defs_with_defaults = merge_dicts(
                {DEFAULT_IO_MANAGER_KEY: default_job_io_manager}, resource_defs or {}
            )

        presets = []
        config_mapping = None
        partitioned_config = None
        self._explicit_config = False

        if partitions_def:
            partitioned_config = PartitionedConfig.from_flexible_config(config, partitions_def)
        else:
            if isinstance(config, ConfigMapping):
                config_mapping = config
            elif isinstance(config, PartitionedConfig):
                partitioned_config = config
            elif isinstance(config, dict):
                check.invariant(
                    len(_preset_defs) == 0,
                    "Bad state: attempted to pass preset definitions to job alongside config dictionary.",
                )
                presets = [PresetDefinition(name="default", run_config=config)]
                # Using config mapping here is a trick to make it so that the preset will be used even
                # when no config is supplied for the job.
                config_mapping = _config_mapping_with_default_value(
                    get_run_config_schema_for_job(
                        graph_def,
                        resource_defs_with_defaults,
                        executor_def,
                        logger_defs,
                        asset_layer,
                    ),
                    config,
                    name,
                )
                self._explicit_config = True
            elif config is not None:
                check.failed(
                    f"config param must be a ConfigMapping, a PartitionedConfig, or a dictionary, but "
                    f"is an object of type {type(config)}"
                )

        # Exists for backcompat - JobDefinition is implemented as a single-mode pipeline.
        mode_def = ModeDefinition(
            resource_defs=resource_defs_with_defaults,
            logger_defs=logger_defs,
            executor_defs=[executor_def] if executor_def else None,
            _config_mapping=config_mapping,
            _partitioned_config=partitioned_config,
        )

        self._cached_partition_set: Optional["PartitionSetDefinition"] = None
        self._subset_selection_data = _subset_selection_data
        self.input_values = input_values
        for input_name in sorted(list(self.input_values.keys())):
            if not graph_def.has_input(input_name):
                raise DagsterInvalidDefinitionError(
                    f"Error when constructing JobDefinition '{name}': Input value provided for key '{input_name}', but job has no top-level input with that name."
                )

        super(JobDefinition, self).__init__(
            name=name,
            description=description,
            mode_defs=[mode_def],
            preset_defs=presets or _preset_defs,
            tags=tags,
            metadata=metadata,
            metadata_entries=_metadata_entries,
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

    @public  # type: ignore
    @property
    def executor_def(self) -> ExecutorDefinition:
        return self.get_mode_definition().executor_defs[0]

    @public  # type: ignore
    @property
    def resource_defs(self) -> Mapping[str, ResourceDefinition]:
        return self.get_mode_definition().resource_defs

    @public  # type: ignore
    @property
    def partitioned_config(self) -> Optional[PartitionedConfig]:
        return self.get_mode_definition().partitioned_config

    @public  # type: ignore
    @property
    def config_mapping(self) -> Optional[ConfigMapping]:
        return self.get_mode_definition().config_mapping

    @public  # type: ignore
    @property
    def loggers(self) -> Mapping[str, LoggerDefinition]:
        return self.get_mode_definition().loggers

    @public
    def execute_in_process(
        self,
        run_config: Optional[Mapping[str, Any]] = None,
        instance: Optional["DagsterInstance"] = None,
        partition_key: Optional[str] = None,
        raise_on_error: bool = True,
        op_selection: Optional[Sequence[str]] = None,
        asset_selection: Optional[Sequence[AssetKey]] = None,
        run_id: Optional[str] = None,
        input_values: Optional[Mapping[str, object]] = None,
        tags: Optional[Mapping[str, str]] = None,
    ) -> "ExecuteInProcessResult":
        """
        Execute the Job in-process, gathering results in-memory.

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
                A dictionary that maps python objects to the top-level inputs of the job. Input values provided here will override input values that have been provided to the job directly.
        Returns:
            :py:class:`~dagster.ExecuteInProcessResult`

        """
        from dagster._core.definitions.executor_definition import execute_in_process_executor
        from dagster._core.execution.execute_in_process import core_execute_in_process

        run_config = check.opt_mapping_param(run_config, "run_config")
        op_selection = check.opt_sequence_param(op_selection, "op_selection", str)
        asset_selection = check.opt_sequence_param(asset_selection, "asset_selection", AssetKey)

        check.invariant(
            not (op_selection and asset_selection),
            "op_selection and asset_selection cannot both be provided as args to execute_in_process",
        )

        partition_key = check.opt_str_param(partition_key, "partition_key")
        input_values = check.opt_mapping_param(input_values, "input_values")

        # Combine provided input values at execute_in_process with input values
        # provided to the definition. Input values provided at
        # execute_in_process will override those provided on the definition.
        input_values = merge_dicts(self.input_values, input_values)

        resource_defs = dict(self.resource_defs)
        logger_defs = dict(self.loggers)
        ephemeral_job = JobDefinition(
            name=self._name,
            graph_def=self._graph_def,
            resource_defs=_swap_default_io_man(resource_defs, self),
            executor_def=execute_in_process_executor,
            logger_defs=logger_defs,
            hook_defs=self.hook_defs,
            config=self.config_mapping or self.partitioned_config,
            tags=self.tags,
            op_retry_policy=self._solid_retry_policy,
            version_strategy=self.version_strategy,
            asset_layer=self.asset_layer,
            input_values=input_values,
            _executor_def_specified=self._executor_def_specified,
            _logger_defs_specified=self._logger_defs_specified,
            _preset_defs=self._preset_defs,
        )

        ephemeral_job = ephemeral_job.get_job_def_for_subset_selection(
            op_selection, frozenset(asset_selection) if asset_selection else None
        )

        merged_tags = merge_dicts(self.tags, tags or {})
        if partition_key:
            if not self.partitioned_config:
                check.failed(
                    f"Provided partition key `{partition_key}` for job `{self._name}` without a partitioned config"
                )
            partition_set = self.get_partition_set_def()
            if not partition_set:
                check.failed(
                    f"Provided partition key `{partition_key}` for job `{self._name}` without a partitioned config"
                )

            partition = partition_set.get_partition(partition_key)
            run_config = (
                run_config if run_config else partition_set.run_config_for_partition(partition)
            )
            merged_tags.update(partition_set.tags_for_partition(partition))

        return core_execute_in_process(
            ephemeral_pipeline=ephemeral_job,
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
    def is_subset_pipeline(self) -> bool:
        if self._subset_selection_data:
            return True
        return False

    def get_job_def_for_subset_selection(
        self,
        op_selection: Optional[Sequence[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
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
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
    ) -> "JobDefinition":
        asset_selection = check.opt_set_param(asset_selection, "asset_selection", AssetKey)

        nonexistent_assets = [
            asset
            for asset in asset_selection
            if asset not in self.asset_layer.asset_keys
            and asset not in self.asset_layer.source_assets_by_key
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

        check.invariant(
            self.asset_layer.assets_defs_by_key is not None,
            "Asset layer must have _asset_defs argument defined",
        )

        new_job = build_asset_selection_job(
            name=self.name,
            assets=set(self.asset_layer.assets_defs_by_key.values()),
            source_assets=self.asset_layer.source_assets_by_key.values(),
            executor_def=self.executor_def,
            resource_defs=self.resource_defs,
            description=self.description,
            tags=self.tags,
            asset_selection=asset_selection,
            asset_selection_data=asset_selection_data,
            config=self.config_mapping or self.partitioned_config,
        )
        return new_job

    def _get_job_def_for_op_selection(
        self,
        op_selection: Optional[Sequence[str]] = None,
    ) -> "JobDefinition":
        if not op_selection:
            return self

        op_selection = check.opt_sequence_param(op_selection, "op_selection", str)

        resolved_op_selection_dict = parse_op_selection(self, op_selection)

        try:
            sub_graph = get_subselected_graph_definition(self.graph, resolved_op_selection_dict)

            # if explicit config was passed the config_mapping that resolves the defaults implicitly is
            # very unlikely to work. The preset will still present the default config in dagit.
            if self._explicit_config:
                config_arg = None
            else:
                config_arg = self.config_mapping or self.partitioned_config

            return JobDefinition(
                name=self.name,
                description=self.description,
                resource_defs=dict(self.resource_defs),
                logger_defs=dict(self.loggers),
                executor_def=self.executor_def,
                config=config_arg,
                tags=self.tags,
                hook_defs=self.hook_defs,
                op_retry_policy=self._solid_retry_policy,
                graph_def=sub_graph,
                version_strategy=self.version_strategy,
                _executor_def_specified=self._executor_def_specified,
                _logger_defs_specified=self._logger_defs_specified,
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
                _preset_defs=self._preset_defs,
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

    @public  # type: ignore
    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        mode = self.get_mode_definition()
        if not mode.partitioned_config:
            return None

        return mode.partitioned_config.partitions_def

    @public
    def run_request_for_partition(
        self,
        partition_key: str,
        run_key: Optional[str] = None,
        tags: Optional[Mapping[str, str]] = None,
        asset_selection: Optional[Sequence[AssetKey]] = None,
        run_config: Optional[Mapping[str, Any]] = None,
    ) -> RunRequest:
        """
        Creates a RunRequest object for a run that processes the given partition.

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

        Returns:
            RunRequest: an object that requests a run to process the given partition.
        """
        partition_set = self.get_partition_set_def()
        if not partition_set:
            check.failed("Called run_request_for_partition on a non-partitioned job")

        partition = partition_set.get_partition(partition_key)
        run_request_tags = (
            {**tags, **partition_set.tags_for_partition(partition)}
            if tags
            else partition_set.tags_for_partition(partition)
        )

        return RunRequest(
            run_key=run_key,
            run_config=run_config
            if run_config is not None
            else partition_set.run_config_for_partition(partition),
            tags=run_request_tags,
            job_name=self.name,
            asset_selection=asset_selection,
        )

    @public
    def with_hooks(self, hook_defs: AbstractSet[HookDefinition]) -> "JobDefinition":
        """Apply a set of hooks to all op instances within the job."""

        hook_defs = check.set_param(hook_defs, "hook_defs", of_type=HookDefinition)

        job_def = JobDefinition(
            name=self.name,
            graph_def=self._graph_def,
            resource_defs=dict(self.resource_defs),
            logger_defs=dict(self.loggers),
            executor_def=self.executor_def,
            config=self.partitioned_config or self.config_mapping,
            tags=self.tags,
            hook_defs=hook_defs | self.hook_defs,
            description=self._description,
            op_retry_policy=self._solid_retry_policy,
            asset_layer=self.asset_layer,
            _subset_selection_data=self._subset_selection_data,
            _executor_def_specified=self._executor_def_specified,
            _logger_defs_specified=self._logger_defs_specified,
            _preset_defs=self._preset_defs,
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
        return input_name in self.input_values

    def get_direct_input_value(self, input_name: str) -> object:
        if input_name not in self.input_values:
            raise DagsterInvalidInvocationError(
                f"On job '{self.name}', attempted to retrieve input value for input named '{input_name}', but no value was provided. Provided input values: {sorted(list(self.input_values.keys()))}"
            )
        return self.input_values[input_name]

    def with_executor_def(self, executor_def: ExecutorDefinition) -> "JobDefinition":
        return JobDefinition(
            graph_def=self.graph,
            resource_defs=dict(self.resource_defs),
            executor_def=executor_def,
            logger_defs=dict(self.loggers),
            config=self.config_mapping or self.partitioned_config,
            name=self.name,
            description=self.description,
            tags=self.tags,
            _metadata_entries=self.metadata,
            hook_defs=self.hook_defs,
            op_retry_policy=self._solid_retry_policy,
            version_strategy=self.version_strategy,
            _subset_selection_data=self._subset_selection_data,
            asset_layer=self.asset_layer,
            input_values=self.input_values,
            _executor_def_specified=False,
            _logger_defs_specified=self._logger_defs_specified,
            _preset_defs=self._preset_defs,
        )

    def with_logger_defs(self, logger_defs: Mapping[str, LoggerDefinition]) -> "JobDefinition":
        return JobDefinition(
            graph_def=self.graph,
            resource_defs=dict(self.resource_defs),
            executor_def=self.executor_def,
            logger_defs=logger_defs,
            config=self.config_mapping or self.partitioned_config,
            name=self.name,
            description=self.description,
            tags=self.tags,
            _metadata_entries=self.metadata,
            hook_defs=self.hook_defs,
            op_retry_policy=self._solid_retry_policy,
            version_strategy=self.version_strategy,
            _subset_selection_data=self._subset_selection_data,
            asset_layer=self.asset_layer,
            input_values=self.input_values,
            _executor_def_specified=self._executor_def_specified,
            _logger_defs_specified=False,
            _preset_defs=self._preset_defs,
        )


def _swap_default_io_man(resources: Mapping[str, ResourceDefinition], job: PipelineDefinition):
    """
    Used to create the user facing experience of the default io_manager
    switching to in-memory when using execute_in_process.
    """
    from dagster._core.storage.mem_io_manager import mem_io_manager

    if (
        # pylint: disable=comparison-with-callable
        resources.get(DEFAULT_IO_MANAGER_KEY) in [default_job_io_manager]
        and job.version_strategy is None
    ):
        updated_resources = dict(resources)
        updated_resources[DEFAULT_IO_MANAGER_KEY] = mem_io_manager
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
    resolved_op_selection_dict: Mapping,
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
        definition: Union[SubselectedGraphDefinition, NodeDefinition]
        if node.is_graph and resolved_op_selection_dict[node.name] is not LeafNodeSelection:
            definition = get_subselected_graph_definition(
                cast(GraphDefinition, node.definition),  # guaranteed by node.is_graph
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
        for node_input in node.inputs():
            if graph.dependency_structure.has_direct_dep(node_input):
                node_output = graph.dependency_structure.get_direct_dep(node_input)
                if node_output.node.name in resolved_op_selection_dict:
                    deps[_dep_key_of(node)][node_input.input_def.name] = DependencyDefinition(
                        node=node_output.node.name, output=node_output.output_def.name
                    )
            elif graph.dependency_structure.has_dynamic_fan_in_dep(node_input):
                node_output = graph.dependency_structure.get_dynamic_fan_in_dep(node_input)
                if node_output.node.name in resolved_op_selection_dict:
                    deps[_dep_key_of(node)][
                        node_input.input_def.name
                    ] = DynamicCollectDependencyDefinition(
                        solid_name=node_output.node.name,
                        output_name=node_output.output_def.name,
                    )
            elif graph.dependency_structure.has_fan_in_deps(node_input):
                outputs = graph.dependency_structure.get_fan_in_deps(node_input)
                multi_dependencies = [
                    DependencyDefinition(
                        node=output_handle.node.name, output=output_handle.output_def.name
                    )
                    for output_handle in outputs
                    if (
                        isinstance(output_handle, NodeOutput)
                        and output_handle.node.name in resolved_op_selection_dict
                    )
                ]
                deps[_dep_key_of(node)][node_input.input_def.name] = MultiDependencyDefinition(
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
        return cast(JobDefinition, target).input_values  # pylint: disable=protected-access
    else:
        return {}


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
                "DAGSTER_DEFAULT_IO_MANAGER_MODULE and DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE must specify an IOManagerDefinition",
            )
            with build_resources({"io_manager": attr}, instance=init_context.instance) as resources:
                return resources.io_manager
        except Exception as e:
            if not silence_failures:
                raise
            else:
                warnings.warn(
                    f"Failed to load io manager override with module: {module_name} attribute: {attribute_name}: {e}\n"
                    "Falling back to default io manager."
                )

    # normally, default to the fs_io_manager
    from dagster._core.storage.fs_io_manager import PickledObjectFilesystemIOManager

    instance = check.not_none(init_context.instance)
    return PickledObjectFilesystemIOManager(base_dir=instance.storage_directory())


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
                "DAGSTER_DEFAULT_IO_MANAGER_MODULE and DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE must specify an IOManagerDefinition",
            )
            with build_resources({"io_manager": attr}, instance=init_context.instance) as resources:
                return resources.io_manager
        except Exception as e:
            if not silence_failures:
                raise
            else:
                warnings.warn(
                    f"Failed to load io manager override with module: {module_name} attribute: {attribute_name}: {e}\n"
                    "Falling back to default io manager."
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
) -> ConfigType:
    return (
        JobDefinition(
            name=graph_def.name,
            graph_def=graph_def,
            resource_defs=resource_defs,
            executor_def=executor_def,
            logger_defs=logger_defs,
            asset_layer=asset_layer,
        )
        .get_run_config_schema("default")
        .run_config_schema_type
    )
