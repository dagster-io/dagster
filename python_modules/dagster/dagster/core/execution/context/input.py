from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union, cast

import dagster._check as check
from dagster.core.definitions.events import AssetKey, AssetObservation
from dagster.core.definitions.metadata import MetadataEntry, PartitionMetadataEntry
from dagster.core.definitions.op_definition import OpDefinition
from dagster.core.definitions.partition_key_range import PartitionKeyRange
from dagster.core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
)
from dagster.core.errors import DagsterInvariantViolationError

if TYPE_CHECKING:
    from dagster.core.definitions.resource_definition import Resources
    from dagster.core.definitions.solid_definition import SolidDefinition
    from dagster.core.events import DagsterEvent
    from dagster.core.execution.context.system import StepExecutionContext
    from dagster.core.log_manager import DagsterLogManager
    from dagster.core.types.dagster_type import DagsterType

    from .output import OutputContext


class InputContext:
    """
    The ``context`` object available to the load_input method of :py:class:`RootInputManager`.

    Attributes:
        name (Optional[str]): The name of the input that we're loading.
        pipeline_name (Optional[str]): The name of the pipeline.
        solid_def (Optional[SolidDefinition]): The definition of the solid that's loading the input.
        config (Optional[Any]): The config attached to the input that we're loading.
        metadata (Optional[Dict[str, Any]]): A dict of metadata that is assigned to the
            InputDefinition that we're loading for.
        upstream_output (Optional[OutputContext]): Info about the output that produced the object
            we're loading.
        dagster_type (Optional[DagsterType]): The type of this input.
        log (Optional[DagsterLogManager]): The log manager to use for this input.
        resource_config (Optional[Dict[str, Any]]): The config associated with the resource that
            initializes the RootInputManager.
        resources (Optional[Resources]): The resources required by the resource that initializes the
            input manager. If using the :py:func:`@root_input_manager` decorator, these resources
            correspond to those requested with the `required_resource_keys` parameter.
        op_def (Optional[OpDefinition]): The definition of the op that's loading the input.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        pipeline_name: Optional[str] = None,
        solid_def: Optional["SolidDefinition"] = None,
        config: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        upstream_output: Optional["OutputContext"] = None,
        dagster_type: Optional["DagsterType"] = None,
        log_manager: Optional["DagsterLogManager"] = None,
        resource_config: Optional[Dict[str, Any]] = None,
        resources: Optional[Union["Resources", Dict[str, Any]]] = None,
        step_context: Optional["StepExecutionContext"] = None,
        op_def: Optional["OpDefinition"] = None,
    ):
        from dagster.core.definitions.resource_definition import IContainsGenerator, Resources
        from dagster.core.execution.build_resources import build_resources

        self._name = name
        self._pipeline_name = pipeline_name
        check.invariant(
            solid_def is None or op_def is None, "Can't provide both a solid_def and an op_def arg"
        )
        self._solid_def = solid_def or op_def
        self._config = config
        self._metadata = metadata
        self._upstream_output = upstream_output
        self._dagster_type = dagster_type
        self._log = log_manager
        self._resource_config = resource_config
        self._step_context = step_context

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

        self._events: List["DagsterEvent"] = []
        self._observations: List[AssetObservation] = []
        self._metadata_entries: List[Union[MetadataEntry, PartitionMetadataEntry]] = []

    def __enter__(self):
        if self._resources_cm:
            self._cm_scope_entered = True
        return self

    def __exit__(self, *exc):
        if self._resources_cm:
            self._resources_cm.__exit__(*exc)  # pylint: disable=no-member

    def __del__(self):
        if self._resources_cm and self._resources_contain_cm and not self._cm_scope_entered:
            self._resources_cm.__exit__(None, None, None)  # pylint: disable=no-member

    @property
    def has_input_name(self) -> bool:
        """If we're the InputContext is being used to load the result of a run from outside the run,
        then it won't have an input name."""
        return self._name is not None

    @property
    def name(self) -> str:
        if self._name is None:
            raise DagsterInvariantViolationError(
                "Attempting to access name, "
                "but it was not provided when constructing the InputContext"
            )

        return self._name

    @property
    def pipeline_name(self) -> str:
        if self._pipeline_name is None:
            raise DagsterInvariantViolationError(
                "Attempting to access pipeline_name, "
                "but it was not provided when constructing the InputContext"
            )

        return self._pipeline_name

    @property
    def solid_def(self) -> "SolidDefinition":
        if self._solid_def is None:
            raise DagsterInvariantViolationError(
                "Attempting to access solid_def, "
                "but it was not provided when constructing the InputContext"
            )

        return self._solid_def

    @property
    def op_def(self) -> "OpDefinition":
        if self._solid_def is None:
            raise DagsterInvariantViolationError(
                "Attempting to access op_def, "
                "but it was not provided when constructing the InputContext"
            )

        return cast(OpDefinition, self._solid_def)

    @property
    def config(self) -> Any:
        return self._config

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        return self._metadata

    @property
    def upstream_output(self) -> Optional["OutputContext"]:
        return self._upstream_output

    @property
    def dagster_type(self) -> "DagsterType":
        if self._dagster_type is None:
            raise DagsterInvariantViolationError(
                "Attempting to access dagster_type, "
                "but it was not provided when constructing the InputContext"
            )

        return self._dagster_type

    @property
    def log(self) -> "DagsterLogManager":
        if self._log is None:
            raise DagsterInvariantViolationError(
                "Attempting to access log, "
                "but it was not provided when constructing the InputContext"
            )

        return self._log

    @property
    def resource_config(self) -> Optional[Dict[str, Any]]:
        return self._resource_config

    @property
    def resources(self) -> Any:
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

    @property
    def has_asset_key(self) -> bool:
        return (
            self._step_context is not None
            and self._name is not None
            and self._step_context.pipeline_def.asset_layer.asset_key_for_input(
                node_handle=self.step_context.solid_handle, input_name=self._name
            )
            is not None
        )

    @property
    def asset_key(self) -> AssetKey:
        result = self.step_context.pipeline_def.asset_layer.asset_key_for_input(
            node_handle=self.step_context.solid_handle, input_name=self.name
        )
        if result is None:
            raise DagsterInvariantViolationError(
                "Attempting to access asset_key, "
                "but it was not provided when constructing the InputContext"
            )

        return result

    @property
    def step_context(self) -> "StepExecutionContext":
        if self._step_context is None:
            raise DagsterInvariantViolationError(
                "Attempting to access step_context, "
                "but it was not provided when constructing the InputContext"
            )

        return self._step_context

    @property
    def has_partition_key(self) -> bool:
        """Whether the current run is a partitioned run"""
        return self.step_context.has_partition_key

    @property
    def partition_key(self) -> str:
        """The partition key for the current run.

        Raises an error if the current run is not a partitioned run.
        """
        return self.step_context.partition_key

    @property
    def has_asset_partitions(self) -> bool:
        if self._step_context is not None:
            return self._step_context.has_asset_partitions_for_input(self.name)
        else:
            return False

    @property
    def asset_partition_key(self) -> str:
        """The partition key for input asset.

        Raises an error if the input asset has no partitioning, or if the run covers a partition
        range for the input asset.
        """
        return self.step_context.asset_partition_key_for_input(self.name)

    @property
    def asset_partition_key_range(self) -> PartitionKeyRange:
        """The partition key range for input asset.

        Raises an error if the input asset has no partitioning.
        """
        return self.step_context.asset_partition_key_range_for_input(self.name)

    @property
    def asset_partitions_time_window(self) -> TimeWindow:
        """The time window for the partitions of the input asset.

        Raises an error if either of the following are true:
        - The input asset has no partitioning.
        - The input asset is not partitioned with a TimeWindowPartitionsDefinition.
        """
        if self.upstream_output is None:
            check.failed("InputContext needs upstream_output to get asset_partitions_time_window")

        asset_info = self.upstream_output.asset_info
        partitions_def = asset_info.partitions_def if asset_info else None

        if not partitions_def:
            raise ValueError(
                "Tried to get asset partitions for an output that does not correspond to a "
                "partitioned asset."
            )

        if not isinstance(partitions_def, TimeWindowPartitionsDefinition):
            raise ValueError(
                "Tried to get asset partitions for an input that correponds to a partitioned "
                "asset that is not partitioned with a TimeWindowPartitionsDefinition."
            )

        partition_key_range = self.asset_partition_key_range
        return TimeWindow(
            # mypy thinks partitions_def is <nothing> here because ????
            partitions_def.time_window_for_partition_key(partition_key_range.start).start,  # type: ignore
            partitions_def.time_window_for_partition_key(partition_key_range.end).end,  # type: ignore
        )

    def consume_events(self) -> Iterator["DagsterEvent"]:
        """Pops and yields all user-generated events that have been recorded from this context.

        If consume_events has not yet been called, this will yield all logged events since the call to `handle_input`. If consume_events has been called, it will yield all events since the last time consume_events was called. Designed for internal use. Users should never need to invoke this method.
        """

        events = self._events
        self._events = []
        yield from events

    def add_input_metadata(
        self,
        metadata: Dict[str, Any],
        description: Optional[str] = None,
    ) -> None:
        """Accepts a dictionary of metadata. Metadata entries will appear on the LOADED_INPUT event.
        If the input is an asset, metadata will be attached to an asset observation.

        The asset observation will be yielded from the run and appear in the event log.
        Only valid if the context has an asset key.
        """
        from dagster.core.definitions.metadata import normalize_metadata
        from dagster.core.events import DagsterEvent

        metadata = check.dict_param(metadata, "metadata", key_type=str)
        self._metadata_entries.extend(normalize_metadata(metadata, []))
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
    ) -> List[AssetObservation]:
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

    def consume_metadata_entries(self) -> List[Union[MetadataEntry, PartitionMetadataEntry]]:
        result = self._metadata_entries
        self._metadata_entries = []
        return result


