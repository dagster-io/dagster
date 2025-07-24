from collections.abc import Iterable, Iterator, Mapping, Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Union

import dagster._check as check
from dagster._annotations import deprecated, deprecated_param, public
from dagster._core.definitions.events import AssetKey, AssetObservation, CoercibleToAssetKey
from dagster._core.definitions.metadata import ArbitraryMetadataMapping, MetadataValue
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._core.definitions.partitions.utils import TimeWindow
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.instance import DagsterInstance
from dagster._utils.warnings import normalize_renamed_param

if TYPE_CHECKING:
    from dagster._core.definitions import PartitionsDefinition
    from dagster._core.definitions.op_definition import OpDefinition
    from dagster._core.definitions.resource_definition import Resources
    from dagster._core.events import DagsterEvent
    from dagster._core.execution.context.output import OutputContext
    from dagster._core.execution.context.system import StepExecutionContext
    from dagster._core.log_manager import DagsterLogManager
    from dagster._core.types.dagster_type import DagsterType


@deprecated_param(
    param="metadata",
    breaking_version="2.0",
    additional_warn_text="Use `definition_metadata` instead.",
)
@public
class InputContext:
    """The ``context`` object available to the load_input method of :py:class:`InputManager`.

    Users should not instantiate this object directly. In order to construct
    an `InputContext` for testing an IO Manager's `load_input` method, use
    :py:func:`dagster.build_input_context`.

    Example:
        .. code-block:: python

            from dagster import IOManager, InputContext

            class MyIOManager(IOManager):
                def load_input(self, context: InputContext):
                    ...
    """

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        job_name: Optional[str] = None,
        op_def: Optional["OpDefinition"] = None,
        config: Optional[Any] = None,
        definition_metadata: Optional[ArbitraryMetadataMapping] = None,
        upstream_output: Optional["OutputContext"] = None,
        dagster_type: Optional["DagsterType"] = None,
        log_manager: Optional["DagsterLogManager"] = None,
        resource_config: Optional[Mapping[str, Any]] = None,
        resources: Optional[Union["Resources", Mapping[str, Any]]] = None,
        step_context: Optional["StepExecutionContext"] = None,
        asset_key: Optional[AssetKey] = None,
        partition_key: Optional[str] = None,
        asset_partitions_subset: Optional[PartitionsSubset] = None,
        asset_partitions_def: Optional["PartitionsDefinition"] = None,
        instance: Optional[DagsterInstance] = None,
        # deprecated
        metadata: Optional[ArbitraryMetadataMapping] = None,
    ):
        from dagster._core.definitions.resource_definition import IContainsGenerator, Resources
        from dagster._core.execution.build_resources import build_resources

        self._name = name
        self._job_name = job_name
        self._op_def = op_def
        self._config = config
        self._definition_metadata = (
            normalize_renamed_param(
                definition_metadata, "definition_metadata", metadata, "metadata"
            )
            or {}
        )
        self._user_generated_metadata = {}
        self._upstream_output = upstream_output
        self._dagster_type = dagster_type
        self._log = log_manager
        self._resource_config = resource_config
        self._step_context = step_context
        self._asset_key = asset_key
        if self._step_context and self._step_context.has_partition_key:
            self._partition_key: Optional[str] = self._step_context.partition_key
        else:
            self._partition_key = partition_key

        self._asset_partitions_subset = asset_partitions_subset
        self._asset_partitions_def = asset_partitions_def

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

        self._events: list[DagsterEvent] = []
        self._observations: list[AssetObservation] = []
        self._instance = instance

    def __enter__(self):
        if self._resources_cm:
            self._cm_scope_entered = True
        return self

    def __exit__(self, *exc):
        if self._resources_cm:
            self._resources_cm.__exit__(*exc)

    def __del__(self):
        if self._resources_cm and self._resources_contain_cm and not self._cm_scope_entered:
            self._resources_cm.__exit__(None, None, None)

    @property
    def instance(self) -> DagsterInstance:
        if self._instance is None:
            raise DagsterInvariantViolationError(
                "Attempting to access instance, "
                "but it was not provided when constructing the InputContext"
            )
        return self._instance

    @public
    @property
    def has_input_name(self) -> bool:
        """If we're the InputContext is being used to load the result of a run from outside the run,
        then it won't have an input name.
        """
        return self._name is not None

    @public
    @property
    def name(self) -> str:
        """The name of the input that we're loading."""
        if self._name is None:
            raise DagsterInvariantViolationError(
                "Attempting to access name, "
                "but it was not provided when constructing the InputContext"
            )

        return self._name

    @property
    def job_name(self) -> str:
        if self._job_name is None:
            raise DagsterInvariantViolationError(
                "Attempting to access job_name, "
                "but it was not provided when constructing the InputContext"
            )
        return self._job_name

    @public
    @property
    def op_def(self) -> "OpDefinition":
        """The definition of the op that's loading the input."""
        if self._op_def is None:
            raise DagsterInvariantViolationError(
                "Attempting to access op_def, "
                "but it was not provided when constructing the InputContext"
            )

        return self._op_def

    @public
    @property
    def config(self) -> Any:
        """The config attached to the input that we're loading."""
        return self._config

    @deprecated(breaking_version="2.0.0", additional_warn_text="Use definition_metadata instead")
    @public
    @property
    def metadata(self) -> Optional[ArbitraryMetadataMapping]:
        """Deprecated: Use definitiion_metadata instead."""
        return self._definition_metadata

    @public
    @property
    def definition_metadata(self) -> ArbitraryMetadataMapping:
        """A dict of metadata that is assigned to the InputDefinition that we're loading.
        This property only contains metadata passed in explicitly with :py:class:`AssetIn`
        or :py:class:`In`. To access metadata of an upstream asset or op definition,
        use the definition_metadata in :py:attr:`.InputContext.upstream_output`.
        """
        return self._definition_metadata

    @public
    @property
    def upstream_output(self) -> Optional["OutputContext"]:
        """Info about the output that produced the object we're loading."""
        return self._upstream_output

    @public
    @property
    def dagster_type(self) -> "DagsterType":
        """The type of this input.
        Dagster types do not propagate from an upstream output to downstream inputs,
        and this property only captures type information for the input that is either
        passed in explicitly with :py:class:`AssetIn` or :py:class:`In`, or can be
        infered from type hints. For an asset input, the Dagster type from the upstream
        asset definition is ignored.
        """
        if self._dagster_type is None:
            raise DagsterInvariantViolationError(
                "Attempting to access dagster_type, "
                "but it was not provided when constructing the InputContext"
            )

        return self._dagster_type

    @public
    @property
    def log(self) -> "DagsterLogManager":
        """The log manager to use for this input."""
        if self._log is None:
            raise DagsterInvariantViolationError(
                "Attempting to access log, "
                "but it was not provided when constructing the InputContext"
            )

        return self._log

    @public
    @property
    def resource_config(self) -> Optional[Mapping[str, Any]]:
        """The config associated with the resource that initializes the InputManager."""
        return self._resource_config

    @public
    @property
    def resources(self) -> Any:
        """The resources required by the resource that initializes the
        input manager. If using the :py:func:`@input_manager` decorator, these resources
        correspond to those requested with the `required_resource_keys` parameter.
        """
        if self._resources is None:
            raise DagsterInvariantViolationError(
                "Attempting to access resources, "
                "but it was not provided when constructing the InputContext"
            )

        if self._resources_cm and self._resources_contain_cm and not self._cm_scope_entered:
            raise DagsterInvariantViolationError(
                "At least one provided resource is a generator, but attempting to access "
                "resources outside of context manager scope. You can use the following syntax to "
                "open a context manager: `with build_input_context(...) as context:`"
            )
        return self._resources

    @public
    @property
    def has_asset_key(self) -> bool:
        """Returns True if an asset is being loaded as input, otherwise returns False. A return value of False
        indicates that an output from an op is being loaded as the input.
        """
        return self._asset_key is not None

    @public
    @property
    def asset_key(self) -> AssetKey:
        """The ``AssetKey`` of the asset that is being loaded as an input."""
        if self._asset_key is None:
            raise DagsterInvariantViolationError(
                "Attempting to access asset_key, but no asset is associated with this input"
            )

        return self._asset_key

    @public
    @property
    def asset_partitions_def(self) -> "PartitionsDefinition":
        """The PartitionsDefinition on the upstream asset corresponding to this input."""
        if self._asset_partitions_def is None:
            if self.asset_key:
                raise DagsterInvariantViolationError(
                    f"Attempting to access partitions def for asset {self.asset_key}, but it is not"
                    " partitioned"
                )
            else:
                raise DagsterInvariantViolationError(
                    "Attempting to access partitions def for asset, but input does not correspond"
                    " to an asset"
                )

        return self._asset_partitions_def

    @property
    def step_context(self) -> "StepExecutionContext":
        if self._step_context is None:
            raise DagsterInvariantViolationError(
                "Attempting to access step_context, "
                "but it was not provided when constructing the InputContext"
            )

        return self._step_context

    @public
    @property
    def has_partition_key(self) -> bool:
        """Whether the current run is a partitioned run."""
        return self._partition_key is not None

    @public
    @property
    def partition_key(self) -> str:
        """The partition key for the current run.

        Raises an error if the current run is not a partitioned run.
        """
        if self._partition_key is None:
            check.failed(
                "Tried to access partition_key on a non-partitioned run.",
            )

        return self._partition_key

    @public
    @property
    def has_asset_partitions(self) -> bool:
        """Returns True if the asset being loaded as input is partitioned."""
        return self._asset_partitions_subset is not None

    @public
    @property
    def asset_partition_key(self) -> str:
        """The partition key for input asset.

        Raises an error if the input asset has no partitioning, or if the run covers a partition
        range for the input asset.
        """
        subset = self._asset_partitions_subset

        if subset is None:
            check.failed("The input does not correspond to a partitioned asset.")

        partition_keys = list(subset.get_partition_keys())
        if len(partition_keys) == 1:
            return partition_keys[0]
        else:
            check.failed(
                f"Tried to access partition key for asset '{self.asset_key}', "
                f"but the number of input partitions != 1: '{subset}'."
            )

    @public
    @property
    def asset_partition_key_range(self) -> PartitionKeyRange:
        """The partition key range for input asset.

        Raises an error if the input asset has no partitioning.
        """
        subset = self._asset_partitions_subset

        if subset is None:
            check.failed(
                "Tried to access asset_partition_key_range, but the asset is not partitioned.",
            )

        partition_key_ranges = subset.get_partition_key_ranges(self.asset_partitions_def)
        if len(partition_key_ranges) != 1:
            check.failed(
                "Tried to access asset_partition_key_range, but there are "
                f"({len(partition_key_ranges)}) key ranges associated with this input.",
            )

        return partition_key_ranges[0]

    @public
    @property
    def asset_partition_keys(self) -> Sequence[str]:
        """The partition keys for input asset.

        Raises an error if the input asset has no partitioning.
        """
        if self._asset_partitions_subset is None:
            check.failed(
                "Tried to access asset_partition_keys, but the asset is not partitioned.",
            )

        return list(self._asset_partitions_subset.get_partition_keys())

    @public
    @property
    def asset_partitions_time_window(self) -> TimeWindow:
        """The time window for the partitions of the input asset.

        Raises an error if either of the following are true:
        - The input asset has no partitioning.
        - The input asset is not partitioned with a TimeWindowPartitionsDefinition or a
        MultiPartitionsDefinition with one time-partitioned dimension.
        """
        subset = self._asset_partitions_subset

        if subset is None:
            check.failed(
                "Tried to access asset_partitions_time_window, but the asset is not partitioned.",
            )

        return self.step_context.asset_partitions_time_window_for_input(self.name)

    @public
    def get_identifier(self) -> Sequence[str]:
        """Utility method to get a collection of identifiers that as a whole represent a unique
        step input.

        If not using memoization, the unique identifier collection consists of

        - ``run_id``: the id of the run which generates the input.
            Note: This method also handles the re-execution memoization logic. If the step that
            generates the input is skipped in the re-execution, the ``run_id`` will be the id
            of its parent run.
        - ``step_key``: the key for a compute step.
        - ``name``: the name of the output. (default: 'result').

        If using memoization, the ``version`` corresponding to the step output is used in place of
        the ``run_id``.

        Returns:
            List[str, ...]: A list of identifiers, i.e. (run_id or version), step_key, and output_name
        """
        if self.upstream_output is None:
            raise DagsterInvariantViolationError(
                "InputContext.upstream_output not defined. Cannot compute an identifier"
            )

        return self.upstream_output.get_identifier()

    @public
    def get_asset_identifier(self) -> Sequence[str]:
        """The sequence of strings making up the AssetKey for the asset being loaded as an input.
        If the asset is partitioned, the identifier contains the partition key as the final element in the
        sequence. For example, for the asset key ``AssetKey(["foo", "bar", "baz"])``, materialized with
        partition key "2023-06-01", ``get_asset_identifier`` will return ``["foo", "bar", "baz", "2023-06-01"]``.
        """
        if self.asset_key is not None:
            if self.has_asset_partitions:
                return [*self.asset_key.path, self.asset_partition_key]
            else:
                return self.asset_key.path
        else:
            check.failed("Can't get asset identifier for an input with no asset key")

    def consume_events(self) -> Iterator["DagsterEvent"]:
        """Pops and yields all user-generated events that have been recorded from this context.

        If consume_events has not yet been called, this will yield all logged events since the call to `handle_input`. If consume_events has been called, it will yield all events since the last time consume_events was called. Designed for internal use. Users should never need to invoke this method.
        """
        events = self._events
        self._events = []
        yield from events

    def add_input_metadata(
        self,
        metadata: Mapping[str, Any],
        description: Optional[str] = None,
    ) -> None:
        """Accepts a dictionary of metadata. Metadata entries will appear on the LOADED_INPUT event.
        If the input is an asset, metadata will be attached to an asset observation.

        The asset observation will be yielded from the run and appear in the event log.
        Only valid if the context has an asset key.
        """
        from dagster._core.definitions.metadata import normalize_metadata
        from dagster._core.events import DagsterEvent

        metadata = check.mapping_param(metadata, "metadata", key_type=str)
        self._user_generated_metadata = {
            **self._user_generated_metadata,
            **normalize_metadata(metadata),
        }
        if self.has_asset_key:
            check.opt_str_param(description, "description")

            observation = AssetObservation(
                asset_key=self.asset_key,
                description=description,
                partition=self.asset_partition_key if self.has_asset_partitions else None,
                metadata=metadata,
            )
            self._observations.append(observation)
            if self._step_context:
                self._events.append(DagsterEvent.asset_observation(self._step_context, observation))

    def get_observations(
        self,
    ) -> Sequence[AssetObservation]:
        """Retrieve the list of user-generated asset observations that were observed via the context.

        User-generated events that were yielded will not appear in this list.

        **Examples:**

        .. code-block:: python

            from dagster import IOManager, build_input_context, AssetObservation

            class MyIOManager(IOManager):
                def load_input(self, context, obj):
                    ...

            def test_load_input():
                mgr = MyIOManager()
                context = build_input_context()
                mgr.load_input(context)
                observations = context.get_observations()
                ...
        """
        return self._observations

    def consume_logged_metadata(self) -> Mapping[str, MetadataValue]:
        """Pops and yields all user-generated metadata entries that have been recorded from this context.

        If consume_logged_metadata has not yet been called, this will yield all logged events since
        the call to `load_input`. If consume_logged_metadata has been called, it will yield all
        events since the last time consume_logged_metadata was called. Designed for internal
        use. Users should never need to invoke this method.
        """
        result = self._user_generated_metadata
        self._user_generated_metadata = {}
        return result


