from collections.abc import Iterator, Mapping, Sequence
from typing import AbstractSet, Any, Optional  # noqa: UP035

import dagster._check as check
from dagster._annotations import deprecated, public
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.data_version import DataProvenance, DataVersion
from dagster._core.definitions.dependency import Node, NodeHandle
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey, UserEvent
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.utils import TimeWindow
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.definitions.step_launcher import StepLauncher
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.instance import DagsterInstance
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.dagster_run import DagsterRun
from dagster._utils.forked_pdb import ForkedPdb


def _copy_docs_from_op_execution_context(obj):
    setattr(obj, "__doc__", getattr(OpExecutionContext, obj.__name__).__doc__)
    return obj


ALTERNATE_METHODS = {
    "run_id": "run.run_id",
    "dagster_run": "run",
    "run_config": "run.run_config",
    "run_tags": "run.tags",
    "get_op_execution_context": "op_execution_context",
    "asset_partition_key_for_output": "partition_key",
    "asset_partitions_time_window_for_output": "partition_time_window",
    "asset_partition_key_range_for_output": "partition_key_range",
    "asset_partitions_def_for_output": "assets_def.partitions_def",
    "asset_partition_keys_for_output": "partition_keys",
}

ALTERNATE_EXPRESSIONS = {
    "has_tag": "key in context.run.tags",
    "get_tag": "context.run.tags.get(key)",
}

USE_OP_CONTEXT = [
    "op_config",
    "node_handle",
    "op_handle",
    "op",
    "get_mapping_key",
    "selected_output_names",
]


def _get_deprecation_kwargs(attr: str) -> Mapping[str, Any]:
    deprecation_kwargs = {"breaking_version": "a future release"}
    deprecation_kwargs["subject"] = f"AssetExecutionContext.{attr}"

    if attr in ALTERNATE_METHODS:
        deprecation_kwargs["additional_warn_text"] = (
            f"You have called the deprecated method {attr} on AssetExecutionContext. Use"
            f" context.{ALTERNATE_METHODS[attr]} instead."
        )
    elif attr in ALTERNATE_EXPRESSIONS:
        deprecation_kwargs["additional_warn_text"] = (
            f"You have called the deprecated method {attr} on AssetExecutionContext. Use"
            f" {ALTERNATE_EXPRESSIONS[attr]} instead."
        )
    elif attr in USE_OP_CONTEXT:
        deprecation_kwargs["additional_warn_text"] = (
            f"You have called the deprecated method {attr} on AssetExecutionContext. Use"
            f" context.op_execution_context.{attr} instead."
        )

    return deprecation_kwargs


