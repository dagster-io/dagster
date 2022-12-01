import importlib
import os
import warnings
from functools import update_wrapper
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    FrozenSet,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

from typing_extensions import Self

import dagster._check as check
from dagster._annotations import public
from dagster._config import Field, Shape, StringSource
from dagster._config.config_type import ConfigType
from dagster._config.validate import validate_config
from dagster._core.definitions.composition import MappedInputPlaceholder
from dagster._core.definitions.dependency import (
    DynamicCollectDependencyDefinition,
    IDependencyDefinition,
    MultiDependencyDefinition,
    Node,
    NodeHandle,
    NodeInputHandle,
    NodeInvocation,
    NodeOutput,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.partition import DynamicPartitionsDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_requirement import ensure_requirements_satisfied
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
    SelectionTreeBranch,
    SelectionTreeLeaf,
    parse_op_selection,
)
from dagster._core.storage.io_manager import IOManagerDefinition, io_manager
from dagster._core.storage.tags import MEMOIZED_RUN_TAG
from dagster._core.utils import str_format_set
from dagster._utils.merger import merge_dicts
from dagster._utils import frozentags, merge_dicts
from dagster._utils.backcompat import experimental_class_warning

from .asset_layer import AssetLayer, build_asset_selection_job
from .config import ConfigMapping
from .dependency import DependencyDefinition, DependencyStructure, GraphNode
from .executor_definition import ExecutorDefinition, multi_or_in_process_executor
from .graph_definition import GraphDefinition, SubselectedGraphDefinition
from .hook_definition import HookDefinition
from .logger_definition import LoggerDefinition
from .metadata import MetadataEntry, PartitionMetadataEntry, RawMetadataValue, normalize_metadata
from .mode import ModeDefinition
from .partition import PartitionedConfig, PartitionsDefinition, PartitionSetDefinition
from .preset import PresetDefinition
from .resource_definition import ResourceDefinition
from .run_request import RunRequest
from .utils import DEFAULT_IO_MANAGER_KEY, validate_tags
from .version_strategy import VersionStrategy

if TYPE_CHECKING:
    from dagster._config.snap import ConfigSchemaSnapshot
    from dagster._core.definitions.run_config_schema import RunConfigSchema
    from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
    from dagster._core.execution.resources_init import InitResourceContext
    from dagster._core.host_representation.pipeline_index import PipelineIndex
    from dagster._core.instance import DagsterInstance
    from dagster._core.snap import PipelineSnapshot

    from .partition import PartitionSetDefinition, PartitionedConfig, PartitionsDefinition