@public
@deprecated_param(
    param="metadata",
    breaking_version="2.0",
    additional_warn_text="Use `definition_metadata` instead.",
)
def build_input_context(
    name: Optional[str] = None,
    config: Optional[Any] = None,
    definition_metadata: Optional[ArbitraryMetadataMapping] = None,
    upstream_output: Optional["OutputContext"] = None,
    dagster_type: Optional["DagsterType"] = None,
    resource_config: Optional[Mapping[str, Any]] = None,
    resources: Optional[Mapping[str, Any]] = None,
    op_def: Optional["OpDefinition"] = None,
    step_context: Optional["StepExecutionContext"] = None,
    asset_key: Optional[CoercibleToAssetKey] = None,
    partition_key: Optional[str] = None,
    asset_partition_key_range: Optional[PartitionKeyRange] = None,
    asset_partitions_def: Optional["PartitionsDefinition"] = None,
    instance: Optional[DagsterInstance] = None,
    # deprecated
    metadata: Optional[ArbitraryMetadataMapping] = None,
) -> "InputContext":
    """Builds input context from provided parameters.

    ``build_input_context`` can be used as either a function, or a context manager. If resources
    that are also context managers are provided, then ``build_input_context`` must be used as a
    context manager.

    Args:
        name (Optional[str]): The name of the input that we're loading.
        config (Optional[Any]): The config attached to the input that we're loading.
        definition_metadata (Optional[Dict[str, Any]]): A dict of metadata that is assigned to the
            InputDefinition that we're loading for.
        upstream_output (Optional[OutputContext]): Info about the output that produced the object
            we're loading.
        dagster_type (Optional[DagsterType]): The type of this input.
        resource_config (Optional[Dict[str, Any]]): The resource config to make available from the
            input context. This usually corresponds to the config provided to the resource that
            loads the input manager.
        resources (Optional[Dict[str, Any]]): The resources to make available from the context.
            For a given key, you can provide either an actual instance of an object, or a resource
            definition.
        asset_key (Optional[Union[AssetKey, Sequence[str], str]]): The asset key attached to the InputDefinition.
        op_def (Optional[OpDefinition]): The definition of the op that's loading the input.
        step_context (Optional[StepExecutionContext]): For internal use.
        partition_key (Optional[str]): String value representing partition key to execute with.
        asset_partition_key_range (Optional[PartitionKeyRange]): The range of asset partition keys
            to load.
        asset_partitions_def: Optional[PartitionsDefinition]: The PartitionsDefinition of the asset
            being loaded.

    Examples:
        .. code-block:: python

            build_input_context()

            with build_input_context(resources={"foo": context_manager_resource}) as context:
                do_something
    """
    from dagster._core.definitions import OpDefinition, PartitionsDefinition
    from dagster._core.execution.context.output import OutputContext
    from dagster._core.execution.context.system import StepExecutionContext
    from dagster._core.execution.context_creation_job import initialize_console_manager
    from dagster._core.types.dagster_type import DagsterType

    name = check.opt_str_param(name, "name")
    check.opt_mapping_param(definition_metadata, "definition_metadata", key_type=str)
    check.opt_mapping_param(metadata, "metadata", key_type=str)
    definition_metadata = normalize_renamed_param(
        definition_metadata,
        "definition_metadata",
        metadata,
        "metadata",
    )
    upstream_output = check.opt_inst_param(upstream_output, "upstream_output", OutputContext)
    dagster_type = check.opt_inst_param(dagster_type, "dagster_type", DagsterType)
    resource_config = check.opt_mapping_param(resource_config, "resource_config", key_type=str)
    resources = check.opt_mapping_param(resources, "resources", key_type=str)
    op_def = check.opt_inst_param(op_def, "op_def", OpDefinition)
    step_context = check.opt_inst_param(step_context, "step_context", StepExecutionContext)
    asset_key = AssetKey.from_coercible(asset_key) if asset_key else None
    partition_key = check.opt_str_param(partition_key, "partition_key")
    asset_partition_key_range = check.opt_inst_param(
        asset_partition_key_range, "asset_partition_key_range", PartitionKeyRange
    )
    asset_partitions_def = check.opt_inst_param(
        asset_partitions_def, "asset_partitions_def", PartitionsDefinition
    )
    if asset_partitions_def and asset_partition_key_range:
        with partition_loading_context(dynamic_partitions_store=instance):
            asset_partitions_subset = asset_partitions_def.empty_subset().with_partition_key_range(
                asset_partitions_def, asset_partition_key_range
            )
    elif asset_partition_key_range:
        asset_partitions_subset = KeyRangeNoPartitionsDefPartitionsSubset(asset_partition_key_range)
    else:
        asset_partitions_subset = None

    return InputContext(
        name=name,
        job_name=None,
        config=config,
        definition_metadata=definition_metadata,
        upstream_output=upstream_output,
        dagster_type=dagster_type,
        log_manager=initialize_console_manager(None),
        resource_config=resource_config,
        resources=resources,
        step_context=step_context,
        op_def=op_def,
        asset_key=asset_key,
        partition_key=partition_key,
        asset_partitions_subset=asset_partitions_subset,
        asset_partitions_def=asset_partitions_def,
        instance=instance,
    )


