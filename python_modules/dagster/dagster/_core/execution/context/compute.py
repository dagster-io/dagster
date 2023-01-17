from abc import ABC, abstractmethod
from typing import AbstractSet, Any, Dict, Iterator, List, Mapping, Optional, Sequence, cast

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.dependency import Node, NodeHandle
from dagster._core.definitions.events import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    ExpectationResult,
    Materialization,
    UserEvent,
)
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.mode import ModeDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.pipeline_definition import PipelineDefinition
from dagster._core.definitions.step_launcher import StepLauncher
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.errors import DagsterInvalidPropertyError, DagsterInvariantViolationError
from dagster._core.events import DagsterEvent
from dagster._core.instance import DagsterInstance
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.pipeline_run import DagsterRun
from dagster._utils.backcompat import deprecation_warning
from dagster._utils.forked_pdb import ForkedPdb

from .system import StepExecutionContext


class AbstractComputeExecutionContext(ABC):  # pylint: disable=no-init
    """Base class for solid context implemented by SolidExecutionContext and DagstermillExecutionContext.
    """

    @abstractmethod
    def has_tag(self, key) -> bool:
        """Implement this method to check if a logging tag is set."""

    @abstractmethod
    def get_tag(self, key: str) -> Optional[str]:
        """Implement this method to get a logging tag."""

    @property
    @abstractmethod
    def run_id(self) -> str:
        """The run id for the context."""

    @property
    @abstractmethod
    def op_def(self) -> OpDefinition:
        """The op definition corresponding to the execution step being executed."""

    @property
    @abstractmethod
    def job_def(self) -> JobDefinition:
        """The job being executed."""

    @property
    @abstractmethod
    def run(self) -> DagsterRun:
        """The DagsterRun object corresponding to the execution."""

    @property
    @abstractmethod
    def resources(self) -> Any:
        """Resources available in the execution context."""

    @property
    @abstractmethod
    def log(self) -> DagsterLogManager:
        """The log manager available in the execution context."""

    @property
    @abstractmethod
    def op_config(self) -> Any:
        """The parsed config specific to this op."""