class JobDefinition:
    """Defines a Dagster job.

    A job is made up of

    - Ops, each of which is a single functional unit of data computation.
    - Dependencies, which determine how the values produced by solids as their outputs flow from
      one solid to another. This tells Dagster how to arrange solids, and potentially multiple
      aliased instances of solids, into a directed, acyclic graph (DAG) of compute.

    Args:
        graph_def (GraphDefinition): The graph containing the ops for this job.
        resource_defs (Optional[Mapping[str, ResourceDefinition]]):
            Resources that are required by this graph for execution.
            If not defined, `io_manager` will default to filesystem.
        executor_def (Optional[ExecutorDefinition]):
            How this Job will be executed. Defaults to :py:class:`multiprocess_executor` .
        logger_defs (Optional[Dict[str, LoggerDefinition]]):
            A dictionary of string logger identifiers to their implementations.
        name (str): The name of the pipeline. Must be unique within any
            :py:class:`RepositoryDefinition` containing the pipeline.
        name (Optional[str]):
            The name for the Job. Defaults to the name of the this graph.
        config:
            Describes how the job is parameterized at runtime.

            If no value is provided, then the schema for the job's run config is a standard
            format based on its ops and resources.

            If a dictionary is provided, then it must conform to the standard config schema, and
            it will be used as the job's run config for the job whenever the job is executed.
            The values provided will be viewable and editable in the Dagit playground, so be
            careful with secrets.

            If a :py:class:`ConfigMapping` object is provided, then the schema for the job's run config is
            determined by the config mapping, and the ConfigMapping, which should return
            configuration in the standard format to configure the job.

            If a :py:class:`PartitionedConfig` object is provided, then it defines a discrete set of config
            values that can parameterize the pipeline, as well as a function for mapping those
            values to the base config. The values provided will be viewable and editable in the
            Dagit playground, so be careful with secrets.
        description (Optional[str]): A human-readable description of the job.
        partitions_def (Optional[PartitionsDefinition]): Defines a discrete set of partition keys
            that can parameterize the job. If this argument is supplied, the config argument
            can't also be supplied.
        tags (Optional[Dict[str, Any]]):
            Arbitrary information that will be attached to the execution of the Job.
            Values that are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.  These tag values may be overwritten by tag
            values provided at invocation time.
        metadata (Optional[Dict[str, RawMetadataValue]]):
            Arbitrary information that will be attached to the JobDefinition and be viewable in Dagit.
            Keys must be strings, and values must be python primitive types or one of the provided
            MetadataValue types
        hook_defs (Optional[AbstractSet[HookDefinition]]): A set of hook definitions applied to the
            job. When a hook is applied to a job, it will be attached to all op
            instances within the job.
        op_retry_policy (Optional[RetryPolicy]): The default retry policy for all ops in this job.
            Only used if retry policy is not defined on the op definition or op invocation.
        version_strategy (Optional[VersionStrategy]):
            Defines how each op (and optionally, resource) in the job can be versioned. If
            provided, memoization will be enabled for this job.
        input_values (Optional[Mapping[str, Any]]):
            A dictionary that maps python objects to the top-level inputs of a job.


    """

    _name: str
    _graph_def: GraphDefinition
    _description: Optional[str]
    _tags: Mapping[str, str]
    _metadata: Sequence[Union[MetadataEntry, PartitionMetadataEntry]]
    _current_level_node_defs: Sequence[NodeDefinition]
    _mode_definitions: Sequence[ModeDefinition]
    _hook_defs: AbstractSet[HookDefinition]
    _op_retry_policy: Optional[RetryPolicy]
    _preset_defs: Sequence[PresetDefinition]
    _preset_dict: Dict[str, PresetDefinition]
    _asset_layer: AssetLayer
    _resource_requirements: Mapping[str, AbstractSet[str]]
    _all_node_defs: Mapping[str, NodeDefinition]
    _parent_job_def: Optional["JobDefinition"]
    _cached_run_config_schemas: Dict[str, "RunConfigSchema"]
    _cached_external_job: Any
    _version_strategy: VersionStrategy
    _cached_partition_set: Optional["PartitionSetDefinition"]
    _subset_selection_data: Optional[Union[OpSelectionData, AssetSelectionData]]
    _explicit_config: bool
    input_values: Mapping[str, object]

    def __init__(
        self,
        *,
        graph_def: GraphDefinition,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
        logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
        name: Optional[str] = None,
        config: Optional[Union[ConfigMapping, Mapping[str, object], "PartitionedConfig"]] = None,
        description: Optional[str] = None,
        partitions_def: Optional["PartitionsDefinition"] = None,
        tags: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        op_retry_policy: Optional[RetryPolicy] = None,
        version_strategy: Optional[VersionStrategy] = None,
        input_values: Optional[Mapping[str, object]] = None,
        _subset_selection_data: Optional[Union[OpSelectionData, AssetSelectionData]] = None,
        _asset_layer: Optional[AssetLayer] = None,
        _metadata_entries: Optional[Sequence[Union[MetadataEntry, PartitionMetadataEntry]]] = None,
        _executor_def_specified: Optional[bool] = None,
        _logger_defs_specified: Optional[bool] = None,
        _preset_defs: Optional[Sequence[PresetDefinition]] = None,
        _parent_job_def: Optional["JobDefinition"] = None,
        _mode_def: Optional["ModeDefinition"] = None,
    ):
        from dagster._loggers import default_loggers

        from .partition import PartitionedConfig, PartitionsDefinition

        self._graph_def = check.inst_param(graph_def, "graph_def", GraphDefinition)
        self._current_level_node_defs = self._graph_def.node_defs

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

        check.opt_mapping_param(
            logger_defs,
            "logger_defs",
            key_type=str,
            value_type=LoggerDefinition,
        )
        self._name = check_valid_name(check.opt_str_param(name, "name", default=graph_def.name))

        config = check.opt_inst_param(config, "config", (Mapping, ConfigMapping, PartitionedConfig))
        partitions_def = check.opt_inst_param(
            partitions_def, "partitions_def", PartitionsDefinition
        )
        # tags and description can exist on graph as well, but since
        # same graph may be in multiple pipelines/jobs, keep separate layer
        self._description = check.opt_str_param(description, "description")
        self._tags = validate_tags(check.opt_mapping_param(tags, "tags", key_type=str))

        self._hook_defs = check.opt_set_param(hook_defs, "hook_defs", of_type=HookDefinition)
        self._op_retry_policy = check.opt_inst_param(
            op_retry_policy, "op_retry_policy", RetryPolicy
        )

        self.version_strategy = check.opt_inst_param(
            version_strategy, "version_strategy", VersionStrategy
        )
        if self.version_strategy is not None:
            experimental_class_warning("VersionStrategy")

        _subset_selection_data = check.opt_inst_param(
            _subset_selection_data, "_subset_selection_data", (OpSelectionData, AssetSelectionData)
        )
        self._asset_layer = check.opt_inst_param(
            _asset_layer, "_asset_layer", AssetLayer, default=AssetLayer.from_graph(self._graph_def)
        )

        input_values = check.opt_mapping_param(input_values, "input_values", key_type=str)
        self._metadata_entries = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata"),
            check.opt_sequence_param(_metadata_entries, "_metadata_entries"),
        )

        executor_def = check.opt_inst_param(
            executor_def, "executor_def", ExecutorDefinition, default=multi_or_in_process_executor
        )
        logger_defs = logger_defs or default_loggers()
        resource_defs = check.opt_mapping_param(
            resource_defs, "resource_defs", key_type=str, value_type=ResourceDefinition
        )
        if resource_defs and DEFAULT_IO_MANAGER_KEY in resource_defs:
            resource_defs_with_defaults = resource_defs
        else:
            resource_defs_with_defaults = merge_dicts(
                {DEFAULT_IO_MANAGER_KEY: default_job_io_manager}, resource_defs or {}
            )

        presets: List[PresetDefinition] = []
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
                    (
                        "Bad state: attempted to pass preset definitions to job alongside config"
                        " dictionary."
                    ),
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
                        _asset_layer,
                    ),
                    config,
                    self._name,
                )
                self._explicit_config = True
            elif config is not None:
                check.failed(
                    "config param must be a ConfigMapping, a PartitionedConfig, or a dictionary,"
                    f" but is an object of type {type(config)}"
                )

        self._preset_defs = check.opt_sequence_param(
            presets, "preset_defs", of_type=PresetDefinition
        )

        # Exists for backcompat - JobDefinition is implemented as a single-mode pipeline.
        if _mode_def is None:
            _mode_def = ModeDefinition(
                resource_defs=resource_defs_with_defaults,
                logger_defs=logger_defs,
                executor_defs=[executor_def] if executor_def else None,
                _config_mapping=config_mapping,
                _partitioned_config=partitioned_config,
            )
        self._mode_definitions = [_mode_def]

        resource_requirements = {}
        resource_requirements[_mode_def.name] = self._get_resource_requirements_for_mode(_mode_def)
        self._resource_requirements = resource_requirements

        self._preset_dict: Dict[str, PresetDefinition] = {}
        for preset in self._preset_defs:
            if preset.name in self._preset_dict:
                raise DagsterInvalidDefinitionError(
                    (
                        f'Two PresetDefinitions seen with the name "{preset.name}" in "{self._name}". '
                        "PresetDefinitions must have unique names."
                    )
                )
            if preset.mode != _mode_def.name:
                raise DagsterInvalidDefinitionError(
                    (
                        f'PresetDefinition "{preset.name}" in "{self._name}" '
                        f'references mode "{preset.mode}" which is not defined.'
                    )
                )
            self._preset_dict[preset.name] = preset

        # Recursively explore all nodes in the this pipeline
        self._all_node_defs = _build_all_node_defs(self._current_level_node_defs)
        self._parent_job_def = check.opt_inst_param(
            _parent_job_def, "_parent_job_def", JobDefinition
        )
        self._cached_run_config_schemas = {}
        self._cached_external_pipeline = None

        self._cached_partition_set: Optional["PartitionSetDefinition"] = None
        self._subset_selection_data = _subset_selection_data
        self.input_values = input_values
        for input_name in sorted(list(self.input_values.keys())):
            if not graph_def.has_input(input_name):
                raise DagsterInvalidDefinitionError(
                    f"Error when constructing JobDefinition '{name}': Input value provided for key"
                    f" '{input_name}', but job has no top-level input with that name."
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
            asset_layer=asset_layer or _infer_asset_layer_from_source_asset_deps(graph_def),
                    f"Error when constructing JobDefinition '{self._name}': Input value provided for key '{input_name}', but job has no top-level input with that name."
                )

        self._graph_def.get_inputs_must_be_resolved_top_level(self._asset_layer)

    def _get_resource_requirements_for_mode(self, mode_def: ModeDefinition) -> Set[str]:
        from ..execution.resources_init import get_transitive_required_resource_keys

        requirements = list(self._graph_def.get_resource_requirements(self._asset_layer))
        for hook_def in self._hook_defs:
            requirements += list(
                hook_def.get_resource_requirements(
                    outer_context=f"{self.target_type} '{self._name}'"
                )
            )
        ensure_requirements_satisfied(mode_def.resource_defs, requirements, mode_def.name)
        required_keys = {requirement.key for requirement in requirements}
        return required_keys.union(
            get_transitive_required_resource_keys(required_keys, mode_def.resource_defs)
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def target_type(self) -> str:
        return "job"

    @property
    def hook_defs(self) -> AbstractSet[HookDefinition]:
        return self._hook_defs

    @property
    def asset_layer(self) -> AssetLayer:
        return self._asset_layer

    @property
    def is_job(self) -> bool:
        return True

    def describe_target(self):
        return f"{self.target_type} '{self.name}'"

    @property
    def tags(self) -> Mapping[str, str]:
        return frozentags(**merge_dicts(self._graph_def.tags, self._tags))

    @property
    def is_single_mode(self) -> bool:
        return True

    @property
    def is_multi_mode(self) -> bool:
        return False

    @property
    def mode_definitions(self) -> Sequence[ModeDefinition]:
        return self._mode_definitions

    def is_using_memoization(self, run_tags: Mapping[str, str]) -> bool:
        tags = merge_dicts(self.tags, run_tags)
        # If someone provides a false value for memoized run tag, then they are intentionally
        # switching off memoization.
        if tags.get(MEMOIZED_RUN_TAG) == "false":
            return False
        return (
            MEMOIZED_RUN_TAG in tags and tags.get(MEMOIZED_RUN_TAG) == "true"
        ) or self.version_strategy is not None

    def has_mode_definition(self, mode: str) -> bool:
        check.str_param(mode, "mode")
        return bool(self._get_mode_definition(mode))

    def get_default_mode_name(self) -> str:
        return self._mode_definitions[0].name

    def get_mode_definition(self, mode: Optional[str] = None) -> ModeDefinition:
        check.opt_str_param(mode, "mode")
        if mode is None:
            check.invariant(self.is_single_mode)
            return self.get_default_mode()

        mode_def = self._get_mode_definition(mode)

        if mode_def is None:
            check.failed(
                "Could not find mode {mode} in pipeline {name}".format(mode=mode, name=self.name),
            )

        return mode_def

    @property
    def preset_defs(self) -> Sequence[PresetDefinition]:
        return self._preset_defs

    def _get_mode_definition(self, mode: str) -> Optional[ModeDefinition]:
        check.str_param(mode, "mode")
        for mode_definition in self._mode_definitions:
            if mode_definition.name == mode:
                return mode_definition

        return None

    def get_default_mode(self) -> ModeDefinition:
        return self._mode_definitions[0]

    @property
    def metadata(self) -> Sequence[Union[MetadataEntry, PartitionMetadataEntry]]:
        return self._metadata_entries

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
    def dependencies(
        self,
    ) -> Mapping[Union[str, NodeInvocation], Mapping[str, IDependencyDefinition]]:
        return self._graph_def.dependencies

    def get_run_config_schema(self, mode: Optional[str] = None) -> "RunConfigSchema":
        check.str_param(mode, "mode")

        mode_def = self.get_mode_definition(mode)

        if mode_def.name in self._cached_run_config_schemas:
            return self._cached_run_config_schemas[mode_def.name]

        self._cached_run_config_schemas[mode_def.name] = _create_run_config_schema(
            self,
            mode_def,
            self._resource_requirements[mode_def.name],
        )
        return self._cached_run_config_schemas[mode_def.name]

    @public  # type: ignore
    @property
    def executor_def(self) -> ExecutorDefinition:
        return self.get_mode_definition().executor_defs[0]

    @public
    @property
    def resource_defs(self) -> Mapping[str, ResourceDefinition]:
        return self.get_mode_definition().resource_defs

    @public
    @property
    def partitioned_config(self) -> Optional["PartitionedConfig"]:
        return self.get_mode_definition().partitioned_config

    @public
    @property
    def config_mapping(self) -> Optional[ConfigMapping]:
        return self.get_mode_definition().config_mapping

    @public
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
            (
                "op_selection and asset_selection cannot both be provided as args to"
                " execute_in_process"
            ),
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
            op_retry_policy=self._op_retry_policy,
            version_strategy=self.version_strategy,
            _asset_layer=self.asset_layer,
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
                    f"Provided partition key `{partition_key}` for job `{self._name}` without a"
                    " partitioned config"
                )
            partition_set = self.get_partition_set_def()
            if not partition_set:
                check.failed(
                    f"Provided partition key `{partition_key}` for job `{self._name}` without a"
                    " partitioned config"
                )

            partition = partition_set.get_partition(partition_key, instance)
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
    ) -> Self:
        check.invariant(
            not (op_selection and asset_selection),
            (
                "op_selection and asset_selection cannot both be provided as args to"
                " execute_in_process"
            ),
        )
        if op_selection:
            return self._get_job_def_for_op_selection(op_selection)
        if asset_selection:
            return self._get_job_def_for_asset_selection(asset_selection)
        else:
            return self

    def _get_job_def_for_asset_selection(
        self,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
    ) -> Self:
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
    ) -> Self:
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
                op_retry_policy=self._op_retry_policy,
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
                _asset_layer=self.asset_layer,
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

    @public
    @property
    def partitions_def(self) -> Optional["PartitionsDefinition"]:
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
        instance: Optional["DagsterInstance"] = None,
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

        if isinstance(partition_set.partitions_def, DynamicPartitionsDefinition):
            if not instance:
                check.failed(
                    "Must provide a dagster instance when calling run_request_for_partition on a "
                    "dynamic partition set"
                )

        partition = partition_set.get_partition(partition_key, instance)
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
            op_retry_policy=self._op_retry_policy,
            _asset_layer=self.asset_layer,
            _subset_selection_data=self._subset_selection_data,
            _executor_def_specified=self._executor_def_specified,
            _logger_defs_specified=self._logger_defs_specified,
            _preset_defs=self._preset_defs,
        )

        update_wrapper(job_def, self, updated=())

        return job_def

    def get_parent_job_snapshot(self) -> Optional["PipelineSnapshot"]:
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
                f"On job '{self.name}', attempted to retrieve input value for input named"
                f" '{input_name}', but no value was provided. Provided input values:"
                f" {sorted(list(self.input_values.keys()))}"
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
            op_retry_policy=self._op_retry_policy,
            version_strategy=self.version_strategy,
            _subset_selection_data=self._subset_selection_data,
            _asset_layer=self.asset_layer,
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
            op_retry_policy=self._op_retry_policy,
            version_strategy=self.version_strategy,
            _subset_selection_data=self._subset_selection_data,
            _asset_layer=self.asset_layer,
            input_values=self.input_values,
            _executor_def_specified=self._executor_def_specified,
            _logger_defs_specified=False,
            _preset_defs=self._preset_defs,
        )

    @property
    def available_modes(self) -> Sequence[str]:
        return [mode_def.name for mode_def in self._mode_definitions]

    def get_required_resource_defs_for_mode(self, mode: str) -> Mapping[str, ResourceDefinition]:
        return {
            resource_key: resource
            for resource_key, resource in self.get_mode_definition(mode).resource_defs.items()
            if resource_key in self._resource_requirements[mode]
        }

    @property
    def all_node_defs(self) -> Sequence[NodeDefinition]:
        return list(self._all_node_defs.values())

    @property
    def top_level_solid_defs(self) -> Sequence[NodeDefinition]:
        return self._current_level_node_defs

    def solid_def_named(self, name: str) -> NodeDefinition:
        check.str_param(name, "name")

        check.invariant(name in self._all_node_defs, "{} not found".format(name))
        return self._all_node_defs[name]

    def has_solid_def(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self._all_node_defs

    def get_solid(self, handle):
        return self._graph_def.get_solid(handle)

    def has_solid_named(self, name):
        return self._graph_def.has_solid_named(name)

    def solid_named(self, name):
        return self._graph_def.solid_named(name)

    @property
    def solids(self):
        return self._graph_def.solids

    @property
    def solids_in_topological_order(self):
        return self._graph_def.solids_in_topological_order

    def all_dagster_types(self):
        return self._graph_def.all_dagster_types()

    def has_dagster_type(self, name):
        return self._graph_def.has_dagster_type(name)

    def dagster_type_named(self, name):
        return self._graph_def.dagster_type_named(name)

    def has_preset(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self._preset_dict

    def get_preset(self, name: str) -> PresetDefinition:
        check.str_param(name, "name")
        if name not in self._preset_dict:
            raise DagsterInvariantViolationError(
                (
                    'Could not find preset for "{name}". Available presets '
                    'for pipeline "{pipeline_name}" are {preset_names}.'
                ).format(
                    name=name,
                    preset_names=list(self._preset_dict.keys()),
                    pipeline_name=self.name,
                )
            )

        return self._preset_dict[name]

    def get_pipeline_snapshot(self) -> "PipelineSnapshot":
        return self.get_pipeline_index().pipeline_snapshot

    def get_pipeline_snapshot_id(self) -> str:
        return self.get_pipeline_index().pipeline_snapshot_id

    def get_pipeline_index(self) -> "PipelineIndex":
        from dagster._core.host_representation import PipelineIndex
        from dagster._core.snap import PipelineSnapshot

        return PipelineIndex(
            PipelineSnapshot.from_pipeline_def(self), self.get_parent_job_snapshot()
        )

    def get_config_schema_snapshot(self) -> "ConfigSchemaSnapshot":
        return self.get_pipeline_snapshot().config_schema_snapshot

    @property
    def parent_job_def(self) -> Optional["JobDefinition"]:
        return None

    @property
    def solids_to_execute(self) -> Optional[FrozenSet[str]]:
        return None

    def get_all_hooks_for_handle(self, handle: NodeHandle) -> FrozenSet[HookDefinition]:
        """Gather all the hooks for the given solid from all places possibly attached with a hook.

        A hook can be attached to any of the following objects
        * Solid (solid invocation)
        * PipelineDefinition

        Args:
            handle (NodeHandle): The solid's handle

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

        # hooks on top-level solid
        name = lineage.pop()
        solid = self._graph_def.solid_named(name)
        hook_defs = hook_defs.union(solid.hook_defs)

        # hooks on non-top-level solids
        while lineage:
            name = lineage.pop()
            # While lineage is non-empty, definition is guaranteed to be a graph
            definition = cast(GraphDefinition, solid.definition)
            solid = definition.solid_named(name)
            hook_defs = hook_defs.union(solid.hook_defs)

        # hooks applied to a pipeline definition will run on every solid
        hook_defs = hook_defs.union(self.hook_defs)

        return frozenset(hook_defs)

    def get_retry_policy_for_handle(self, handle: NodeHandle) -> Optional[RetryPolicy]:
        solid = self.get_solid(handle)
        definition = solid.definition

        if solid.retry_policy:
            return solid.retry_policy
        elif isinstance(definition, OpDefinition) and definition.retry_policy:
            return definition.retry_policy

        # could be expanded to look in composite_solid / graph containers
        else:
            return self._op_retry_policy

    # make Callable for decorator reference updates
    def __call__(self, *args, **kwargs):
        if self.is_job:
            msg = (
                f"Attempted to call job '{self.name}' directly. Jobs should be invoked by "
                "using an execution API function (e.g. `job.execute_in_process`)."
            )
        else:
            msg = (
                f"Attempted to call pipeline '{self.name}' directly. Pipelines should be invoked by "
                "using an execution API function (e.g. `execute_pipeline`)."
            )
        raise DagsterInvariantViolationError(msg)


class PipelineSubsetDefinition(JobDefinition):
    @property
    def solids_to_execute(self) -> FrozenSet[str]:
        return frozenset(self._graph_def.node_names())

    @property
    def solid_selection(self) -> Sequence[str]:
        # we currently don't pass the real solid_selection (the solid query list) down here.
        # so in the short-term, to make the call sites cleaner, we will convert the solids to execute
        # to a list
        return self._graph_def.node_names()

    @property
    def parent_job_def(self) -> JobDefinition:
        return check.not_none(self._parent_job_def)

    def get_parent_job_snapshot(self) -> Optional["PipelineSnapshot"]:
        parent_job = check.not_none(self.parent_job_def)
        return parent_job.get_pipeline_snapshot()

    @property
    def is_subset_pipeline(self) -> bool:
        return True

    def get_pipeline_subset_def(
        self, _solids_to_execute: Optional[AbstractSet[str]]
    ) -> "PipelineSubsetDefinition":
        raise DagsterInvariantViolationError("Pipeline subsets may not be subset again.")


def _swap_default_io_man(resources: Mapping[str, ResourceDefinition], job: JobDefinition):
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
    resolved_op_selection_dict: SelectionTreeBranch,
    parent_handle: Optional[NodeHandle] = None,
) -> SubselectedGraphDefinition:
    deps: Dict[
        Union[str, NodeInvocation],
        Dict[str, IDependencyDefinition],
    ] = {}

    selected_nodes: List[Tuple[str, NodeDefinition]] = []

    for node in graph.nodes_in_topological_order:
        node_handle = NodeHandle(node.name, parent=parent_handle)
        # skip if the node isn't selected
        if node.name not in resolved_op_selection_dict:
            continue

        # rebuild graph if any nodes inside the graph are selected
        definition: Union[SubselectedGraphDefinition, NodeDefinition]
        selection_node = resolved_op_selection_dict[node.name]
        if isinstance(node, GraphNode) and not isinstance(selection_node, SelectionTreeLeaf):
            definition = get_subselected_graph_definition(
                node.definition,
                selection_node,
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
                        node_name=node_output.node.name,
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
            lambda input_mapping: input_mapping.maps_to.node_name
            in [name for name, _ in selected_nodes],
            graph._input_mappings,  # pylint: disable=protected-access
        )
    )
    new_output_mappings = list(
        filter(
            lambda output_mapping: output_mapping.maps_from.node_name
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


def get_direct_input_values_from_job(target: JobDefinition) -> Mapping[str, Any]:
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
                (
                    "DAGSTER_DEFAULT_IO_MANAGER_MODULE and DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE"
                    " must specify an IOManagerDefinition"
                ),
            )
            with build_resources({"io_manager": attr}, instance=init_context.instance) as resources:
                return resources.io_manager  # type: ignore
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
                (
                    "DAGSTER_DEFAULT_IO_MANAGER_MODULE and DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE"
                    " must specify an IOManagerDefinition"
                ),
            )
            with build_resources({"io_manager": attr}, instance=init_context.instance) as resources:
                return resources.io_manager  # type: ignore
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
) -> ConfigType:
    return (
        JobDefinition(
            name=graph_def.name,
            graph_def=graph_def,
            resource_defs=resource_defs,
            executor_def=executor_def,
            logger_defs=logger_defs,
            _asset_layer=asset_layer,
        )
        .get_run_config_schema("default")
        .run_config_schema_type
    )


def _infer_asset_layer_from_source_asset_deps(job_graph_def: GraphDefinition) -> AssetLayer:
    """
    For non-asset jobs that have some inputs that are fed from SourceAssets, constructs an
    AssetLayer that includes those SourceAssets.
    """
    asset_keys_by_node_input_handle: Dict[NodeInputHandle, AssetKey] = {}
    source_assets_list = []
    source_asset_keys_set = set()
    io_manager_keys_by_asset_key: Mapping[AssetKey, str] = {}

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

                if source_asset.io_manager_key:
                    io_manager_keys_by_asset_key[source_asset.key] = source_asset.io_manager_key

        for node_name, node in graph_def.node_dict.items():
            if isinstance(node.definition, GraphDefinition):
                stack.append((node.definition, NodeHandle(node_name, parent_node_handle)))

    return AssetLayer(
        asset_keys_by_node_input_handle=asset_keys_by_node_input_handle,
        asset_info_by_node_output_handle={},
        asset_deps={},
        dependency_node_handles_by_asset_key={},
        assets_defs=[],
        source_asset_defs=source_assets_list,
        io_manager_keys_by_asset_key=io_manager_keys_by_asset_key,
        node_output_handles_to_dep_asset_keys={},
        partition_mappings_by_asset_dep={},
    )

def _get_pipeline_subset_def(
    pipeline_def: JobDefinition,
    solids_to_execute: AbstractSet[str],
) -> "PipelineSubsetDefinition":
    """
    Build a pipeline which is a subset of another pipeline.
    Only includes the solids which are in solids_to_execute.
    """

    check.inst_param(pipeline_def, "pipeline_def", JobDefinition)
    check.set_param(solids_to_execute, "solids_to_execute", of_type=str)
    graph = pipeline_def.graph
    for solid_name in solids_to_execute:
        if not graph.has_solid_named(solid_name):
            raise DagsterInvalidSubsetError(
                "{target_type} {pipeline_name} has no {node_type} named {name}.".format(
                    target_type=pipeline_def.target_type,
                    pipeline_name=pipeline_def.name,
                    name=solid_name,
                    node_type="ops" if pipeline_def.is_job else "solids",
                ),
            )

    # go in topo order to ensure deps dict is ordered
    solids = list(
        filter(lambda solid: solid.name in solids_to_execute, graph.solids_in_topological_order)
    )

    deps: Dict[
        Union[str, NodeInvocation],
        Dict[str, IDependencyDefinition],
    ] = {_dep_key_of(solid): {} for solid in solids}

    for node in solids:
        for node_input in node.inputs():
            if graph.dependency_structure.has_direct_dep(node_input):
                node_output = pipeline_def.dependency_structure.get_direct_dep(node_input)
                if node_output.node.name in solids_to_execute:
                    deps[_dep_key_of(node)][node_input.input_def.name] = DependencyDefinition(
                        node=node_output.node.name, output=node_output.output_def.name
                    )
            elif graph.dependency_structure.has_dynamic_fan_in_dep(node_input):
                node_output = graph.dependency_structure.get_dynamic_fan_in_dep(node_input)
                if node_output.node.name in solids_to_execute:
                    deps[_dep_key_of(node)][
                        node_input.input_def.name
                    ] = DynamicCollectDependencyDefinition(
                        solid_name=node_output.node.name,
                        output_name=node_output.output_def.name,
                    )
            elif graph.dependency_structure.has_fan_in_deps(node_input):
                outputs = cast(
                    Sequence[NodeOutput],
                    graph.dependency_structure.get_fan_in_deps(node_input),
                )
                deps[_dep_key_of(node)][node_input.input_def.name] = MultiDependencyDefinition(
                    [
                        DependencyDefinition(
                            node=node_output.node.name, output=node_output.output_def.name
                        )
                        for node_output in outputs
                        if node_output.node.name in solids_to_execute
                    ]
                )
            # else input is unconnected

    try:
        sub_pipeline_def = PipelineSubsetDefinition(
            name=pipeline_def.name,  # should we change the name for subsetted pipeline?
            solid_defs=list({solid.definition for solid in solids}),
            mode_defs=pipeline_def.mode_definitions,
            dependencies=deps,
            _parent_pipeline_def=pipeline_def,
            tags=pipeline_def.tags,
            hook_defs=pipeline_def.hook_defs,
        )

        return sub_pipeline_def
    except DagsterInvalidDefinitionError as exc:
        # This handles the case when you construct a subset such that an unsatisfied
        # input cannot be loaded from config. Instead of throwing a DagsterInvalidDefinitionError,
        # we re-raise a DagsterInvalidSubsetError.
        raise DagsterInvalidSubsetError(
            f"The attempted subset {str_format_set(solids_to_execute)} for {pipeline_def.target_type} "
            f"{pipeline_def.name} results in an invalid {pipeline_def.target_type}"
        ) from exc


def _iterate_all_nodes(root_node_dict: Mapping[str, Node]) -> Iterator[Node]:
    for node in root_node_dict.values():
        yield node
        if node.is_graph:
            yield from _iterate_all_nodes(node.definition.ensure_graph_def().node_dict)


def _create_run_config_schema(
    pipeline_def: JobDefinition,
    mode_definition: ModeDefinition,
    required_resources: AbstractSet[str],
) -> "RunConfigSchema":
    from .run_config import (
        RunConfigSchemaCreationData,
        construct_config_type_dictionary,
        define_run_config_schema_type,
    )
    from .run_config_schema import RunConfigSchema

    # When executing with a subset pipeline, include the missing solids
    # from the original pipeline as ignored to allow execution with
    # run config that is valid for the original
    ignored_solids: Sequence[Node] = []
    if isinstance(pipeline_def, JobDefinition) and pipeline_def.is_subset_pipeline:
        if isinstance(pipeline_def.graph, SubselectedGraphDefinition):  # op selection provided
            ignored_solids = pipeline_def.graph.get_top_level_omitted_nodes()
        elif pipeline_def.asset_selection_data:
            parent_job = pipeline_def
            while parent_job.asset_selection_data:
                parent_job = parent_job.asset_selection_data.parent_job_def

            ignored_solids = [
                solid
                for solid in parent_job.graph.solids
                if not pipeline_def.has_solid_named(solid.name)
            ]
    elif pipeline_def.is_subset_pipeline:
        if pipeline_def.parent_job_def is None:
            check.failed("Unexpected subset pipeline state")

        ignored_solids = [
            solid
            for solid in pipeline_def.parent_job_def.graph.solids
            if not pipeline_def.has_solid_named(solid.name)
        ]
    else:
        ignored_solids = []

    run_config_schema_type = define_run_config_schema_type(
        RunConfigSchemaCreationData(
            pipeline_name=pipeline_def.name,
            solids=pipeline_def.graph.solids,
            graph_def=pipeline_def.graph,
            dependency_structure=pipeline_def.graph.dependency_structure,
            mode_definition=mode_definition,
            logger_defs=mode_definition.loggers,
            ignored_solids=ignored_solids,
            required_resources=required_resources,
            is_using_graph_job_op_apis=pipeline_def.is_job,
            direct_inputs=get_direct_input_values_from_job(pipeline_def),
            asset_layer=pipeline_def.asset_layer,
        )
    )

    if mode_definition.config_mapping:
        outer_config_type = mode_definition.config_mapping.config_schema.config_type
    else:
        outer_config_type = run_config_schema_type

    if outer_config_type is None:
        check.failed("Unexpected outer_config_type value of None")

    config_type_dict_by_name, config_type_dict_by_key = construct_config_type_dictionary(
        pipeline_def.all_node_defs,
        outer_config_type,
    )

    return RunConfigSchema(
        run_config_schema_type=run_config_schema_type,
        config_type_dict_by_name=config_type_dict_by_name,
        config_type_dict_by_key=config_type_dict_by_key,
        config_mapping=mode_definition.config_mapping,
    )
