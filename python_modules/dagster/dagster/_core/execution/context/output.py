import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    ContextManager,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
)

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.asset_layer import AssetOutputInfo
from dagster._core.definitions.events import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    Materialization,
    MetadataEntry,
    PartitionMetadataEntry,
)
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.plan.utils import build_resources_for_manager

if TYPE_CHECKING:
    from dagster._core.definitions import PartitionsDefinition, PipelineDefinition
    from dagster._core.definitions.op_definition import OpDefinition
    from dagster._core.definitions.resource_definition import Resources
    from dagster._core.events import DagsterEvent
    from dagster._core.execution.context.system import StepExecutionContext
    from dagster._core.execution.plan.outputs import StepOutputHandle
    from dagster._core.execution.plan.plan import ExecutionPlan
    from dagster._core.log_manager import DagsterLogManager
    from dagster._core.system_config.objects import ResolvedRunConfig
    from dagster._core.types.dagster_type import DagsterType

RUN_ID_PLACEHOLDER = "__EPHEMERAL_RUN_ID"


class OutputContext:
    """
    The context object that is available to the `handle_output` method of an :py:class:`IOManager`.

    Users should not instantiate this object directly. To construct an
    `OutputContext` for testing an IO Manager's `handle_output` method, use
    :py:func:`dagster.build_output_context`.

    Attributes:
        step_key (Optional[str]): The step_key for the compute step that produced the output.
        name (Optional[str]): The name of the output that produced the output.
        run_id (Optional[str]): The id of the run that produced the output.
        metadata (Optional[Mapping[str, RawMetadataValue]]): A dict of the metadata that is assigned to the
            OutputDefinition that produced the output.
        mapping_key (Optional[str]): The key that identifies a unique mapped output. None for regular outputs.
        config (Optional[Any]): The configuration for the output.
        dagster_type (Optional[DagsterType]): The type of this output.
        log (Optional[DagsterLogManager]): The log manager to use for this output.
        version (Optional[str]): (Experimental) The version of the output.
        resource_config (Optional[Mapping[str, Any]]): The config associated with the resource that
            initializes the RootInputManager.
        resources (Optional[Resources]): The resources required by the output manager, specified by the
            `required_resource_keys` parameter.
        op_def (Optional[OpDefinition]): The definition of the op that produced the output.
        asset_info: Optional[AssetOutputInfo]: (Experimental) Asset info corresponding to the
            output.

    Example:

    .. code-block:: python

        from dagster import IOManager, OutputContext

        class MyIOManager(IOManager):
            def handle_output(self, context: OutputContext, obj):
                ...

    """

    _step_key: Optional[str]
    _name: Optional[str]
    _pipeline_name: Optional[str]
    _run_id: Optional[str]
    _metadata: Optional[Mapping[str, RawMetadataValue]]
    _mapping_key: Optional[str]
    _config: object
    _op_def: Optional["OpDefinition"]
    _dagster_type: Optional["DagsterType"]
    _log: Optional["DagsterLogManager"]
    _version: Optional[str]
    _resource_config: Optional[Mapping[str, object]]
    _step_context: Optional["StepExecutionContext"]
    _asset_info: Optional[AssetOutputInfo]
    _warn_on_step_context_use: bool
    _resources: Optional["Resources"]
    _resources_cm: Optional[ContextManager["Resources"]]
    _resources_contain_cm: Optional[bool]
    _cm_scope_entered: Optional[bool]
    _events: List["DagsterEvent"]
    _user_events: List[Union[AssetMaterialization, AssetObservation, Materialization]]
    _metadata_entries: Optional[Sequence[Union[MetadataEntry, PartitionMetadataEntry]]]

    def __init__(
        self,
        step_key: Optional[str] = None,
        name: Optional[str] = None,
        pipeline_name: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        mapping_key: Optional[str] = None,
        config: object = None,
        dagster_type: Optional["DagsterType"] = None,
        log_manager: Optional["DagsterLogManager"] = None,
        version: Optional[str] = None,
        resource_config: Optional[Mapping[str, object]] = None,
        resources: Optional[Union["Resources", Mapping[str, object]]] = None,
        step_context: Optional["StepExecutionContext"] = None,
        op_def: Optional["OpDefinition"] = None,
        asset_info: Optional[AssetOutputInfo] = None,
        warn_on_step_context_use: bool = False,
        partition_key: Optional[str] = None,
    ):
        from dagster._core.definitions.resource_definition import IContainsGenerator, Resources
        from dagster._core.execution.build_resources import build_resources

        self._step_key = step_key
        self._name = name
        self._pipeline_name = pipeline_name
        self._run_id = run_id
        self._metadata = metadata
        self._mapping_key = mapping_key
        self._config = config
        self._op_def = op_def
        self._dagster_type = dagster_type
        self._log = log_manager
        self._version = version
        self._resource_config = resource_config
        self._step_context = step_context
        self._asset_info = asset_info
        self._warn_on_step_context_use = warn_on_step_context_use
        if self._step_context and self._step_context.has_partition_key:
            self._partition_key: Optional[str] = self._step_context.partition_key
        else:
            self._partition_key = partition_key

        if isinstance(resources, Resources):
            self._resources_cm = None
            self._resources = resources
        else:
            self._resources_cm = build_resources(
                check.opt_dict_param(resources, "resources", key_type=str)
            )
            self._resources = self._resources_cm.__enter__()  # pylint: disable=no-member
            self._resources_contain_cm = isinstance(self._resources, IContainsGenerator)
            self._cm_scope_entered = False

        self._events = []
        self._user_events = []
        self._metadata_entries = None

    def __enter__(self):
        if self._resources_cm:
            self._cm_scope_entered = True
        return self

    def __exit__(self, *exc):
        if self._resources_cm:
            self._resources_cm.__exit__(*exc)  # pylint: disable=no-member

    def __del__(self):
        if (
            hasattr(self, "_resources_cm")
            and self._resources_cm
            and self._resources_contain_cm
            and not self._cm_scope_entered
        ):
            self._resources_cm.__exit__(None, None, None)  # pylint: disable=no-member

    @public  # type: ignore
    @property
    def step_key(self) -> str:
        if self._step_key is None:
            raise DagsterInvariantViolationError(
                "Attempting to access step_key, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._step_key

    @public  # type: ignore
    @property
    def name(self) -> str:
        if self._name is None:
            raise DagsterInvariantViolationError(
                "Attempting to access name, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._name

    @property
    def pipeline_name(self) -> str:
        if self._pipeline_name is None:
            raise DagsterInvariantViolationError(
                "Attempting to access pipeline_name, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._pipeline_name

    @public  # type: ignore
    @property
    def run_id(self) -> str:
        if self._run_id is None:
            raise DagsterInvariantViolationError(
                "Attempting to access run_id, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._run_id

    @public  # type: ignore
    @property
    def metadata(self) -> Optional[Mapping[str, object]]:
        return self._metadata

    @public  # type: ignore
    @property
    def mapping_key(self) -> Optional[str]:
        return self._mapping_key

    @public  # type: ignore
    @property
    def config(self) -> Any:
        return self._config

    @public  # type: ignore
    @property
    def op_def(self) -> "OpDefinition":
        from dagster._core.definitions import OpDefinition

        if self._op_def is None:
            raise DagsterInvariantViolationError(
                "Attempting to access op_def, "
                "but it was not provided when constructing the OutputContext"
            )

        return cast(OpDefinition, self._op_def)

    @public  # type: ignore
    @property
    def dagster_type(self) -> "DagsterType":
        if self._dagster_type is None:
            raise DagsterInvariantViolationError(
                "Attempting to access dagster_type, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._dagster_type

    @public  # type: ignore
    @property
    def log(self) -> "DagsterLogManager":
        if self._log is None:
            raise DagsterInvariantViolationError(
                "Attempting to access log, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._log

    @public  # type: ignore
    @property
    def version(self) -> Optional[str]:
        return self._version

    @public  # type: ignore
    @property
    def resource_config(self) -> Optional[Mapping[str, object]]:
        return self._resource_config

    @public  # type: ignore
    @property
    def resources(self) -> Any:
        if self._resources is None:
            raise DagsterInvariantViolationError(
                "Attempting to access resources, "
                "but it was not provided when constructing the OutputContext"
            )

        if self._resources_cm and self._resources_contain_cm and not self._cm_scope_entered:
            raise DagsterInvariantViolationError(
                "At least one provided resource is a generator, but attempting to access "
                "resources outside of context manager scope. You can use the following syntax to "
                "open a context manager: `with build_output_context(...) as context:`"
            )
        return self._resources

    @property
    def asset_info(self) -> Optional[AssetOutputInfo]:
        return self._asset_info

    @public  # type: ignore
    @property
    def has_asset_key(self) -> bool:
        return self._asset_info is not None

    @public  # type: ignore
    @property
    def asset_key(self) -> AssetKey:
        if self._asset_info is None:
            raise DagsterInvariantViolationError(
                "Attempting to access asset_key, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._asset_info.key

    @public  # type: ignore
    @property
    def asset_partitions_def(self) -> "PartitionsDefinition":
        """The PartitionsDefinition on the asset corresponding to this output."""
        asset_key = self.asset_key
        result = self.step_context.pipeline_def.asset_layer.partitions_def_for_asset(asset_key)
        if result is None:
            raise DagsterInvariantViolationError(
                f"Attempting to access partitions def for asset {asset_key}, but it is not partitioned"
            )

        return result

    @property
    def step_context(self) -> "StepExecutionContext":
        if self._warn_on_step_context_use:
            warnings.warn(
                "You are using InputContext.upstream_output.step_context"
                "This use on upstream_output is deprecated and will fail in the future"
                "Try to obtain what you need directly from InputContext"
                "For more details: https://github.com/dagster-io/dagster/issues/7900"
            )

        if self._step_context is None:
            raise DagsterInvariantViolationError(
                "Attempting to access step_context, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._step_context

    @public  # type: ignore
    @property
    def has_partition_key(self) -> bool:
        """Whether the current run is a partitioned run"""
        if self._warn_on_step_context_use:
            warnings.warn(
                "You are using InputContext.upstream_output.has_partition_key"
                "This use on upstream_output is deprecated and will fail in the future"
                "Try to obtain what you need directly from InputContext"
                "For more details: https://github.com/dagster-io/dagster/issues/7900"
            )

        return self._partition_key is not None

    @public  # type: ignore
    @property
    def partition_key(self) -> str:
        """The partition key for the current run.

        Raises an error if the current run is not a partitioned run.
        """
        if self._warn_on_step_context_use:
            warnings.warn(
                "You are using InputContext.upstream_output.partition_key"
                "This use on upstream_output is deprecated and will fail in the future"
                "Try to obtain what you need directly from InputContext"
                "For more details: https://github.com/dagster-io/dagster/issues/7900"
            )

        check.invariant(
            self._partition_key is not None,
            "Tried to access partition_key on a non-partitioned run.",
        )
        return cast(str, self._partition_key)

    @public  # type: ignore
    @property
    def has_asset_partitions(self) -> bool:
        if self._warn_on_step_context_use:
            warnings.warn(
                "You are using InputContext.upstream_output.has_asset_partitions"
                "This use on upstream_output is deprecated and will fail in the future"
                "Try to obtain what you need directly from InputContext"
                "For more details: https://github.com/dagster-io/dagster/issues/7900"
            )

        if self._step_context is not None:
            return self._step_context.has_asset_partitions_for_output(self.name)
        else:
            return False

    @public  # type: ignore
    @property
    def asset_partition_key(self) -> str:
        """The partition key for output asset.

        Raises an error if the output asset has no partitioning, or if the run covers a partition
        range for the output asset.
        """
        if self._warn_on_step_context_use:
            warnings.warn(
                "You are using InputContext.upstream_output.asset_partition_key"
                "This use on upstream_output is deprecated and will fail in the future"
                "Try to obtain what you need directly from InputContext"
                "For more details: https://github.com/dagster-io/dagster/issues/7900"
            )

        return self.step_context.asset_partition_key_for_output(self.name)

    @public  # type: ignore
    @property
    def asset_partition_key_range(self) -> PartitionKeyRange:
        """The partition key range for output asset.

        Raises an error if the output asset has no partitioning.
        """
        if self._warn_on_step_context_use:
            warnings.warn(
                "You are using InputContext.upstream_output.asset_partition_key_range"
                "This use on upstream_output is deprecated and will fail in the future"
                "Try to obtain what you need directly from InputContext"
                "For more details: https://github.com/dagster-io/dagster/issues/7900"
            )

        return self.step_context.asset_partition_key_range_for_output(self.name)

    @public  # type: ignore
    @property
    def asset_partition_keys(self) -> Sequence[str]:
        """The partition keys for the output asset.

        Raises an error if the output asset has no partitioning.
        """
        if self._warn_on_step_context_use:
            warnings.warn(
                "You are using InputContext.upstream_output.asset_partition_keys"
                "This use on upstream_output is deprecated and will fail in the future"
                "Try to obtain what you need directly from InputContext"
                "For more details: https://github.com/dagster-io/dagster/issues/7900"
            )

        return self.asset_partitions_def.get_partition_keys_in_range(
            self.step_context.asset_partition_key_range_for_output(self.name)
        )

    @public  # type: ignore
    @property
    def asset_partitions_time_window(self) -> TimeWindow:
        """The time window for the partitions of the output asset.

        Raises an error if either of the following are true:
        - The output asset has no partitioning.
        - The output asset is not partitioned with a TimeWindowPartitionsDefinition.
        """
        if self._warn_on_step_context_use:
            warnings.warn(
                "You are using InputContext.upstream_output.asset_partitions_time_window"
                "This use on upstream_output is deprecated and will fail in the future"
                "Try to obtain what you need directly from InputContext"
                "For more details: https://github.com/dagster-io/dagster/issues/7900"
            )

        return self.step_context.asset_partitions_time_window_for_output(self.name)

    def get_run_scoped_output_identifier(self) -> Sequence[str]:
        """Utility method to get a collection of identifiers that as a whole represent a unique
        step output.

        The unique identifier collection consists of

        - ``run_id``: the id of the run which generates the output.
            Note: This method also handles the re-execution memoization logic. If the step that
            generates the output is skipped in the re-execution, the ``run_id`` will be the id
            of its parent run.
        - ``step_key``: the key for a compute step.
        - ``name``: the name of the output. (default: 'result').

        Returns:
            Sequence[str, ...]: A list of identifiers, i.e. run id, step key, and output name
        """

        warnings.warn(
            "`OutputContext.get_run_scoped_output_identifier` is deprecated. Use "
            "`OutputContext.get_identifier` instead."
        )
        # if run_id is None and this is a re-execution, it means we failed to find its source run id
        check.invariant(
            self.run_id is not None,
            "Unable to find the run scoped output identifier: run_id is None on OutputContext.",
        )
        check.invariant(
            self.step_key is not None,
            "Unable to find the run scoped output identifier: step_key is None on OutputContext.",
        )
        check.invariant(
            self.name is not None,
            "Unable to find the run scoped output identifier: name is None on OutputContext.",
        )
        run_id = cast(str, self.run_id)
        step_key = cast(str, self.step_key)
        name = cast(str, self.name)

        if self.mapping_key:
            return [run_id, step_key, name, self.mapping_key]

        return [run_id, step_key, name]

    @public
    def get_identifier(self) -> Sequence[str]:
        """Utility method to get a collection of identifiers that as a whole represent a unique
        step output.

        If not using memoization, the unique identifier collection consists of

        - ``run_id``: the id of the run which generates the output.
            Note: This method also handles the re-execution memoization logic. If the step that
            generates the output is skipped in the re-execution, the ``run_id`` will be the id
            of its parent run.
        - ``step_key``: the key for a compute step.
        - ``name``: the name of the output. (default: 'result').

        If using memoization, the ``version`` corresponding to the step output is used in place of
        the ``run_id``.

        Returns:
            Sequence[str, ...]: A list of identifiers, i.e. (run_id or version), step_key, and output_name
        """
        version = self.version
        step_key = self.step_key
        name = self.name
        if version is not None:
            check.invariant(
                self.mapping_key is None,
                f"Mapping key and version both provided for output '{name}' of step '{step_key}'. "
                "Dynamic mapping is not supported when using versioning.",
            )
            identifier = ["versioned_outputs", version, step_key, name]
        else:
            run_id = self.run_id
            identifier = [run_id, step_key, name]
            if self.mapping_key:
                identifier.append(self.mapping_key)

        return identifier

    def get_output_identifier(self) -> Sequence[str]:
        warnings.warn(
            "`OutputContext.get_output_identifier` is deprecated. Use "
            "`OutputContext.get_identifier` instead."
        )

        return self.get_identifier()

    @public
    def get_asset_identifier(self) -> Sequence[str]:
        if self.asset_key is not None:
            if self.has_asset_partitions:
                return self.asset_key.path + [self.asset_partition_key]
            else:
                return self.asset_key.path
        else:
            check.failed("Can't get asset output identifier for an output with no asset key")

    def get_asset_output_identifier(self) -> Sequence[str]:
        warnings.warn(
            "`OutputContext.get_asset_output_identifier` is deprecated. Use "
            "`OutputContext.get_asset_identifier` instead."
        )

        return self.get_asset_identifier()

    @public
    def log_event(
        self, event: Union[AssetObservation, AssetMaterialization, Materialization]
    ) -> None:
        """Log an AssetMaterialization or AssetObservation from within the body of an io manager's `handle_output` method.

        Events logged with this method will appear in the event log.

        Args:
            event (Union[AssetMaterialization, Materialization, AssetObservation]): The event to log.

        Examples:

        .. code-block:: python

            from dagster import IOManager, AssetMaterialization

            class MyIOManager(IOManager):
                def handle_output(self, context, obj):
                    context.log_event(AssetMaterialization("foo"))
        """
        from dagster._core.events import DagsterEvent

        if isinstance(event, (AssetMaterialization, Materialization)):
            if self._step_context:
                self._events.append(
                    DagsterEvent.asset_materialization(
                        self._step_context,
                        event,
                        self._step_context.get_input_lineage(),
                    )
                )
            self._user_events.append(event)
        elif isinstance(event, AssetObservation):
            if self._step_context:
                self._events.append(DagsterEvent.asset_observation(self._step_context, event))
            self._user_events.append(event)
        else:
            check.failed("Unexpected event {event}".format(event=event))

    def consume_events(self) -> Iterator["DagsterEvent"]:
        """Pops and yields all user-generated events that have been recorded from this context.

        If consume_events has not yet been called, this will yield all logged events since the call to `handle_output`. If consume_events has been called, it will yield all events since the last time consume_events was called. Designed for internal use. Users should never need to invoke this method.
        """

        events = self._events
        self._events = []
        yield from events

    def get_logged_events(
        self,
    ) -> Sequence[Union[AssetMaterialization, Materialization, AssetObservation]]:
        """Retrieve the list of user-generated events that were logged via the context.


        User-generated events that were yielded will not appear in this list.

        **Examples:**

        .. code-block:: python

            from dagster import IOManager, build_output_context, AssetMaterialization

            class MyIOManager(IOManager):
                def handle_output(self, context, obj):
                    ...

            def test_handle_output():
                mgr = MyIOManager()
                context = build_output_context()
                mgr.handle_output(context)
                all_user_events = context.get_logged_events()
                materializations = [event for event in all_user_events if isinstance(event, AssetMaterialization)]
                ...
        """

        return self._user_events

    @public
    def add_output_metadata(self, metadata: Mapping[str, RawMetadataValue]) -> None:
        """Add a dictionary of metadata to the handled output.

        Metadata entries added will show up in the HANDLED_OUTPUT and ASSET_MATERIALIZATION events for the run.

        Args:
            metadata (Mapping[str, RawMetadataValue]): A metadata dictionary to log

        Examples:

        .. code-block:: python

            from dagster import IOManager

            class MyIOManager(IOManager):
                def handle_output(self, context, obj):
                    context.add_output_metadata({"foo": "bar"})
        """
        from dagster._core.definitions.metadata import normalize_metadata

        self._metadata_entries = normalize_metadata(metadata, [])

    def get_logged_metadata_entries(
        self,
    ) -> Sequence[Union[MetadataEntry, PartitionMetadataEntry]]:
        """Get the list of metadata entries that have been logged for use with this output."""
        return self._metadata_entries or []

    def consume_logged_metadata_entries(
        self,
    ) -> Sequence[Union[MetadataEntry, PartitionMetadataEntry]]:
        """Pops and yields all user-generated metadata entries that have been recorded from this context.

        If consume_logged_metadata_entries has not yet been called, this will yield all logged events since the call to `handle_output`. If consume_logged_metadata_entries has been called, it will yield all events since the last time consume_logged_metadata_entries was called. Designed for internal use. Users should never need to invoke this method.
        """
        result = self._metadata_entries
        self._metadata_entries = []
        return result or []


def get_output_context(
    execution_plan: "ExecutionPlan",
    pipeline_def: "PipelineDefinition",
    resolved_run_config: "ResolvedRunConfig",
    step_output_handle: "StepOutputHandle",
    run_id: Optional[str],
    log_manager: Optional["DagsterLogManager"],
    step_context: Optional["StepExecutionContext"],
    resources: Optional["Resources"],
    version: Optional[str],
    warn_on_step_context_use: bool = False,
) -> "OutputContext":
    """
    Args:
        run_id (str): The run ID of the run that produced the output, not necessarily the run that
            the context will be used in.
    """

    step = execution_plan.get_step_by_key(step_output_handle.step_key)
    # get config
    solid_config = resolved_run_config.solids[step.solid_handle.to_string()]
    outputs_config = solid_config.outputs

    if outputs_config:
        output_config = outputs_config.get_output_manager_config(step_output_handle.output_name)
    else:
        output_config = None

    step_output = execution_plan.get_step_output(step_output_handle)
    output_def = pipeline_def.get_solid(step_output.solid_handle).output_def_named(step_output.name)

    io_manager_key = output_def.io_manager_key
    resource_config = resolved_run_config.resources[io_manager_key].config

    node_handle = execution_plan.get_step_by_key(step.key).solid_handle
    asset_info = pipeline_def.asset_layer.asset_info_for_output(
        node_handle=node_handle, output_name=step_output.name
    )

    if step_context:
        check.invariant(
            not resources,
            "Expected either resources or step context to be set, but "
            "received both. If step context is provided, resources for IO manager will be "
            "retrieved off of that.",
        )
        resources = build_resources_for_manager(io_manager_key, step_context)

    return OutputContext(
        step_key=step_output_handle.step_key,
        name=step_output_handle.output_name,
        pipeline_name=pipeline_def.name,
        run_id=run_id,
        metadata=output_def.metadata,
        mapping_key=step_output_handle.mapping_key,
        config=output_config,
        op_def=pipeline_def.get_solid(step.solid_handle).definition,
        dagster_type=output_def.dagster_type,
        log_manager=log_manager,
        version=version,
        step_context=step_context,
        resource_config=resource_config,
        resources=resources,
        asset_info=asset_info,
        warn_on_step_context_use=warn_on_step_context_use,
    )


def step_output_version(
    pipeline_def: "PipelineDefinition",
    execution_plan: "ExecutionPlan",
    resolved_run_config: "ResolvedRunConfig",
    step_output_handle: "StepOutputHandle",
) -> Optional[str]:
    from dagster._core.execution.resolve_versions import resolve_step_output_versions

    step_output_versions = resolve_step_output_versions(
        pipeline_def, execution_plan, resolved_run_config
    )
    return (
        step_output_versions[step_output_handle]
        if step_output_handle in step_output_versions
        else None
    )


def build_output_context(
    step_key: Optional[str] = None,
    name: Optional[str] = None,
    metadata: Optional[Mapping[str, RawMetadataValue]] = None,
    run_id: Optional[str] = None,
    mapping_key: Optional[str] = None,
    config: Optional[Any] = None,
    dagster_type: Optional["DagsterType"] = None,
    version: Optional[str] = None,
    resource_config: Optional[Mapping[str, object]] = None,
    resources: Optional[Mapping[str, object]] = None,
    op_def: Optional["OpDefinition"] = None,
    asset_key: Optional[Union[AssetKey, str]] = None,
    partition_key: Optional[str] = None,
) -> "OutputContext":
    """Builds output context from provided parameters.

    ``build_output_context`` can be used as either a function, or a context manager. If resources
    that are also context managers are provided, then ``build_output_context`` must be used as a
    context manager.

    Args:
        step_key (Optional[str]): The step_key for the compute step that produced the output.
        name (Optional[str]): The name of the output that produced the output.
        metadata (Optional[Mapping[str, Any]]): A dict of the metadata that is assigned to the
            OutputDefinition that produced the output.
        mapping_key (Optional[str]): The key that identifies a unique mapped output. None for regular outputs.
        config (Optional[Any]): The configuration for the output.
        dagster_type (Optional[DagsterType]): The type of this output.
        version (Optional[str]): (Experimental) The version of the output.
        resource_config (Optional[Mapping[str, Any]]): The resource config to make available from the
            input context. This usually corresponds to the config provided to the resource that
            loads the output manager.
        resources (Optional[Resources]): The resources to make available from the context.
            For a given key, you can provide either an actual instance of an object, or a resource
            definition.
        op_def (Optional[OpDefinition]): The definition of the op that produced the output.
        asset_key: Optional[Union[AssetKey, Sequence[str], str]]: The asset key corresponding to the
            output.
        partition_key: Optional[str]: String value representing partition key to execute with.

    Examples:

        .. code-block:: python

            build_output_context()

            with build_output_context(resources={"foo": context_manager_resource}) as context:
                do_something

    """
    from dagster._core.definitions import OpDefinition
    from dagster._core.execution.context_creation_pipeline import initialize_console_manager
    from dagster._core.types.dagster_type import DagsterType

    step_key = check.opt_str_param(step_key, "step_key")
    name = check.opt_str_param(name, "name")
    metadata = check.opt_dict_param(metadata, "metadata", key_type=str)
    run_id = check.opt_str_param(run_id, "run_id", default=RUN_ID_PLACEHOLDER)
    mapping_key = check.opt_str_param(mapping_key, "mapping_key")
    dagster_type = check.opt_inst_param(dagster_type, "dagster_type", DagsterType)
    version = check.opt_str_param(version, "version")
    resource_config = check.opt_dict_param(resource_config, "resource_config", key_type=str)
    resources = check.opt_dict_param(resources, "resources", key_type=str)
    op_def = check.opt_inst_param(op_def, "op_def", OpDefinition)
    asset_key = AssetKey.from_coerceable(asset_key) if asset_key else None
    partition_key = check.opt_str_param(partition_key, "partition_key")

    return OutputContext(
        step_key=step_key,
        name=name,
        pipeline_name=None,
        run_id=run_id,
        metadata=metadata,
        mapping_key=mapping_key,
        config=config,
        dagster_type=dagster_type,
        log_manager=initialize_console_manager(None),
        version=version,
        resource_config=resource_config,
        resources=resources,
        step_context=None,
        op_def=op_def,
        asset_info=AssetOutputInfo(key=asset_key) if asset_key else None,
        partition_key=partition_key,
    )