@public
class AssetExecutionContext:
    def __init__(self, op_execution_context: OpExecutionContext) -> None:
        self._op_execution_context = check.inst_param(
            op_execution_context, "op_execution_context", OpExecutionContext
        )
        self._step_execution_context = self._op_execution_context._step_execution_context  # noqa: SLF001

    @staticmethod
    def get() -> "AssetExecutionContext":
        from dagster._core.execution.context.asset_check_execution_context import (
            AssetCheckExecutionContext,
        )
        from dagster._core.execution.context.compute import current_execution_context

        ctx = current_execution_context.get()
        if ctx is None:
            raise DagsterInvariantViolationError("No current AssetExecutionContext in scope.")
        if isinstance(ctx, AssetCheckExecutionContext):
            raise DagsterInvariantViolationError(
                "Can't use AssetExecutionContext.get() in the context of an "
                "AssetCheckExecutionContext. Use AssetCheckExecutionContext.get() instead."
            )
        return ctx

    @property
    def op_execution_context(self) -> OpExecutionContext:
        return self._op_execution_context

    ####### Top-level properties/methods on AssetExecutionContext

    @public
    @property
    def log(self) -> DagsterLogManager:
        """The log manager available in the execution context. Logs will be viewable in the Dagster UI.
        Returns: DagsterLogManager.

        Example:
            .. code-block:: python

                @asset
                def logger(context):
                    context.log.info("Info level message")
        """
        return self.op_execution_context.log

    @public
    @property
    def pdb(self) -> ForkedPdb:
        """Gives access to pdb debugging from within the asset. Materializing the asset via the
        Dagster UI or CLI will enter the pdb debugging context in the process used to launch the UI or
        run the CLI.

        Returns: dagster.utils.forked_pdb.ForkedPdb

        Example:
            .. code-block:: python

                @asset
                def debug(context):
                    context.pdb.set_trace()
        """
        return self.op_execution_context.pdb

    @property
    def run(self) -> DagsterRun:
        """The DagsterRun object corresponding to the execution. Information like run_id,
        run configuration, and the assets selected for materialization can be found on the DagsterRun.
        """
        return self.op_execution_context.run

    @public
    @property
    def job_def(self) -> JobDefinition:
        """The definition for the currently executing job. Information like the job name, and job tags
        can be found on the JobDefinition.
        Returns: JobDefinition.
        """
        return self.op_execution_context.job_def

    @property
    def repository_def(self) -> RepositoryDefinition:
        """RepositoryDefinition: The Dagster repository for the currently executing job."""
        return self.op_execution_context.repository_def

    ######## Deprecated methods

    @deprecated(**_get_deprecation_kwargs("dagster_run"))
    @property
    @_copy_docs_from_op_execution_context
    def dagster_run(self) -> DagsterRun:
        return self.op_execution_context.dagster_run

    @deprecated(**_get_deprecation_kwargs("run_id"))
    @property
    @_copy_docs_from_op_execution_context
    def run_id(self) -> str:
        return self.op_execution_context.run_id

    @deprecated(**_get_deprecation_kwargs("run_config"))
    @property
    @_copy_docs_from_op_execution_context
    def run_config(self) -> Mapping[str, object]:
        return self.op_execution_context.run_config

    @deprecated(**_get_deprecation_kwargs("run_tags"))
    @property
    @_copy_docs_from_op_execution_context
    def run_tags(self) -> Mapping[str, str]:
        return self.op_execution_context.run_tags

    @deprecated(**_get_deprecation_kwargs("has_tag"))
    @public
    @_copy_docs_from_op_execution_context
    def has_tag(self, key: str) -> bool:
        return self.op_execution_context.has_tag(key)

    @deprecated(**_get_deprecation_kwargs("get_tag"))
    @public
    @_copy_docs_from_op_execution_context
    def get_tag(self, key: str) -> Optional[str]:
        return self.op_execution_context.get_tag(key)

    @deprecated(**_get_deprecation_kwargs("get_op_execution_context"))
    def get_op_execution_context(self) -> "OpExecutionContext":
        return self.op_execution_context

    @deprecated(**_get_deprecation_kwargs("asset_partition_key_for_output"))
    @public
    @_copy_docs_from_op_execution_context
    def asset_partition_key_for_output(self, output_name: str = "result") -> str:
        return self.op_execution_context.asset_partition_key_for_output(output_name=output_name)

    @deprecated(**_get_deprecation_kwargs("asset_partitions_time_window_for_output"))
    @public
    @_copy_docs_from_op_execution_context
    def asset_partitions_time_window_for_output(self, output_name: str = "result") -> TimeWindow:
        return self.op_execution_context.asset_partitions_time_window_for_output(output_name)

    @deprecated(**_get_deprecation_kwargs("asset_partition_key_range_for_output"))
    @public
    @_copy_docs_from_op_execution_context
    def asset_partition_key_range_for_output(
        self, output_name: str = "result"
    ) -> PartitionKeyRange:
        return self.op_execution_context.asset_partition_key_range_for_output(output_name)

    @deprecated(**_get_deprecation_kwargs("asset_partitions_def_for_output"))
    @public
    @_copy_docs_from_op_execution_context
    def asset_partitions_def_for_output(self, output_name: str = "result") -> PartitionsDefinition:
        return self.op_execution_context.asset_partitions_def_for_output(output_name=output_name)

    @deprecated(**_get_deprecation_kwargs("asset_partition_keys_for_output"))
    @public
    @_copy_docs_from_op_execution_context
    def asset_partition_keys_for_output(self, output_name: str = "result") -> Sequence[str]:
        return self.op_execution_context.asset_partition_keys_for_output(output_name=output_name)

    @deprecated(**_get_deprecation_kwargs("op_config"))
    @public
    @property
    @_copy_docs_from_op_execution_context
    def op_config(self) -> Any:
        return self.op_execution_context.op_config

    @deprecated(**_get_deprecation_kwargs("node_handle"))
    @property
    @_copy_docs_from_op_execution_context
    def node_handle(self) -> NodeHandle:
        return self.op_execution_context.node_handle

    @deprecated(**_get_deprecation_kwargs("op_handle"))
    @property
    @_copy_docs_from_op_execution_context
    def op_handle(self) -> NodeHandle:
        return self.op_execution_context.op_handle

    @deprecated(**_get_deprecation_kwargs("op"))
    @property
    @_copy_docs_from_op_execution_context
    def op(self) -> Node:
        return self.op_execution_context.op

    @deprecated(**_get_deprecation_kwargs("get_mapping_key"))
    @public
    @_copy_docs_from_op_execution_context
    def get_mapping_key(self) -> Optional[str]:
        return self.op_execution_context.get_mapping_key()

    @deprecated(**_get_deprecation_kwargs("selected_output_names"))
    @public
    @property
    @_copy_docs_from_op_execution_context
    def selected_output_names(self) -> AbstractSet[str]:
        return self.op_execution_context.selected_output_names

    ########## pass-through to op context

    #### op related

    @property
    @_copy_docs_from_op_execution_context
    def retry_number(self):
        return self.op_execution_context.retry_number

    @_copy_docs_from_op_execution_context
    def describe_op(self) -> str:
        return self.op_execution_context.describe_op()

    @public
    @property
    @_copy_docs_from_op_execution_context
    def op_def(self) -> OpDefinition:
        return self.op_execution_context.op_def

    #### job related

    @public
    @property
    @_copy_docs_from_op_execution_context
    def job_name(self) -> str:
        return self.op_execution_context.job_name

    #### asset related

    @public
    @property
    @_copy_docs_from_op_execution_context
    def asset_key(self) -> AssetKey:
        return self.op_execution_context.asset_key

    @public
    @property
    @_copy_docs_from_op_execution_context
    def has_assets_def(self) -> bool:
        return self.op_execution_context.has_assets_def

    @public
    @property
    @_copy_docs_from_op_execution_context
    def assets_def(self) -> AssetsDefinition:
        return self.op_execution_context.assets_def

    @public
    @_copy_docs_from_op_execution_context
    def asset_key_for_output(self, output_name: str = "result") -> AssetKey:
        return self.op_execution_context.asset_key_for_output(output_name=output_name)

    @public
    @_copy_docs_from_op_execution_context
    def output_for_asset_key(self, asset_key: AssetKey) -> str:
        return self.op_execution_context.output_for_asset_key(asset_key=asset_key)

    @public
    @_copy_docs_from_op_execution_context
    def asset_key_for_input(self, input_name: str) -> AssetKey:
        return self.op_execution_context.asset_key_for_input(input_name=input_name)

    @public
    @property
    @_copy_docs_from_op_execution_context
    def selected_asset_keys(self) -> AbstractSet[AssetKey]:
        return self.op_execution_context.selected_asset_keys

    #### execution related

    @public
    @property
    @_copy_docs_from_op_execution_context
    def instance(self) -> DagsterInstance:
        return self.op_execution_context.instance

    @property
    @_copy_docs_from_op_execution_context
    def step_launcher(self) -> Optional[StepLauncher]:
        return self.op_execution_context.step_launcher

    @_copy_docs_from_op_execution_context
    def get_step_execution_context(self) -> StepExecutionContext:
        return self.op_execution_context.get_step_execution_context()

    #### partition_related

    @public
    @property
    @_copy_docs_from_op_execution_context
    def has_partition_key(self) -> bool:
        return self.op_execution_context.has_partition_key

    @public
    @property
    @_copy_docs_from_op_execution_context
    def partition_key(self) -> str:
        return self.op_execution_context.partition_key

    @public
    @property
    @_copy_docs_from_op_execution_context
    def partition_keys(self) -> Sequence[str]:
        return self.op_execution_context.partition_keys

    @public
    @property
    @_copy_docs_from_op_execution_context
    def has_partition_key_range(self) -> bool:
        return self.op_execution_context.has_partition_key_range

    @deprecated(breaking_version="2.0", additional_warn_text="Use `partition_key_range` instead.")
    @public
    @property
    @_copy_docs_from_op_execution_context
    def asset_partition_key_range(self) -> PartitionKeyRange:
        return self.op_execution_context.asset_partition_key_range

    @public
    @property
    @_copy_docs_from_op_execution_context
    def partition_key_range(self) -> PartitionKeyRange:
        return self.op_execution_context.partition_key_range

    @public
    @property
    @_copy_docs_from_op_execution_context
    def partition_time_window(self) -> TimeWindow:
        return self.op_execution_context.partition_time_window

    @public
    @_copy_docs_from_op_execution_context
    def asset_partition_key_range_for_input(self, input_name: str) -> PartitionKeyRange:
        return self.op_execution_context.asset_partition_key_range_for_input(input_name)

    @public
    @_copy_docs_from_op_execution_context
    def asset_partition_key_for_input(self, input_name: str) -> str:
        return self.op_execution_context.asset_partition_key_for_input(input_name)

    @public
    @_copy_docs_from_op_execution_context
    def asset_partitions_def_for_input(self, input_name: str) -> PartitionsDefinition:
        return self.op_execution_context.asset_partitions_def_for_input(input_name=input_name)

    @public
    @_copy_docs_from_op_execution_context
    def asset_partition_keys_for_input(self, input_name: str) -> Sequence[str]:
        return self.op_execution_context.asset_partition_keys_for_input(input_name=input_name)

    @public
    @_copy_docs_from_op_execution_context
    def asset_partitions_time_window_for_input(self, input_name: str = "result") -> TimeWindow:
        return self.op_execution_context.asset_partitions_time_window_for_input(input_name)

    #### Event log related

    @_copy_docs_from_op_execution_context
    def has_events(self) -> bool:
        return self.op_execution_context.has_events()

    @_copy_docs_from_op_execution_context
    def consume_events(self) -> Iterator[DagsterEvent]:
        yield from self.op_execution_context.consume_events()

    @public
    @_copy_docs_from_op_execution_context
    def log_event(self, event: UserEvent) -> None:
        return self.op_execution_context.log_event(event)

    #### metadata related

    @public
    @_copy_docs_from_op_execution_context
    def add_output_metadata(
        self,
        metadata: Mapping[str, Any],
        output_name: Optional[str] = None,
        mapping_key: Optional[str] = None,
    ) -> None:
        return self.op_execution_context.add_output_metadata(
            metadata=metadata,
            output_name=output_name,
            mapping_key=mapping_key,
        )

    @public
    def add_asset_metadata(
        self,
        metadata: Mapping[str, Any],
        asset_key: Optional[CoercibleToAssetKey] = None,
        partition_key: Optional[str] = None,
    ) -> None:
        """Add metadata to an asset materialization event. This metadata will be
        available in the Dagster UI.

        Args:
            metadata (Mapping[str, Any]): The metadata to add to the asset
                materialization event.
            asset_key (Optional[CoercibleToAssetKey]): The asset key to add metadata to.
                Does not need to be provided if only one asset is currently being
                materialized.
            partition_key (Optional[str]): The partition key to add metadata to, if
                applicable. Should not be provided on non-partitioned assets. If not
                provided on a partitioned asset, the metadata will be added to all
                partitions of the asset currently being materialized.

        Examples:
            Adding metadata to the asset materialization event for a single asset:

            .. code-block:: python

                import dagster as dg

                @dg.asset
                def my_asset(context):
                    # Add metadata
                    context.add_asset_metadata({"key": "value"})

            Adding metadata to the asset materialization event for a particular partition of a partitioned asset:

            .. code-block:: python

                import dagster as dg

                @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b"]))
                def my_asset(context):
                    # Adds metadata to all partitions currently being materialized, since no
                    # partition is specified.
                    context.add_asset_metadata({"key": "value"})

                    for partition_key in context.partition_keys:
                        # Add metadata only to the event for partition "a"
                        if partition_key == "a":
                            context.add_asset_metadata({"key": "value"}, partition_key=partition_key)

            Adding metadata to the asset materialization event for a particular asset in a multi-asset.

            .. code-block:: python

                import dagster as dg

                @dg.multi_asset(specs=[dg.AssetSpec("asset1"), dg.AssetSpec("asset2")])
                def my_multi_asset(context):
                    # Add metadata to the materialization event for "asset1"
                    context.add_asset_metadata({"key": "value"}, asset_key="asset1")

                    # THIS line will fail since asset key is not specified:
                    context.add_asset_metadata({"key": "value"})

        """
        self._step_execution_context.add_asset_metadata(
            metadata=metadata,
            asset_key=asset_key,
            partition_key=partition_key,
        )

    @_copy_docs_from_op_execution_context
    def get_output_metadata(
        self,
        output_name: str,
        mapping_key: Optional[str] = None,
    ) -> Optional[Mapping[str, Any]]:
        return self.op_execution_context.get_output_metadata(
            output_name=output_name,
            mapping_key=mapping_key,
        )

    #### asset check related

    @public
    @property
    @_copy_docs_from_op_execution_context
    def selected_asset_check_keys(self) -> AbstractSet[AssetCheckKey]:
        return self.op_execution_context.selected_asset_check_keys

    #### data lineage related

    @public
    @_copy_docs_from_op_execution_context
    def get_asset_provenance(self, asset_key: AssetKey) -> Optional[DataProvenance]:
        return self.op_execution_context.get_asset_provenance(asset_key=asset_key)

    @_copy_docs_from_op_execution_context
    def set_data_version(self, asset_key: AssetKey, data_version: DataVersion) -> None:
        return self.op_execution_context.set_data_version(
            asset_key=asset_key, data_version=data_version
        )

    # misc

    @public
    @property
    @_copy_docs_from_op_execution_context
    def resources(self) -> Any:
        return self.op_execution_context.resources

    @property
    @_copy_docs_from_op_execution_context
    def is_subset(self):
        return self.op_execution_context.is_subset

    # In this mode no conversion is done on returned values and missing but expected outputs are not
    # allowed.
    @property
    @_copy_docs_from_op_execution_context
    def requires_typed_event_stream(self) -> bool:
        return self.op_execution_context.requires_typed_event_stream

    @property
    @_copy_docs_from_op_execution_context
    def typed_event_stream_error_message(self) -> Optional[str]:
        return self.op_execution_context.typed_event_stream_error_message

    @_copy_docs_from_op_execution_context
    def set_requires_typed_event_stream(self, *, error_message: Optional[str] = None) -> None:
        self.op_execution_context.set_requires_typed_event_stream(error_message=error_message)

    @_copy_docs_from_op_execution_context
    def load_asset_value(
        self,
        asset_key: AssetKey,
        *,
        python_type: Optional[type] = None,
        partition_key: Optional[str] = None,
    ) -> Any:
        return self.op_execution_context.load_asset_value(
            asset_key=asset_key,
            python_type=python_type,
            partition_key=partition_key,
        )