class KeyRangeNoPartitionsDefPartitionsSubset(PartitionsSubset):
    """For build_input_context when no PartitionsDefinition has been provided."""

    def __init__(self, key_range: PartitionKeyRange):
        self._key_range = key_range

    def get_partition_keys_not_in_subset(
        self, partitions_def: "PartitionsDefinition"
    ) -> Iterable[str]:
        raise NotImplementedError()

    def get_partition_keys(self, current_time: Optional[datetime] = None) -> Iterable[str]:
        if self._key_range.start == self._key_range.end:
            return self._key_range.start
        else:
            raise NotImplementedError()

    def get_partition_key_ranges(
        self, partitions_def: "PartitionsDefinition"
    ) -> Sequence[PartitionKeyRange]:
        return [self._key_range]

    def with_partition_keys(self, partition_keys: Iterable[str]) -> "PartitionsSubset":
        raise NotImplementedError()

    def with_partition_key_range(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, partition_key_range: PartitionKeyRange
    ) -> "PartitionsSubset":
        raise NotImplementedError()

    def serialize(self) -> str:
        raise NotImplementedError()

    @property
    def partitions_def(self) -> Optional["PartitionsDefinition"]:
        raise NotImplementedError()

    def __len__(self) -> int:
        raise NotImplementedError()

    def __contains__(self, value) -> bool:
        raise NotImplementedError()

    @classmethod
    def from_serialized(
        cls, partitions_def: "PartitionsDefinition", serialized: str
    ) -> "PartitionsSubset":
        raise NotImplementedError()

    @classmethod
    def can_deserialize(
        cls,
        partitions_def: "PartitionsDefinition",
        serialized: str,
        serialized_partitions_def_unique_id: Optional[str],
        serialized_partitions_def_class_name: Optional[str],
    ) -> bool:
        raise NotImplementedError()

    def empty_subset(self) -> "PartitionsSubset":
        raise NotImplementedError()

    @classmethod
    def create_empty_subset(
        cls, partitions_def: Optional["PartitionsDefinition"] = None
    ) -> "PartitionsSubset":
        raise NotImplementedError()
