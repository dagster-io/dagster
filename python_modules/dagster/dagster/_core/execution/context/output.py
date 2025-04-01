import warnings
from collections.abc import Iterator, Mapping, Sequence
from typing import TYPE_CHECKING, Any, ContextManager, Optional, Union, cast  # noqa: UP035

import dagster._check as check
from dagster._annotations import deprecated, deprecated_param, public
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.events import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    CoercibleToAssetKey,
)
from dagster._core.definitions.metadata import (
    ArbitraryMetadataMapping,
    MetadataValue,
    RawMetadataValue,
)
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.errors import DagsterInvalidMetadata, DagsterInvariantViolationError
from dagster._core.execution.plan.utils import build_resources_for_manager
from dagster._utils.warnings import normalize_renamed_param

if TYPE_CHECKING:
    from dagster._core.definitions import JobDefinition, PartitionsDefinition
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


@deprecated_param(
    param="metadata",
    breaking_version="2.0",
    additional_warn_text="Use `definition_metadata` instead.",
)
class OutputContext:
    """The context object that is available to the `handle_output` method of an :py:class:`IOManager`.

    Users should not instantiate this object directly. To construct an
    `OutputContext` for testing an IO Manager's `handle_output` method, use
    :py:func:`dagster.build_output_context`.

    Example:
        .. code-block:: python

            from dagster import IOManager, OutputContext

            class MyIOManager(IOManager):
                def handle_output(self, context: OutputContext, obj):
                    ...
    """

    _step_key: Optional[str]
    _name: Optional[str]
    _job_name: Optional[str]
    _run_id: Optional[str]
    _definition_metadata: ArbitraryMetadataMapping
    _output_metadata: ArbitraryMetadataMapping
    _user_generated_metadata: Mapping[str, MetadataValue]
    _mapping_key: Optional[str]
    _config: object
    _op_def: Optional["OpDefinition"]
    _dagster_type: Optional["DagsterType"]
    _log: Optional["DagsterLogManager"]
    _version: Optional[str]
    _resource_config: Optional[Mapping[str, object]]
    _step_context: Optional["StepExecutionContext"]
    _asset_key: Optional[AssetKey]
    _warn_on_step_context_use: bool
    _resources: Optional["Resources"]
    _resources_cm: Optional[ContextManager["Resources"]]
    _resources_contain_cm: Optional[bool]
    _cm_scope_entered: Optional[bool]
    _events: list["DagsterEvent"]
    _user_events: list[Union[AssetMaterialization, AssetObservation]]

    def __init__(
        self,
        step_key: Optional[str] = None,
        name: Optional[str] = None,
        job_name: Optional[str] = None,
        run_id: Optional[str] = None,
        definition_metadata: Optional[ArbitraryMetadataMapping] = None,
        mapping_key: Optional[str] = None,
        config: object = None,
        dagster_type: Optional["DagsterType"] = None,
        log_manager: Optional["DagsterLogManager"] = None,
        version: Optional[str] = None,
        resource_config: Optional[Mapping[str, object]] = None,
        resources: Optional[Union["Resources", Mapping[str, object]]] = None,
        step_context: Optional["StepExecutionContext"] = None,
        op_def: Optional["OpDefinition"] = None,
        asset_key: Optional[AssetKey] = None,
        warn_on_step_context_use: bool = False,
        partition_key: Optional[str] = None,
        output_metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        # deprecated
        metadata: Optional[ArbitraryMetadataMapping] = None,
    ):
        from dagster._core.definitions.resource_definition import IContainsGenerator, Resources
        from dagster._core.execution.build_resources import build_resources

        self._step_key = step_key
        self._name = name
        self._job_name = job_name
        self._run_id = run_id
        normalized_metadata = normalize_renamed_param(
            definition_metadata, "definition_metadata", metadata, "metadata"
        )
        self._definition_metadata = normalized_metadata or {}
        self._output_metadata = output_metadata or {}
        self._mapping_key = mapping_key
        self._config = config
        self._op_def = op_def
        self._dagster_type = dagster_type
        self._log = log_manager
        self._version = version
        self._resource_config = resource_config
        self._step_context = step_context
        self._asset_key = asset_key
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
                check.opt_mapping_param(resources, "resources", key_type=str)
            )
            self._resources = self._resources_cm.__enter__()
            self._resources_contain_cm = isinstance(self._resources, IContainsGenerator)
            self._cm_scope_entered = False

        self._events = []
        self._user_events = []
        self._user_generated_metadata = {}

    def __enter__(self):
        if self._resources_cm:
            self._cm_scope_entered = True
        return self

    def __exit__(self, *exc):
        if self._resources_cm:
            self._resources_cm.__exit__(*exc)

    def __del__(self):
        if (
            hasattr(self, "_resources_cm")
            and self._resources_cm
            and self._resources_contain_cm
            and not self._cm_scope_entered
        ):
            self._resources_cm.__exit__(None, None, None)

    @public
    @property
    def step_key(self) -> str:
        """The step_key for the compute step that produced the output."""
        if self._step_key is None:
            raise DagsterInvariantViolationError(
                "Attempting to access step_key, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._step_key

    @public
    @property
    def name(self) -> str:
        """The name of the output that produced the output."""
        if self._name is None:
            raise DagsterInvariantViolationError(
                "Attempting to access name, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._name

    @property
    def job_name(self) -> str:
        if self._job_name is None:
            raise DagsterInvariantViolationError(
                "Attempting to access pipeline_name, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._job_name

    @public
    @property
    def run_id(self) -> str:
        """The id of the run that produced the output."""
        if self._run_id is None:
            raise DagsterInvariantViolationError(
                "Attempting to access run_id, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._run_id

    @deprecated(breaking_version="2.0.0", additional_warn_text="Use definition_metadata instead")
    @public
    @property
    def metadata(self) -> Optional[ArbitraryMetadataMapping]:
        """Deprecated: used definition_metadata instead."""
        return self._definition_metadata

    @public
    @property
    def definition_metadata(self) -> ArbitraryMetadataMapping:
        """A dict of the metadata that is assigned to the OutputDefinition that produced
        the output. Metadata is assigned to an OutputDefinition either directly on the OutputDefinition
        or in the @asset decorator.
        """
        return self._definition_metadata

    @public
    @property
    def output_metadata(self) -> ArbitraryMetadataMapping:
        """A dict of the metadata that is assigned to the output at execution time."""
        if self._warn_on_step_context_use:
            warnings.warn(
                "You are using InputContext.upstream_output.output_metadata."
                "Output metadata is not available when accessed from the InputContext."
                "https://github.com/dagster-io/dagster/issues/20094"
            )
            return {}

        return self._output_metadata

    @public
    @property
    def mapping_key(self) -> Optional[str]:
        """The key that identifies a unique mapped output. None for regular outputs."""
        return self._mapping_key

    @public
    @property
    def config(self) -> Any:
        """The configuration for the output."""
        return self._config

    @public
    @property
    def op_def(self) -> "OpDefinition":
        """The definition of the op that produced the output."""
        from dagster._core.definitions import OpDefinition

        if self._op_def is None:
            raise DagsterInvariantViolationError(
                "Attempting to access op_def, "
                "but it was not provided when constructing the OutputContext"
            )

        return cast(OpDefinition, self._op_def)

    @public
    @property
    def dagster_type(self) -> "DagsterType":
        """The type of this output."""
        if self._dagster_type is None:
            raise DagsterInvariantViolationError(
                "Attempting to access dagster_type, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._dagster_type

    @public
    @property
    def log(self) -> "DagsterLogManager":
        """The log manager to use for this output."""
        if self._log is None:
            raise DagsterInvariantViolationError(
                "Attempting to access log, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._log

    @public
    @property
    def version(self) -> Optional[str]:
        """The version of the output."""
        return self._version

    @public
    @property
    def resource_config(self) -> Optional[Mapping[str, object]]:
        """The config associated with the resource that initializes the InputManager."""
        return self._resource_config

    @public
    @property
    def resources(self) -> Any:
        """The resources required by the output manager, specified by the `required_resource_keys`
        parameter.
        """
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

    @public
    @property
    def has_asset_key(self) -> bool:
        """Returns True if an asset is being stored, otherwise returns False. A return value of False
        indicates that an output from an op is being stored.
        """
        return self._asset_key is not None

    @public
    @property
    def asset_key(self) -> AssetKey:
        """The ``AssetKey`` of the asset that is being stored as an output."""
        if self._asset_key is None:
            raise DagsterInvariantViolationError(
                "Attempting to access asset_key, "
                "but it was not provided when constructing the OutputContext"
            )

        return self._asset_key

    @public
    @property
    def asset_partitions_def(self) -> "PartitionsDefinition":
        """The PartitionsDefinition on the asset corresponding to this output."""
        asset_key = self.asset_key
        result = self.step_context.job_def.asset_layer.get(asset_key).partitions_def
        if result is None:
            raise DagsterInvariantViolationError(
                f"Attempting to access partitions def for asset {asset_key}, but it is not"
                " partitioned"
            )

        return result

    @public
    @property
    def asset_spec(self) -> AssetSpec:
        """The ``AssetSpec`` that is being stored as an output."""
        asset_key = self.asset_key
        return self.step_context.job_def.asset_layer.get(asset_key).to_asset_spec()

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

    @public
    @property
    def has_partition_key(self) -> bool:
        """Whether the current run is a partitioned run."""
        if self._warn_on_step_context_use:
            warnings.warn(
                "You are using InputContext.upstream_output.has_partition_key"
                "This use on upstream_output is deprecated and will fail in the future"
                "Try to obtain what you need directly from InputContext"
                "For more details: https://github.com/dagster-io/dagster/issues/7900"
            )

        return self._partition_key is not None

    @public
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

        if self._partition_key is None:
            check.failed(
                "Tried to access partition_key on a non-partitioned run.",
            )

        return self._partition_key

    @public
    @property
    def has_asset_partitions(self) -> bool:
        """Returns True if the asset being stored is partitioned."""
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

    @public
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

    @public
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

    @public
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
            self.step_context.asset_partition_key_range_for_output(self.name),
            dynamic_partitions_store=self.step_context.instance,
        )

    @public
    @property
    def asset_partitions_time_window(self) -> TimeWindow:
        """The time window for the partitions of the output asset.

        Raises an error if either of the following are true:
        - The output asset has no partitioning.
        - The output asset is not partitioned with a TimeWindowPartitionsDefinition or a
        MultiPartitionsDefinition with one time-partitioned dimension.
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
                f"Mapping key and version both provided for output '{name}' of step"
                f" '{step_key}'. Dynamic mapping is not supported when using versioning.",
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
        """The sequence of strings making up the AssetKey for the asset being stored as an output.
        If the asset is partitioned, the identifier contains the partition key as the final element in the
        sequence. For example, for the asset key ``AssetKey(["foo", "bar", "baz"])`` materialized with
        partition key "2023-06-01", ``get_asset_identifier`` will return ``["foo", "bar", "baz", "2023-06-01"]``.
        """
        if self.asset_key is not None:
            if self.has_asset_partitions:
                return [*self.asset_key.path, self.asset_partition_key]
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
    def log_event(self, event: Union[AssetObservation, AssetMaterialization]) -> None:
        """Log an AssetMaterialization or AssetObservation from within the body of an io manager's `handle_output` method.

        Events logged with this method will appear in the event log.

        Args:
            event (Union[AssetMaterialization, AssetObservation]): The event to log.

        Examples:
            .. code-block:: python

                from dagster import IOManager, AssetMaterialization

                class MyIOManager(IOManager):
                    def handle_output(self, context, obj):
                        context.log_event(AssetMaterialization("foo"))
        """
        from dagster._core.events import DagsterEvent

        if isinstance(event, (AssetMaterialization)):
            if self._step_context:
                self._events.append(DagsterEvent.asset_materialization(self._step_context, event))
            self._user_events.append(event)
        elif isinstance(event, AssetObservation):
            if self._step_context:
                self._events.append(DagsterEvent.asset_observation(self._step_context, event))
            self._user_events.append(event)
        else:
            check.failed(f"Unexpected event {event}")

    def consume_events(self) -> Iterator["DagsterEvent"]:
        """Pops and yields all user-generated events that have been recorded from this context.

        If consume_events has not yet been called, this will yield all logged events since the call to `handle_output`. If consume_events has been called, it will yield all events since the last time consume_events was called. Designed for internal use. Users should never need to invoke this method.
        """
        events = self._events
        self._events = []
        yield from events

    def get_logged_events(
        self,
    ) -> Sequence[Union[AssetMaterialization, AssetObservation]]:
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

        overlapping_labels = set(self._user_generated_metadata.keys()) & metadata.keys()
        if overlapping_labels:
            raise DagsterInvalidMetadata(
                f"Tried to add metadata for key(s) that already have metadata: {overlapping_labels}"
            )

        self._user_generated_metadata = {
            **self._user_generated_metadata,
            **normalize_metadata(metadata),
        }

    def get_logged_metadata(
        self,
    ) -> Mapping[str, MetadataValue]:
        """Get the mapping of metadata entries that have been logged for use with this output."""
        return self._user_generated_metadata

    def consume_logged_metadata(
        self,
    ) -> Mapping[str, MetadataValue]:
        """Pops and yields all user-generated metadata entries that have been recorded from this context.

        If consume_logged_metadata has not yet been called, this will yield all logged events since
        the call to `handle_output`. If consume_logged_metadata has been called, it will yield all
        events since the last time consume_logged_metadata_entries was called. Designed for internal
        use. Users should never need to invoke this method.
        """
        result = self._user_generated_metadata
        self._user_generated_metadata = {}
        return result or {}


def get_output_context(
    execution_plan: "ExecutionPlan",
    job_def: "JobDefinition",
    resolved_run_config: "ResolvedRunConfig",
    step_output_handle: "StepOutputHandle",
    run_id: Optional[str],
    log_manager: Optional["DagsterLogManager"],
    step_context: Optional["StepExecutionContext"],
    resources: Optional["Resources"],
    version: Optional[str],
    warn_on_step_context_use: bool = False,
    output_metadata: Optional[Mapping[str, RawMetadataValue]] = None,
) -> "OutputContext":
    """Args:
    run_id (str): The run ID of the run that produced the output, not necessarily the run that
        the context will be used in.
    """
    step = execution_plan.get_step_by_key(step_output_handle.step_key)
    # get config
    op_config = resolved_run_config.ops[str(step.node_handle)]
    outputs_config = op_config.outputs

    if outputs_config:
        output_config = outputs_config.get_output_manager_config(step_output_handle.output_name)
    else:
        output_config = None

    step_output = execution_plan.get_step_output(step_output_handle)
    output_def = job_def.get_node(step_output.node_handle).output_def_named(step_output.name)

    io_manager_key = output_def.io_manager_key
    resource_config = resolved_run_config.resources[io_manager_key].config

    node_handle = execution_plan.get_step_by_key(step.key).node_handle
    asset_key = job_def.asset_layer.asset_key_for_output(
        node_handle=node_handle, output_name=step_output.name
    )
    if asset_key is not None:
        definition_metadata = job_def.asset_layer.get(asset_key).metadata or output_def.metadata
    else:
        definition_metadata = output_def.metadata

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
        job_name=job_def.name,
        run_id=run_id,
        definition_metadata=definition_metadata,
        mapping_key=step_output_handle.mapping_key,
        config=output_config,
        op_def=job_def.get_node(step.node_handle).definition,  # type: ignore  # (should be OpDefinition not NodeDefinition)
        dagster_type=output_def.dagster_type,
        log_manager=log_manager,
        version=version,
        step_context=step_context,
        resource_config=resource_config,
        resources=resources,
        asset_key=asset_key,
        warn_on_step_context_use=warn_on_step_context_use,
        output_metadata=output_metadata,
    )


@deprecated_param(
    param="metadata",
    breaking_version="2.0",
    additional_warn_text="Use `definition_metadata` instead.",
)
def build_output_context(
    step_key: Optional[str] = None,
    name: Optional[str] = None,
    definition_metadata: Optional[Mapping[str, RawMetadataValue]] = None,
    run_id: Optional[str] = None,
    mapping_key: Optional[str] = None,
    config: Optional[Any] = None,
    dagster_type: Optional["DagsterType"] = None,
    version: Optional[str] = None,
    resource_config: Optional[Mapping[str, object]] = None,
    resources: Optional[Mapping[str, object]] = None,
    op_def: Optional["OpDefinition"] = None,
    asset_key: Optional[CoercibleToAssetKey] = None,
    partition_key: Optional[str] = None,
    # deprecated
    metadata: Optional[Mapping[str, RawMetadataValue]] = None,
) -> "OutputContext":
    """Builds output context from provided parameters.

    ``build_output_context`` can be used as either a function, or a context manager. If resources
    that are also context managers are provided, then ``build_output_context`` must be used as a
    context manager.

    Args:
        step_key (Optional[str]): The step_key for the compute step that produced the output.
        name (Optional[str]): The name of the output that produced the output.
        definition_metadata (Optional[Mapping[str, Any]]): A dict of the metadata that is assigned to the
            OutputDefinition that produced the output.
        mapping_key (Optional[str]): The key that identifies a unique mapped output. None for regular outputs.
        config (Optional[Any]): The configuration for the output.
        dagster_type (Optional[DagsterType]): The type of this output.
        version (Optional[str]): The version of the output.
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
        metadata (Optional[Mapping[str, Any]]): Deprecated. Use definition_metadata instead.

    Examples:
        .. code-block:: python

            build_output_context()

            with build_output_context(resources={"foo": context_manager_resource}) as context:
                do_something

    """
    from dagster._core.definitions import OpDefinition
    from dagster._core.execution.context_creation_job import initialize_console_manager
    from dagster._core.types.dagster_type import DagsterType

    step_key = check.opt_str_param(step_key, "step_key")
    name = check.opt_str_param(name, "name")
    check.opt_mapping_param(definition_metadata, "definition_metadata", key_type=str)
    check.opt_mapping_param(metadata, "metadata", key_type=str)
    definition_metadata = normalize_renamed_param(
        definition_metadata,
        "definition_metadata",
        metadata,
        "metadata",
    )
    run_id = check.opt_str_param(run_id, "run_id", default=RUN_ID_PLACEHOLDER)
    mapping_key = check.opt_str_param(mapping_key, "mapping_key")
    dagster_type = check.opt_inst_param(dagster_type, "dagster_type", DagsterType)
    version = check.opt_str_param(version, "version")
    resource_config = check.opt_mapping_param(resource_config, "resource_config", key_type=str)
    resources = check.opt_mapping_param(resources, "resources", key_type=str)
    op_def = check.opt_inst_param(op_def, "op_def", OpDefinition)
    asset_key = AssetKey.from_coercible(asset_key) if asset_key else None
    partition_key = check.opt_str_param(partition_key, "partition_key")

    return OutputContext(
        step_key=step_key,
        name=name,
        job_name=None,
        run_id=run_id,
        definition_metadata=definition_metadata,
        mapping_key=mapping_key,
        config=config,
        dagster_type=dagster_type,
        log_manager=initialize_console_manager(None),
        version=version,
        resource_config=resource_config,
        resources=resources,
        step_context=None,
        op_def=op_def,
        asset_key=asset_key,
        partition_key=partition_key,
    )