def build_input_context(
    name: Optional[str] = None,
    config: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None,
    upstream_output: Optional["OutputContext"] = None,
    dagster_type: Optional["DagsterType"] = None,
    resource_config: Optional[Dict[str, Any]] = None,
    resources: Optional[Dict[str, Any]] = None,
    op_def: Optional[OpDefinition] = None,
    step_context: Optional["StepExecutionContext"] = None,
) -> "InputContext":
    """Builds input context from provided parameters.

    ``build_input_context`` can be used as either a function, or a context manager. If resources
    that are also context managers are provided, then ``build_input_context`` must be used as a
    context manager.

    Args:
        name (Optional[str]): The name of the input that we're loading.
        config (Optional[Any]): The config attached to the input that we're loading.
        metadata (Optional[Dict[str, Any]]): A dict of metadata that is assigned to the
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
        asset_key (Optional[AssetKey]): The asset key attached to the InputDefinition.
        op_def (Optional[OpDefinition]): The definition of the op that's loading the input.
        step_context (Optional[StepExecutionContext]): For internal use.

    Examples:

        .. code-block:: python

            build_input_context()

            with build_input_context(resources={"foo": context_manager_resource}) as context:
                do_something
    """
    from dagster.core.execution.context.output import OutputContext
    from dagster.core.execution.context.system import StepExecutionContext
    from dagster.core.execution.context_creation_pipeline import initialize_console_manager
    from dagster.core.types.dagster_type import DagsterType

    name = check.opt_str_param(name, "name")
    metadata = check.opt_dict_param(metadata, "metadata", key_type=str)
    upstream_output = check.opt_inst_param(upstream_output, "upstream_output", OutputContext)
    dagster_type = check.opt_inst_param(dagster_type, "dagster_type", DagsterType)
    resource_config = check.opt_dict_param(resource_config, "resource_config", key_type=str)
    resources = check.opt_dict_param(resources, "resources", key_type=str)
    op_def = check.opt_inst_param(op_def, "op_def", OpDefinition)
    step_context = check.opt_inst_param(step_context, "step_context", StepExecutionContext)

    return InputContext(
        name=name,
        pipeline_name=None,
        config=config,
        metadata=metadata,
        upstream_output=upstream_output,
        dagster_type=dagster_type,
        log_manager=initialize_console_manager(None),
        resource_config=resource_config,
        resources=resources,
        step_context=step_context,
        op_def=op_def,
    )