class OpExecutionContext(AbstractComputeExecutionContext):
    """The ``context`` object that can be made available as the first argument to an op's compute
    function.

    The context object provides system information such as resources, config,
    and logging to an op's compute function. Users should not instantiate this
    object directly. To construct an `OpExecutionContext` for testing
    purposes, use :py:func:`dagster.build_op_context`.

    Example:
        .. code-block:: python

            from dagster import op

            @op
            def hello_world(context: OpExecutionContext):
                context.log.info("Hello, world!")
    """

    __slots__ = ["_step_execution_context"]

    def __init__(self, step_execution_context: StepExecutionContext):
        self._step_execution_context = check.inst_param(
            step_execution_context,
            "step_execution_context",
            StepExecutionContext,
        )
        self._pdb: Optional[ForkedPdb] = None
        self._events: List[DagsterEvent] = []
        self._output_metadata: Dict[str, Any] = {}

    @property
    def solid_config(self) -> Any:
        return self._step_execution_context.op_config

    @public  # type: ignore
    @property
    def op_config(self) -> Any:
        return self.solid_config

    @property
    def pipeline_run(self) -> DagsterRun:
        """PipelineRun: The current pipeline run."""
        return self._step_execution_context.pipeline_run

    @property
    def run(self) -> DagsterRun:
        """DagsterRun: The current run."""
        return cast(DagsterRun, self.pipeline_run)

    @public  # type: ignore
    @property
    def instance(self) -> DagsterInstance:
        """DagsterInstance: The current Dagster instance."""
        return self._step_execution_context.instance

    @public  # type: ignore
    @property
    def pdb(self) -> ForkedPdb:
        """dagster.utils.forked_pdb.ForkedPdb: Gives access to pdb debugging from within the op.

        Example:
            .. code-block:: python

                @op
                def debug(context):
                    context.pdb.set_trace()
        """
        if self._pdb is None:
            self._pdb = ForkedPdb()

        return self._pdb

    @property
    def file_manager(self):
        """Deprecated access to the file manager.

        :meta private:
        """
        raise DagsterInvalidPropertyError(
            "You have attempted to access the file manager which has been moved to resources in"
            " 0.10.0. Please access it via `context.resources.file_manager` instead."
        )

    @public  # type: ignore
    @property
    def resources(self) -> Any:
        """Resources: The currently available resources."""
        return self._step_execution_context.resources

    @property
    def step_launcher(self) -> Optional[StepLauncher]:
        """Optional[StepLauncher]: The current step launcher, if any."""
        return self._step_execution_context.step_launcher

    @public  # type: ignore
    @property
    def run_id(self) -> str:
        """str: The id of the current execution's run."""
        return self._step_execution_context.run_id

    @public  # type: ignore
    @property
    def run_config(self) -> Mapping[str, object]:
        """dict: The run config for the current execution."""
        return self._step_execution_context.run_config

    @property
    def pipeline_def(self) -> PipelineDefinition:
        """PipelineDefinition: The currently executing pipeline."""
        return self._step_execution_context.pipeline_def

    @public  # type: ignore
    @property
    def job_def(self) -> JobDefinition:
        """JobDefinition: The currently executing job."""
        return cast(
            JobDefinition,
            check.inst(
                self.pipeline_def,
                JobDefinition,
                "Accessing job_def inside a legacy pipeline. Use pipeline_def instead.",
            ),
        )

    @property
    def pipeline_name(self) -> str:
        """str: The name of the currently executing pipeline."""
        return self._step_execution_context.pipeline_name

    @public  # type: ignore
    @property
    def job_name(self) -> str:
        """str: The name of the currently executing job."""
        return self.pipeline_name

    @property
    def mode_def(self) -> ModeDefinition:
        """ModeDefinition: The mode of the current execution."""
        return self._step_execution_context.mode_def

    @public  # type: ignore
    @property
    def log(self) -> DagsterLogManager:
        """DagsterLogManager: The log manager available in the execution context."""
        return self._step_execution_context.log

    @property
    def solid_handle(self) -> NodeHandle:
        """NodeHandle: The current solid's handle.

        :meta private:
        """
        return self._step_execution_context.solid_handle

    @property
    def op_handle(self) -> NodeHandle:
        """NodeHandle: The current op's handle.

        :meta private:
        """
        return self.solid_handle

    @property
    def solid(self) -> Node:
        """Solid: The current solid object.

        :meta private:

        """
        return self._step_execution_context.pipeline_def.get_solid(self.solid_handle)

    @property
    def op(self) -> Node:
        """Solid: The current op object.

        :meta private:

        """
        return self.solid

    @public  # type: ignore
    @property
    def op_def(self) -> OpDefinition:
        """OpDefinition: The current op definition."""
        return cast(OpDefinition, self.op.definition)

    @public  # type: ignore
    @property
    def has_partition_key(self) -> bool:
        """Whether the current run is a partitioned run."""
        return self._step_execution_context.has_partition_key

    @public  # type: ignore
    @property
    def partition_key(self) -> str:
        """The partition key for the current run.

        Raises an error if the current run is not a partitioned run.
        """
        return self._step_execution_context.partition_key

    @public  # type: ignore
    @property
    def asset_partition_key_range(self) -> PartitionKeyRange:
        """The asset partition key for the current run.

        Raises an error if the current run is not a partitioned run.
        """
        return self._step_execution_context.asset_partition_key_range

    @public  # type: ignore
    @property
    def partition_time_window(self) -> str:
        """The partition time window for the current run.

        Raises an error if the current run is not a partitioned run, or if the job's partition
        definition is not a TimeWindowPartitionsDefinition.
        """
        return self._step_execution_context.partition_time_window

    @public  # type: ignore
    @property
    def selected_asset_keys(self) -> AbstractSet[AssetKey]:
        assets_def = self.job_def.asset_layer.assets_def_for_node(self.solid_handle)
        if assets_def is None:
            return set()
        return assets_def.keys

    @public  # type: ignore
    @property
    def selected_output_names(self) -> AbstractSet[str]:
        # map selected asset keys to the output names they correspond to
        selected_asset_keys = self.selected_asset_keys
        selected_outputs = set()
        for output_name in self.op.output_dict.keys():
            asset_info = self.job_def.asset_layer.asset_info_for_output(
                self.solid_handle, output_name
            )
            if any(  #  For graph-backed assets, check if a downstream asset is selected
                [
                    asset_key in selected_asset_keys
                    for asset_key in self.job_def.asset_layer.downstream_dep_assets(
                        self.solid_handle, output_name
                    )
                ]
            ) or (asset_info and asset_info.key in selected_asset_keys):
                selected_outputs.add(output_name)

        return selected_outputs

    @public
    def asset_key_for_output(self, output_name: str = "result") -> AssetKey:
        asset_output_info = self.pipeline_def.asset_layer.asset_info_for_output(
            node_handle=self.op_handle, output_name=output_name
        )
        if asset_output_info is None:
            check.failed(f"Output '{output_name}' has no asset")
        else:
            return asset_output_info.key

    @public
    def asset_key_for_input(self, input_name: str) -> AssetKey:
        key = self.pipeline_def.asset_layer.asset_key_for_input(
            node_handle=self.op_handle, input_name=input_name
        )
        if key is None:
            check.failed(f"Input '{input_name}' has no asset")
        else:
            return key

    def output_asset_partition_key(self, output_name: str = "result") -> str:
        deprecation_warning(
            "OpExecutionContext.output_asset_partition_key",
            "1.0.0",
            additional_warn_txt="Use OpExecutionContext.asset_partition_key_for_output instead.",
        )

        return self.asset_partition_key_for_output(output_name)

    @public
    def asset_partition_key_for_output(self, output_name: str = "result") -> str:
        """Returns the asset partition key for the given output. Defaults to "result", which is the
        name of the default output.
        """
        return self._step_execution_context.asset_partition_key_for_output(output_name)

    def output_asset_partitions_time_window(self, output_name: str = "result") -> TimeWindow:
        deprecation_warning(
            "OpExecutionContext.output_asset_partitions_time_window",
            "1.0.0",
            additional_warn_txt=(
                "Use OpExecutionContext.asset_partitions_time_window_for_output instead."
            ),
        )

        return self.asset_partitions_time_window_for_output(output_name)

    @public
    def asset_partitions_time_window_for_output(self, output_name: str = "result") -> TimeWindow:
        """The time window for the partitions of the output asset.

        Raises an error if either of the following are true:
        - The output asset has no partitioning.
        - The output asset is not partitioned with a TimeWindowPartitionsDefinition.
        """
        return self._step_execution_context.asset_partitions_time_window_for_output(output_name)

    @public
    def asset_partition_key_range_for_output(
        self, output_name: str = "result"
    ) -> PartitionKeyRange:
        return self._step_execution_context.asset_partition_key_range_for_output(output_name)

    @public
    def asset_partition_key_range_for_input(self, input_name: str) -> PartitionKeyRange:
        return self._step_execution_context.asset_partition_key_range_for_input(input_name)

    @public
    def asset_partition_key_for_input(self, input_name: str) -> str:
        """Returns the partition key of the upstream asset corresponding to the given input."""
        return self._step_execution_context.asset_partition_key_for_input(input_name)

    @public
    def asset_partitions_def_for_output(self, output_name: str = "result") -> PartitionsDefinition:
        """The PartitionsDefinition on the upstream asset corresponding to this input."""
        asset_key = self.asset_key_for_output(output_name)
        result = self._step_execution_context.pipeline_def.asset_layer.partitions_def_for_asset(
            asset_key
        )
        if result is None:
            raise DagsterInvariantViolationError(
                f"Attempting to access partitions def for asset {asset_key}, but it is not"
                " partitioned"
            )

        return result

    @public
    def asset_partitions_def_for_input(self, input_name: str) -> PartitionsDefinition:
        """The PartitionsDefinition on the upstream asset corresponding to this input."""
        asset_key = self.asset_key_for_input(input_name)
        result = self._step_execution_context.pipeline_def.asset_layer.partitions_def_for_asset(
            asset_key
        )
        if result is None:
            raise DagsterInvariantViolationError(
                f"Attempting to access partitions def for asset {asset_key}, but it is not"
                " partitioned"
            )

        return result

    @public
    def asset_partition_keys_for_output(self, output_name: str) -> Sequence[str]:
        """Returns a list of the partition keys for the given output."""
        return self.asset_partitions_def_for_output(output_name).get_partition_keys_in_range(
            self._step_execution_context.asset_partition_key_range_for_output(output_name)
        )

    @public
    def asset_partition_keys_for_input(self, input_name: str) -> Sequence[str]:
        """Returns a list of the partition keys of the upstream asset corresponding to the
        given input.
        """
        return self.asset_partitions_def_for_input(input_name).get_partition_keys_in_range(
            self._step_execution_context.asset_partition_key_range_for_input(input_name)
        )

    @public
    def has_tag(self, key: str) -> bool:
        """Check if a logging tag is set.

        Args:
            key (str): The tag to check.

        Returns:
            bool: Whether the tag is set.
        """
        return self._step_execution_context.has_tag(key)

    @public
    def get_tag(self, key: str) -> Optional[str]:
        """Get a logging tag.

        Args:
            key (tag): The tag to get.

        Returns:
            Optional[str]: The value of the tag, if present.
        """
        return self._step_execution_context.get_tag(key)

    def has_events(self) -> bool:
        return bool(self._events)

    def consume_events(self) -> Iterator[DagsterEvent]:
        """Pops and yields all user-generated events that have been recorded from this context.

        If consume_events has not yet been called, this will yield all logged events since the beginning of the op's computation. If consume_events has been called, it will yield all events since the last time consume_events was called. Designed for internal use. Users should never need to invoke this method.
        """
        events = self._events
        self._events = []
        yield from events

    @public
    def log_event(self, event: UserEvent) -> None:
        """Log an AssetMaterialization, AssetObservation, or ExpectationResult from within the body of an op.

        Events logged with this method will appear in the list of DagsterEvents, as well as the event log.

        Args:
            event (Union[AssetMaterialization, Materialization, AssetObservation, ExpectationResult]): The event to log.

        **Examples:**

        .. code-block:: python

            from dagster import op, AssetMaterialization

            @op
            def log_materialization(context):
                context.log_event(AssetMaterialization("foo"))
        """
        if isinstance(event, (AssetMaterialization, Materialization)):
            self._events.append(
                DagsterEvent.asset_materialization(
                    self._step_execution_context,
                    event,
                    self._step_execution_context.get_input_lineage(),
                )
            )
        elif isinstance(event, AssetObservation):
            self._events.append(DagsterEvent.asset_observation(self._step_execution_context, event))
        elif isinstance(event, ExpectationResult):
            self._events.append(
                DagsterEvent.step_expectation_result(self._step_execution_context, event)
            )
        else:
            check.failed("Unexpected event {event}".format(event=event))

    def add_output_metadata(
        self,
        metadata: Mapping[str, Any],
        output_name: Optional[str] = None,
        mapping_key: Optional[str] = None,
    ) -> None:
        """Add metadata to one of the outputs of an op.

        This can only be used once per output in the body of an op. Using this method with the same output_name more than once within an op will result in an error.

        Args:
            metadata (Mapping[str, Any]): The metadata to attach to the output
            output_name (Optional[str]): The name of the output to attach metadata to. If there is only one output on the op, then this argument does not need to be provided. The metadata will automatically be attached to the only output.

        **Examples:**

        .. code-block:: python

            from dagster import Out, op
            from typing import Tuple

            @op
            def add_metadata(context):
                context.add_output_metadata({"foo", "bar"})
                return 5 # Since the default output is called "result", metadata will be attached to the output "result".

            @op(out={"a": Out(), "b": Out()})
            def add_metadata_two_outputs(context) -> Tuple[str, int]:
                context.add_output_metadata({"foo": "bar"}, output_name="b")
                context.add_output_metadata({"baz": "bat"}, output_name="a")

                return ("dog", 5)

        """
        metadata = check.mapping_param(metadata, "metadata", key_type=str)
        output_name = check.opt_str_param(output_name, "output_name")
        mapping_key = check.opt_str_param(mapping_key, "mapping_key")

        self._step_execution_context.add_output_metadata(
            metadata=metadata, output_name=output_name, mapping_key=mapping_key
        )

    def get_output_metadata(
        self, output_name: str, mapping_key: Optional[str] = None
    ) -> Optional[Mapping[str, Any]]:
        return self._step_execution_context.get_output_metadata(
            output_name=output_name, mapping_key=mapping_key
        )

    def get_step_execution_context(self) -> StepExecutionContext:
        """Allows advanced users (e.g. framework authors) to punch through to the underlying
        step execution context.

        :meta private:

        Returns:
            StepExecutionContext: The underlying system context.
        """
        return self._step_execution_context

    @public  # type: ignore
    @property
    def retry_number(self) -> int:
        """
        Which retry attempt is currently executing i.e. 0 for initial attempt, 1 for first retry, etc.
        """
        return self._step_execution_context.previous_attempt_count

    def describe_op(self):
        return self._step_execution_context.describe_op()

    @public
    def get_mapping_key(self) -> Optional[str]:
        """
        Which mapping_key this execution is for if downstream of a DynamicOutput, otherwise None.
        """
        return self._step_execution_context.step.get_mapping_key()


SourceAssetObserveContext: TypeAlias = OpExecutionContext
