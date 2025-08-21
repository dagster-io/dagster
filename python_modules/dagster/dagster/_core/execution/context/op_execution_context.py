from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, Sequence
from typing import AbstractSet, Any, Optional, cast  # noqa: UP035

import dagster._check as check
from dagster._annotations import deprecated, public
from dagster._core.definitions.asset_checks.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.data_version import (
    DataProvenance,
    DataVersion,
    extract_data_provenance_from_entry,
)
from dagster._core.definitions.dependency import Node, NodeHandle
from dagster._core.definitions.events import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    ExpectationResult,
    UserEvent,
)
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.utils import TimeWindow
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.definitions.step_launcher import StepLauncher
from dagster._core.errors import DagsterInvalidPropertyError, DagsterInvariantViolationError
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.instance import DagsterInstance
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.dagster_run import DagsterRun
from dagster._utils.forked_pdb import ForkedPdb


class AbstractComputeExecutionContext(ABC):
    """Base class for op context implemented by OpExecutionContext and DagstermillExecutionContext."""

    @abstractmethod
    def has_tag(self, key: str) -> bool:
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
    def repository_def(self) -> RepositoryDefinition:
        """The Dagster repository containing the job being executed."""

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


@public
class OpExecutionContext(AbstractComputeExecutionContext):
    """The ``context`` object that can be made available as the first argument to the function
    used for computing an op or asset.

    This context object provides system information such as resources, config, and logging.

    To construct an execution context for testing purposes, use :py:func:`dagster.build_op_context`.

    Example:
        .. code-block:: python

            from dagster import op, OpExecutionContext

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
        self._events: list[DagsterEvent] = []
        self._output_metadata: dict[str, Any] = {}

    @property
    def op_execution_context(self) -> "OpExecutionContext":
        return self

    @public
    @property
    def op_config(self) -> Any:
        """Any: The parsed config specific to this op."""
        return self._step_execution_context.op_config

    @property
    def dagster_run(self) -> DagsterRun:
        """DagsterRun: The current run."""
        return self._step_execution_context.dagster_run

    @public
    @property
    def run(self) -> DagsterRun:
        """DagsterRun: The current run."""
        return self.dagster_run

    @public
    @property
    def instance(self) -> DagsterInstance:
        """DagsterInstance: The current Dagster instance."""
        return self._step_execution_context.instance

    @public
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

    @public
    @property
    def resources(self) -> Any:
        """Resources: The currently available resources."""
        return self._step_execution_context.resources

    @property
    def step_launcher(self) -> Optional[StepLauncher]:
        """Optional[StepLauncher]: The current step launcher, if any."""
        return self._step_execution_context.step_launcher

    @public
    @property
    def run_id(self) -> str:
        """str: The id of the current execution's run."""
        return self._step_execution_context.run_id

    @public
    @property
    def run_config(self) -> Mapping[str, object]:
        """dict: The run config for the current execution."""
        return self._step_execution_context.run_config

    @public
    @property
    def job_def(self) -> JobDefinition:
        """JobDefinition: The currently executing job."""
        return self._step_execution_context.job_def

    @property
    def repository_def(self) -> RepositoryDefinition:
        """RepositoryDefinition: The Dagster repository for the currently executing job."""
        return self._step_execution_context.repository_def

    @public
    @property
    def job_name(self) -> str:
        """str: The name of the currently executing pipeline."""
        return self._step_execution_context.job_name

    @public
    @property
    def log(self) -> DagsterLogManager:
        """DagsterLogManager: The log manager available in the execution context."""
        return self._step_execution_context.log

    @property
    def node_handle(self) -> NodeHandle:
        """NodeHandle: The current op's handle.

        :meta private:
        """
        return self._step_execution_context.node_handle

    @property
    def op_handle(self) -> NodeHandle:
        """NodeHandle: The current op's handle.

        :meta private:
        """
        return self.node_handle

    @property
    def op(self) -> Node:
        """Node: The object representing the invoked op within the graph.

        :meta private:

        """
        return self._step_execution_context.job_def.get_node(self.node_handle)

    @public
    @property
    def op_def(self) -> OpDefinition:
        """OpDefinition: The current op definition."""
        return cast("OpDefinition", self.op.definition)

    @public
    @property
    def has_partitions(self) -> bool:
        """Whether the current run is a partitioned run."""
        return self._step_execution_context.has_partitions

    @public
    @property
    def has_partition_key(self) -> bool:
        """Whether the current run targets a single partition."""
        return self._step_execution_context.has_partition_key

    @public
    @property
    def partition_key(self) -> str:
        """The partition key for the current run.

        Raises an error if the current run is not a partitioned run. Or if the current run is operating
        over a range of partitions (ie. a backfill of several partitions executed in a single run).

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(
                    partitions_def=partitions_def
                )
                def my_asset(context: AssetExecutionContext):
                    context.log.info(context.partition_key)

                # materializing the 2023-08-21 partition of this asset will log:
                #   "2023-08-21"
        """
        return self._step_execution_context.partition_key

    @public
    @property
    def partition_keys(self) -> Sequence[str]:
        """Returns a list of the partition keys for the current run.

        If you want to write your asset to support running a backfill of several partitions in a single run,
        you can use ``partition_keys`` to get all of the partitions being materialized
        by the backfill.

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(partitions_def=partitions_def)
                def an_asset(context: AssetExecutionContext):
                    context.log.info(context.partition_keys)


                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   ["2023-08-21", "2023-08-22", "2023-08-23", "2023-08-24", "2023-08-25"]
        """
        key_range = self.partition_key_range
        partitions_def = self._step_execution_context.run_partitions_def
        if partitions_def is None:
            raise DagsterInvariantViolationError(
                "Cannot access partition_keys for a non-partitioned run"
            )

        with partition_loading_context(dynamic_partitions_store=self.instance):
            return partitions_def.get_partition_keys_in_range(key_range)

    @deprecated(breaking_version="2.0", additional_warn_text="Use `partition_key_range` instead.")
    @public
    @property
    def asset_partition_key_range(self) -> PartitionKeyRange:
        """The range of partition keys for the current run.

        If run is for a single partition key, return a `PartitionKeyRange` with the same start and
        end. Raises an error if the current run is not a partitioned run.
        """
        return self.partition_key_range

    @public
    @property
    def has_partition_key_range(self) -> bool:
        """Whether the current run targets a range of partitions."""
        return self._step_execution_context.has_partition_key_range

    @public
    @property
    def partition_key_range(self) -> PartitionKeyRange:
        """The range of partition keys for the current run.

        If run is for a single partition key, returns a `PartitionKeyRange` with the same start and
        end. Raises an error if the current run is not a partitioned run.

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(
                    partitions_def=partitions_def
                )
                def my_asset(context: AssetExecutionContext):
                    context.log.info(context.partition_key_range)

                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   PartitionKeyRange(start="2023-08-21", end="2023-08-25")
        """
        return self._step_execution_context.partition_key_range

    @public
    @property
    def partition_time_window(self) -> TimeWindow:
        """The partition time window for the current run.

        Raises an error if the current run is not a partitioned run, or if the job's partition
        definition is not a TimeWindowPartitionsDefinition.

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(
                    partitions_def=partitions_def
                )
                def my_asset(context: AssetExecutionContext):
                    context.log.info(context.partition_time_window)

                # materializing the 2023-08-21 partition of this asset will log:
                #   TimeWindow("2023-08-21", "2023-08-22")
        """
        return self._step_execution_context.partition_time_window

    @public
    def has_tag(self, key: str) -> bool:
        """Check if a logging tag is set.

        Args:
            key (str): The tag to check.

        Returns:
            bool: Whether the tag is set.
        """
        return key in self.dagster_run.tags

    @public
    def get_tag(self, key: str) -> Optional[str]:
        """Get a logging tag.

        Args:
            key (tag): The tag to get.

        Returns:
            Optional[str]: The value of the tag, if present.
        """
        return self.dagster_run.tags.get(key)

    @property
    def run_tags(self) -> Mapping[str, str]:
        """Mapping[str, str]: The tags for the current run."""
        return self.dagster_run.tags

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
            event (Union[AssetMaterialization, AssetObservation, ExpectationResult]): The event to log.

        **Examples:**

        .. code-block:: python

            from dagster import op, AssetMaterialization

            @op
            def log_materialization(context):
                context.log_event(AssetMaterialization("foo"))
        """
        if isinstance(event, AssetMaterialization):
            self._events.append(
                DagsterEvent.asset_materialization(self._step_execution_context, event)
            )
        elif isinstance(event, AssetCheckEvaluation):
            self._events.append(
                DagsterEvent.asset_check_evaluation(self._step_execution_context, event)
            )
        elif isinstance(event, AssetObservation):
            self._events.append(DagsterEvent.asset_observation(self._step_execution_context, event))
        elif isinstance(event, ExpectationResult):
            self._events.append(
                DagsterEvent.step_expectation_result(self._step_execution_context, event)
            )
        else:
            check.failed(f"Unexpected event {event}")

    @public
    def add_output_metadata(
        self,
        metadata: Mapping[str, Any],
        output_name: Optional[str] = None,
        mapping_key: Optional[str] = None,
    ) -> None:
        """Add metadata to one of the outputs of an op.

        This can be invoked multiple times per output in the body of an op. If the same key is
        passed multiple times, the value associated with the last call will be used.

        Args:
            metadata (Mapping[str, Any]): The metadata to attach to the output
            output_name (Optional[str]): The name of the output to attach metadata to. If there is only one output on the op, then this argument does not need to be provided. The metadata will automatically be attached to the only output.
            mapping_key (Optional[str]): The mapping key of the output to attach metadata to. If the
                output is not dynamic, this argument does not need to be provided.

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

    @public
    @property
    def retry_number(self) -> int:
        """Which retry attempt is currently executing i.e. 0 for initial attempt, 1 for first retry, etc."""
        return self._step_execution_context.previous_attempt_count

    def describe_op(self) -> str:
        return self._step_execution_context.describe_op()

    @public
    def get_mapping_key(self) -> Optional[str]:
        """Which mapping_key this execution is for if downstream of a DynamicOutput, otherwise None."""
        return self._step_execution_context.step.get_mapping_key()

    #############################################################################################
    # asset related methods
    #############################################################################################

    @public
    @property
    def asset_key(self) -> AssetKey:
        """The AssetKey for the current asset. In a multi_asset, use asset_key_for_output instead."""
        if self.has_assets_def and len(self.assets_def.keys_by_output_name.keys()) > 1:
            raise DagsterInvariantViolationError(
                "Cannot call `context.asset_key` in a multi_asset with more than one asset. Use"
                " `context.asset_key_for_output` instead."
            )
        return next(iter(self.assets_def.keys_by_output_name.values()))

    @public
    @property
    def has_assets_def(self) -> bool:
        """If there is a backing AssetsDefinition for what is currently executing."""
        assets_def = self.job_def.asset_layer.get_assets_def_for_node(self.node_handle)
        return assets_def is not None

    @public
    @property
    def assets_def(self) -> AssetsDefinition:
        """The backing AssetsDefinition for what is currently executing, errors if not available."""
        assets_def = self.job_def.asset_layer.get_assets_def_for_node(self.node_handle)
        if assets_def is None:
            raise DagsterInvalidPropertyError(
                f"Op '{self.op.name}' does not have an assets definition."
            )
        return assets_def

    @public
    @property
    def selected_asset_keys(self) -> AbstractSet[AssetKey]:
        """Get the set of AssetKeys this execution is expected to materialize."""
        if not self.has_assets_def:
            return set()
        return self.assets_def.keys

    @property
    def is_subset(self):
        """Whether the current AssetsDefinition is subsetted. Note that this can be True inside a
        a graph asset for an op that's not subsetted, if the graph asset is subsetted elsewhere.
        """
        if not self.has_assets_def:
            return False
        return self.assets_def.is_subset

    @public
    @property
    def selected_asset_check_keys(self) -> AbstractSet[AssetCheckKey]:
        """Get the asset check keys that correspond to the current selection of assets this execution is expected to materialize."""
        return self.assets_def.check_keys if self.has_assets_def else set()

    @public
    @property
    def selected_output_names(self) -> AbstractSet[str]:
        """Get the output names that correspond to the current selection of assets this execution is expected to materialize."""
        return self._step_execution_context.selected_output_names

    @public
    def asset_key_for_output(self, output_name: str = "result") -> AssetKey:
        """Return the AssetKey for the corresponding output."""
        asset_key = self.job_def.asset_layer.get_asset_key_for_node_output(
            node_handle=self.op_handle, output_name=output_name
        )
        if asset_key is None:
            check.failed(f"Output '{output_name}' has no asset")
        else:
            return asset_key

    @public
    def output_for_asset_key(self, asset_key: AssetKey) -> str:
        """Return the output name for the corresponding asset key."""
        node_output_handle = self.job_def.asset_layer.get_op_output_handle(asset_key)
        if node_output_handle is None:
            check.failed(f"Asset key '{asset_key}' has no output")
        else:
            return node_output_handle.output_name

    @public
    def asset_key_for_input(self, input_name: str) -> AssetKey:
        """Return the AssetKey for the corresponding input."""
        key = self.job_def.asset_layer.get_asset_key_for_node_input(
            inner_node_handle=self.op_handle, input_name=input_name
        )
        if key is None:
            check.failed(f"Input '{input_name}' has no asset")
        else:
            return key

    @deprecated(breaking_version="2.0", additional_warn_text="Use `partition_key` instead.")
    @public
    def asset_partition_key_for_output(self, output_name: str = "result") -> str:
        """Returns the asset partition key for the given output.

        Args:
            output_name (str): For assets defined with the ``@asset`` decorator, the name of the output
                will be automatically provided. For assets defined with ``@multi_asset``, ``output_name``
                should be the op output associated with the asset key (as determined by AssetOut)
                to get the partition key for.

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(
                    partitions_def=partitions_def
                )
                def an_asset(context: AssetExecutionContext):
                    context.log.info(context.asset_partition_key_for_output())


                # materializing the 2023-08-21 partition of this asset will log:
                #   "2023-08-21"

                @multi_asset(
                    outs={
                        "first_asset": AssetOut(key=["my_assets", "first_asset"]),
                        "second_asset": AssetOut(key=["my_assets", "second_asset"]),
                    },
                    partitions_def=partitions_def,
                )
                def a_multi_asset(context: AssetExecutionContext):
                    context.log.info(context.asset_partition_key_for_output("first_asset"))
                    context.log.info(context.asset_partition_key_for_output("second_asset"))


                # materializing the 2023-08-21 partition of this asset will log:
                #   "2023-08-21"
                #   "2023-08-21"


                @asset(
                    partitions_def=partitions_def,
                    ins={
                        "self_dependent_asset": AssetIn(partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)),
                    }
                )
                def self_dependent_asset(context: AssetExecutionContext, self_dependent_asset):
                    context.log.info(context.asset_partition_key_for_output())

                # materializing the 2023-08-21 partition of this asset will log:
                #   "2023-08-21"

        """
        return self._step_execution_context.asset_partition_key_for_output(output_name)

    @deprecated(breaking_version="2.0", additional_warn_text="Use `partition_time_window` instead.")
    @public
    def asset_partitions_time_window_for_output(self, output_name: str = "result") -> TimeWindow:
        """The time window for the partitions of the output asset.

        If you want to write your asset to support running a backfill of several partitions in a single run,
        you can use ``asset_partitions_time_window_for_output`` to get the TimeWindow of all of the partitions
        being materialized by the backfill.

        Raises an error if either of the following are true:
        - The output asset has no partitioning.
        - The output asset is not partitioned with a TimeWindowPartitionsDefinition or a
        MultiPartitionsDefinition with one time-partitioned dimension.

        Args:
            output_name (str): For assets defined with the ``@asset`` decorator, the name of the output
                will be automatically provided. For assets defined with ``@multi_asset``, ``output_name``
                should be the op output associated with the asset key (as determined by AssetOut)
                to get the time window for.

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(
                    partitions_def=partitions_def
                )
                def an_asset(context: AssetExecutionContext):
                    context.log.info(context.asset_partitions_time_window_for_output())


                # materializing the 2023-08-21 partition of this asset will log:
                #   TimeWindow("2023-08-21", "2023-08-22")

                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   TimeWindow("2023-08-21", "2023-08-26")

                @multi_asset(
                    outs={
                        "first_asset": AssetOut(key=["my_assets", "first_asset"]),
                        "second_asset": AssetOut(key=["my_assets", "second_asset"]),
                    },
                    partitions_def=partitions_def,
                )
                def a_multi_asset(context: AssetExecutionContext):
                    context.log.info(context.asset_partitions_time_window_for_output("first_asset"))
                    context.log.info(context.asset_partitions_time_window_for_output("second_asset"))

                # materializing the 2023-08-21 partition of this asset will log:
                #   TimeWindow("2023-08-21", "2023-08-22")
                #   TimeWindow("2023-08-21", "2023-08-22")

                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   TimeWindow("2023-08-21", "2023-08-26")
                #   TimeWindow("2023-08-21", "2023-08-26")


                @asset(
                    partitions_def=partitions_def,
                    ins={
                        "self_dependent_asset": AssetIn(partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)),
                    }
                )
                def self_dependent_asset(context: AssetExecutionContext, self_dependent_asset):
                    context.log.info(context.asset_partitions_time_window_for_output())

                # materializing the 2023-08-21 partition of this asset will log:
                #   TimeWindow("2023-08-21", "2023-08-22")

                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   TimeWindow("2023-08-21", "2023-08-26")

        """
        return self._step_execution_context.asset_partitions_time_window_for_output(output_name)

    @deprecated(breaking_version="2.0", additional_warn_text="Use `partition_key_range` instead.")
    @public
    def asset_partition_key_range_for_output(
        self, output_name: str = "result"
    ) -> PartitionKeyRange:
        """Return the PartitionKeyRange for the corresponding output. Errors if the run is not partitioned.

        If you want to write your asset to support running a backfill of several partitions in a single run,
        you can use ``asset_partition_key_range_for_output`` to get all of the partitions being materialized
        by the backfill.

        Args:
            output_name (str): For assets defined with the ``@asset`` decorator, the name of the output
                will be automatically provided. For assets defined with ``@multi_asset``, ``output_name``
                should be the op output associated with the asset key (as determined by AssetOut)
                to get the partition key range for.

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(
                    partitions_def=partitions_def
                )
                def an_asset(context: AssetExecutionContext):
                    context.log.info(context.asset_partition_key_range_for_output())


                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   PartitionKeyRange(start="2023-08-21", end="2023-08-25")

                @multi_asset(
                    outs={
                        "first_asset": AssetOut(key=["my_assets", "first_asset"]),
                        "second_asset": AssetOut(key=["my_assets", "second_asset"]),
                    },
                    partitions_def=partitions_def,
                )
                def a_multi_asset(context: AssetExecutionContext):
                    context.log.info(context.asset_partition_key_range_for_output("first_asset"))
                    context.log.info(context.asset_partition_key_range_for_output("second_asset"))


                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   PartitionKeyRange(start="2023-08-21", end="2023-08-25")
                #   PartitionKeyRange(start="2023-08-21", end="2023-08-25")


                @asset(
                    partitions_def=partitions_def,
                    ins={
                        "self_dependent_asset": AssetIn(partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)),
                    }
                )
                def self_dependent_asset(context: AssetExecutionContext, self_dependent_asset):
                    context.log.info(context.asset_partition_key_range_for_output())

                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   PartitionKeyRange(start="2023-08-21", end="2023-08-25")

        """
        return self._step_execution_context.asset_partition_key_range_for_output(output_name)

    @public
    def asset_partition_key_range_for_input(self, input_name: str) -> PartitionKeyRange:
        """Return the PartitionKeyRange for the corresponding input. Errors if the asset depends on a
        non-contiguous chunk of the input.

        If you want to write your asset to support running a backfill of several partitions in a single run,
        you can use ``asset_partition_key_range_for_input`` to get the range of partitions keys of the input that
        are relevant to that backfill.

        Args:
            input_name (str): The name of the input to get the time window for.

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(
                    partitions_def=partitions_def
                )
                def upstream_asset():
                    ...

                @asset(
                    partitions_def=partitions_def
                )
                def an_asset(context: AssetExecutionContext, upstream_asset):
                    context.log.info(context.asset_partition_key_range_for_input("upstream_asset"))


                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   PartitionKeyRange(start="2023-08-21", end="2023-08-25")

                @asset(
                    ins={
                        "upstream_asset": AssetIn(partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)),
                    },
                    partitions_def=partitions_def,
                )
                def another_asset(context: AssetExecutionContext, upstream_asset):
                    context.log.info(context.asset_partition_key_range_for_input("upstream_asset"))


                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   PartitionKeyRange(start="2023-08-20", end="2023-08-24")


                @asset(
                    partitions_def=partitions_def,
                    ins={
                        "self_dependent_asset": AssetIn(partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)),
                    }
                )
                def self_dependent_asset(context: AssetExecutionContext, self_dependent_asset):
                    context.log.info(context.asset_partition_key_range_for_input("self_dependent_asset"))

                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   PartitionKeyRange(start="2023-08-20", end="2023-08-24")


        """
        return self._step_execution_context.asset_partition_key_range_for_input(input_name)

    @public
    def asset_partition_key_for_input(self, input_name: str) -> str:
        """Returns the partition key of the upstream asset corresponding to the given input.

        Args:
            input_name (str): The name of the input to get the partition key for.

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(
                    partitions_def=partitions_def
                )
                def upstream_asset():
                    ...

                @asset(
                    partitions_def=partitions_def
                )
                def an_asset(context: AssetExecutionContext, upstream_asset):
                    context.log.info(context.asset_partition_key_for_input("upstream_asset"))

                # materializing the 2023-08-21 partition of this asset will log:
                #   "2023-08-21"


                @asset(
                    partitions_def=partitions_def,
                    ins={
                        "self_dependent_asset": AssetIn(partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)),
                    }
                )
                def self_dependent_asset(context: AssetExecutionContext, self_dependent_asset):
                    context.log.info(context.asset_partition_key_for_input("self_dependent_asset"))

                # materializing the 2023-08-21 partition of this asset will log:
                #   "2023-08-20"

        """
        return self._step_execution_context.asset_partition_key_for_input(input_name)

    @public
    def asset_partitions_def_for_output(self, output_name: str = "result") -> PartitionsDefinition:
        """The PartitionsDefinition on the asset corresponding to this output.

        Args:
            output_name (str): For assets defined with the ``@asset`` decorator, the name of the output
                will be automatically provided. For assets defined with ``@multi_asset``, ``output_name``
                should be the op output associated with the asset key (as determined by AssetOut)
                to get the PartitionsDefinition for.

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(
                    partitions_def=partitions_def
                )
                def upstream_asset(context: AssetExecutionContext):
                    context.log.info(context.asset_partitions_def_for_output())

                # materializing the 2023-08-21 partition of this asset will log:
                #   DailyPartitionsDefinition("2023-08-20")

                @multi_asset(
                    outs={
                        "first_asset": AssetOut(key=["my_assets", "first_asset"]),
                        "second_asset": AssetOut(key=["my_assets", "second_asset"]),
                    },
                    partitions_def=partitions_def,
                )
                def a_multi_asset(context: AssetExecutionContext):
                    context.log.info(context.asset_partitions_def_for_output("first_asset"))
                    context.log.info(context.asset_partitions_def_for_output("second_asset"))

                # materializing the 2023-08-21 partition of this asset will log:
                #   DailyPartitionsDefinition("2023-08-20")
                #   DailyPartitionsDefinition("2023-08-20")

        """
        asset_key = self.asset_key_for_output(output_name)
        result = self._step_execution_context.job_def.asset_layer.get(asset_key).partitions_def
        if result is None:
            raise DagsterInvariantViolationError(
                f"Attempting to access partitions def for asset {asset_key}, but it is not"
                " partitioned"
            )

        return result

    @public
    def asset_partitions_def_for_input(self, input_name: str) -> PartitionsDefinition:
        """The PartitionsDefinition on the upstream asset corresponding to this input.

        Args:
            input_name (str): The name of the input to get the PartitionsDefinition for.

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(
                    partitions_def=partitions_def
                )
                def upstream_asset():
                    ...

                @asset(
                    partitions_def=partitions_def
                )
                def upstream_asset(context: AssetExecutionContext, upstream_asset):
                    context.log.info(context.asset_partitions_def_for_input("upstream_asset"))

                # materializing the 2023-08-21 partition of this asset will log:
                #   DailyPartitionsDefinition("2023-08-20")

        """
        asset_key = self.asset_key_for_input(input_name)
        result = self._step_execution_context.job_def.asset_layer.get(asset_key).partitions_def
        if result is None:
            raise DagsterInvariantViolationError(
                f"Attempting to access partitions def for asset {asset_key}, but it is not"
                " partitioned"
            )

        return result

    @deprecated(breaking_version="2.0", additional_warn_text="Use `partition_keys` instead.")
    @public
    def asset_partition_keys_for_output(self, output_name: str = "result") -> Sequence[str]:
        """Returns a list of the partition keys for the given output.

        If you want to write your asset to support running a backfill of several partitions in a single run,
        you can use ``asset_partition_keys_for_output`` to get all of the partitions being materialized
        by the backfill.

        Args:
            output_name (str): For assets defined with the ``@asset`` decorator, the name of the output
                will be automatically provided. For assets defined with ``@multi_asset``, ``output_name``
                should be the op output associated with the asset key (as determined by AssetOut)
                to get the partition keys for.

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(
                    partitions_def=partitions_def
                )
                def an_asset(context: AssetExecutionContext):
                    context.log.info(context.asset_partition_keys_for_output())


                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   ["2023-08-21", "2023-08-22", "2023-08-23", "2023-08-24", "2023-08-25"]

                @multi_asset(
                    outs={
                        "first_asset": AssetOut(key=["my_assets", "first_asset"]),
                        "second_asset": AssetOut(key=["my_assets", "second_asset"]),
                    },
                    partitions_def=partitions_def,
                )
                def a_multi_asset(context: AssetExecutionContext):
                    context.log.info(context.asset_partition_keys_for_output("first_asset"))
                    context.log.info(context.asset_partition_keys_for_output("second_asset"))


                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   ["2023-08-21", "2023-08-22", "2023-08-23", "2023-08-24", "2023-08-25"]
                #   ["2023-08-21", "2023-08-22", "2023-08-23", "2023-08-24", "2023-08-25"]


                @asset(
                    partitions_def=partitions_def,
                    ins={
                        "self_dependent_asset": AssetIn(partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)),
                    }
                )
                def self_dependent_asset(context: AssetExecutionContext, self_dependent_asset):
                    context.log.info(context.asset_partition_keys_for_output())

                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   ["2023-08-21", "2023-08-22", "2023-08-23", "2023-08-24", "2023-08-25"]
        """
        with partition_loading_context(dynamic_partitions_store=self.instance):
            return self.asset_partitions_def_for_output(output_name).get_partition_keys_in_range(
                self._step_execution_context.asset_partition_key_range_for_output(output_name),
            )

    @public
    def asset_partition_keys_for_input(self, input_name: str) -> Sequence[str]:
        """Returns a list of the partition keys of the upstream asset corresponding to the
        given input.

        If you want to write your asset to support running a backfill of several partitions in a single run,
        you can use ``asset_partition_keys_for_input`` to get all of the partition keys of the input that
        are relevant to that backfill.

        Args:
            input_name (str): The name of the input to get the time window for.

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(
                    partitions_def=partitions_def
                )
                def upstream_asset():
                    ...

                @asset(
                    partitions_def=partitions_def
                )
                def an_asset(context: AssetExecutionContext, upstream_asset):
                    context.log.info(context.asset_partition_keys_for_input("upstream_asset"))


                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   ["2023-08-21", "2023-08-22", "2023-08-23", "2023-08-24", "2023-08-25"]

                @asset(
                    ins={
                        "upstream_asset": AssetIn(partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)),
                    },
                    partitions_def=partitions_def,
                )
                def another_asset(context: AssetExecutionContext, upstream_asset):
                    context.log.info(context.asset_partition_keys_for_input("upstream_asset"))


                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   ["2023-08-20", "2023-08-21", "2023-08-22", "2023-08-23", "2023-08-24"]


                @asset(
                    partitions_def=partitions_def,
                    ins={
                        "self_dependent_asset": AssetIn(partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)),
                    }
                )
                def self_dependent_asset(context: AssetExecutionContext, self_dependent_asset):
                    context.log.info(context.asset_partition_keys_for_input("self_dependent_asset"))

                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   ["2023-08-20", "2023-08-21", "2023-08-22", "2023-08-23", "2023-08-24"]
        """
        return list(
            self._step_execution_context.asset_partitions_subset_for_input(
                input_name
            ).get_partition_keys()
        )

    @public
    def asset_partitions_time_window_for_input(self, input_name: str = "result") -> TimeWindow:
        """The time window for the partitions of the input asset.

        If you want to write your asset to support running a backfill of several partitions in a single run,
        you can use ``asset_partitions_time_window_for_input`` to get the time window of the input that
        are relevant to that backfill.

        Raises an error if either of the following are true:
        - The input asset has no partitioning.
        - The input asset is not partitioned with a TimeWindowPartitionsDefinition or a
        MultiPartitionsDefinition with one time-partitioned dimension.

        Args:
            input_name (str): The name of the input to get the partition key for.

        Examples:
            .. code-block:: python

                partitions_def = DailyPartitionsDefinition("2023-08-20")

                @asset(
                    partitions_def=partitions_def
                )
                def upstream_asset():
                    ...

                @asset(
                    partitions_def=partitions_def
                )
                def an_asset(context: AssetExecutionContext, upstream_asset):
                    context.log.info(context.asset_partitions_time_window_for_input("upstream_asset"))


                # materializing the 2023-08-21 partition of this asset will log:
                #   TimeWindow("2023-08-21", "2023-08-22")

                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   TimeWindow("2023-08-21", "2023-08-26")


                @asset(
                    ins={
                        "upstream_asset": AssetIn(partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)),
                    },
                    partitions_def=partitions_def,
                )
                def another_asset(context: AssetExecutionContext, upstream_asset):
                    context.log.info(context.asset_partitions_time_window_for_input("upstream_asset"))


                # materializing the 2023-08-21 partition of this asset will log:
                #   TimeWindow("2023-08-20", "2023-08-21")

                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   TimeWindow("2023-08-21", "2023-08-26")


                @asset(
                    partitions_def=partitions_def,
                    ins={
                        "self_dependent_asset": AssetIn(partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)),
                    }
                )
                def self_dependent_asset(context: AssetExecutionContext, self_dependent_asset):
                    context.log.info(context.asset_partitions_time_window_for_input("self_dependent_asset"))

                # materializing the 2023-08-21 partition of this asset will log:
                #   TimeWindow("2023-08-20", "2023-08-21")

                # running a backfill of the 2023-08-21 through 2023-08-25 partitions of this asset will log:
                #   TimeWindow("2023-08-20", "2023-08-25")

        """
        return self._step_execution_context.asset_partitions_time_window_for_input(input_name)

    @public
    def get_asset_provenance(self, asset_key: AssetKey) -> Optional[DataProvenance]:
        """Return the provenance information for the most recent materialization of an asset.

        Args:
            asset_key (AssetKey): Key of the asset for which to retrieve provenance.

        Returns:
            Optional[DataProvenance]: Provenance information for the most recent
                materialization of the asset. Returns `None` if the asset was never materialized or
                the materialization record is too old to contain provenance information.
        """
        record = self.instance.get_latest_data_version_record(asset_key)

        return (
            None if record is None else extract_data_provenance_from_entry(record.event_log_entry)
        )

    def set_data_version(self, asset_key: AssetKey, data_version: DataVersion) -> None:
        """Set the data version for an asset being materialized by the currently executing step.
        This is useful for external execution situations where it is not possible to return
        an `Output`.

        Args:
            asset_key (AssetKey): Key of the asset for which to set the data version.
            data_version (DataVersion): The data version to set.
        """
        self._step_execution_context.set_data_version(asset_key, data_version)

    # In this mode no conversion is done on returned values and missing but expected outputs are not
    # allowed.
    @property
    def requires_typed_event_stream(self) -> bool:
        return self._step_execution_context.requires_typed_event_stream

    @property
    def typed_event_stream_error_message(self) -> Optional[str]:
        return self._step_execution_context.typed_event_stream_error_message

    def set_requires_typed_event_stream(self, *, error_message: Optional[str] = None) -> None:
        self._step_execution_context.set_requires_typed_event_stream(error_message=error_message)

    @staticmethod
    def get() -> "OpExecutionContext":
        from dagster._core.execution.context.compute import current_execution_context

        ctx = current_execution_context.get()
        if ctx is None:
            raise DagsterInvariantViolationError("No current OpExecutionContext in scope.")
        return ctx.op_execution_context

    def load_asset_value(
        self,
        asset_key: AssetKey,
        *,
        python_type: Optional[type] = None,
        partition_key: Optional[str] = None,
    ) -> Any:
        """Loads the value of an asset by key.

        Args:
            asset_key (AssetKey): The key of the asset to load.
            python_type (Optional[type]): The python type to load the asset as. This is what will
                be returned inside `load_input` by `context.dagster_type.typing_type`.
            partition_key (Optional[str]): The partition of the asset to load.

        Example:
            .. code-block:: python

                @dg.asset(deps=[dg.AssetKey("upstream_asset")])
                def my_asset(context: dg.AssetExecutionContext):
                    return context.load_asset_value(dg.AssetKey("upstream_asset")) * 2
        """
        from dagster._core.storage.asset_value_loader import AssetValueLoader

        loader = AssetValueLoader(
            assets_defs_by_key={
                asset_key: self._step_execution_context.job_def.asset_layer.get(
                    asset_key
                ).assets_def
            },
            instance=self.instance,
        )
        return loader.load_asset_value(
            asset_key,
            python_type=python_type,
            partition_key=partition_key,
        )
