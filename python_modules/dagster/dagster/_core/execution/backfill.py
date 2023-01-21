from enum import Enum
from typing import Dict, Mapping, NamedTuple, Optional, Sequence, Set

from dagster import _check as check
from dagster._core.definitions import AssetKey
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.partition import PartitionsSubset
from dagster._core.errors import DagsterDefinitionChangedDeserializationError
from dagster._core.execution.bulk_actions import BulkActionType
from dagster._core.host_representation.origin import ExternalPartitionSetOrigin
from dagster._core.workspace.workspace import IWorkspace
from dagster._serdes import whitelist_for_serdes
from dagster._utils.error import SerializableErrorInfo

from .asset_backfill import AssetBackfillData


@whitelist_for_serdes
class BulkActionStatus(Enum):
    REQUESTED = "REQUESTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

    @staticmethod
    def from_graphql_input(graphql_str):
        return BulkActionStatus(graphql_str)


@whitelist_for_serdes
class PartitionBackfill(
    NamedTuple(
        "_PartitionBackfill",
        [
            ("backfill_id", str),
            ("status", BulkActionStatus),
            ("from_failure", bool),
            ("tags", Mapping[str, str]),
            ("backfill_timestamp", float),
            ("error", Optional[SerializableErrorInfo]),
            ("asset_selection", Optional[Sequence[AssetKey]]),
            # fields that are only used by job backfills
            ("partition_set_origin", Optional[ExternalPartitionSetOrigin]),
            ("partition_names", Optional[Sequence[str]]),
            ("last_submitted_partition_name", Optional[str]),
            ("reexecution_steps", Optional[Sequence[str]]),
            # only used by asset backfills
            ("serialized_asset_backfill_data", Optional[str]),
        ],
    ),
):
    def __new__(
        cls,
        backfill_id: str,
        status: BulkActionStatus,
        from_failure: bool,
        tags: Mapping[str, str],
        backfill_timestamp: float,
        error: Optional[SerializableErrorInfo] = None,
        asset_selection: Optional[Sequence[AssetKey]] = None,
        partition_set_origin: Optional[ExternalPartitionSetOrigin] = None,
        partition_names: Optional[Sequence[str]] = None,
        last_submitted_partition_name: Optional[str] = None,
        reexecution_steps: Optional[Sequence[str]] = None,
        serialized_asset_backfill_data: Optional[str] = None,
    ):
        check.invariant(
            not (asset_selection and reexecution_steps),
            "Can't supply both an asset_selection and reexecution_steps to a PartitionBackfill.",
        )

        if serialized_asset_backfill_data is not None:
            check.invariant(partition_set_origin is None)
            check.invariant(partition_names is None)
            check.invariant(last_submitted_partition_name is None)
            check.invariant(reexecution_steps is None)

        return super(PartitionBackfill, cls).__new__(
            cls,
            check.str_param(backfill_id, "backfill_id"),
            check.inst_param(status, "status", BulkActionStatus),
            check.bool_param(from_failure, "from_failure"),
            check.opt_mapping_param(tags, "tags", key_type=str, value_type=str),
            check.float_param(backfill_timestamp, "backfill_timestamp"),
            check.opt_inst_param(error, "error", SerializableErrorInfo),
            check.opt_nullable_sequence_param(asset_selection, "asset_selection", of_type=AssetKey),
            check.opt_inst_param(
                partition_set_origin, "partition_set_origin", ExternalPartitionSetOrigin
            ),
            check.opt_nullable_sequence_param(partition_names, "partition_names", of_type=str),
            check.opt_str_param(last_submitted_partition_name, "last_submitted_partition_name"),
            check.opt_nullable_sequence_param(reexecution_steps, "reexecution_steps", of_type=str),
            check.opt_str_param(serialized_asset_backfill_data, "serialized_asset_backfill_data"),
        )

    @property
    def selector_id(self):
        return self.partition_set_origin.get_selector_id() if self.partition_set_origin else None

    @property
    def is_asset_backfill(self) -> bool:
        return self.serialized_asset_backfill_data is not None

    @property
    def bulk_action_type(self) -> BulkActionType:
        if self.is_asset_backfill:
            return BulkActionType.MULTI_RUN_ASSET_ACTION
        else:
            return BulkActionType.PARTITION_BACKFILL

    @property
    def partition_set_name(self) -> Optional[str]:
        if self.partition_set_origin is None:
            return None

        return self.partition_set_origin.partition_set_name

    def get_num_partitions(self, workspace: IWorkspace) -> int:
        if self.serialized_asset_backfill_data is not None:
            try:
                asset_backfill_data = AssetBackfillData.from_serialized(
                    self.serialized_asset_backfill_data,
                    ExternalAssetGraph.from_workspace(workspace),
                )
            except DagsterDefinitionChangedDeserializationError:
                return 0

            return asset_backfill_data.get_num_partitions()
        else:
            if self.partition_names is None:
                check.failed("Non-asset backfills should have a non-null partition_names field")

            return len(self.partition_names)

    def get_partition_names(self, workspace: IWorkspace) -> Sequence[str]:
        if self.serialized_asset_backfill_data is not None:
            try:
                asset_backfill_data = AssetBackfillData.from_serialized(
                    self.serialized_asset_backfill_data,
                    ExternalAssetGraph.from_workspace(workspace),
                )
            except DagsterDefinitionChangedDeserializationError:
                return []

            return asset_backfill_data.get_partition_names()
        else:
            if self.partition_names is None:
                check.failed("Non-asset backfills should have a non-null partition_names field")

            return self.partition_names

    def get_num_cancelable(self) -> int:
        if self.is_asset_backfill:
            return 0

        if self.status != BulkActionStatus.REQUESTED:
            return 0

        if self.partition_names is None:
            check.failed("Expected partition_names to not be None for job backfill")

        checkpoint = self.last_submitted_partition_name
        total_count = len(self.partition_names)
        checkpoint_idx = (
            self.partition_names.index(checkpoint) + 1
            if checkpoint and checkpoint in self.partition_names
            else 0
        )
        return max(0, total_count - checkpoint_idx)

    def with_status(self, status):
        check.inst_param(status, "status", BulkActionStatus)
        return PartitionBackfill(
            status=status,
            backfill_id=self.backfill_id,
            partition_set_origin=self.partition_set_origin,
            partition_names=self.partition_names,
            from_failure=self.from_failure,
            reexecution_steps=self.reexecution_steps,
            tags=self.tags,
            backfill_timestamp=self.backfill_timestamp,
            last_submitted_partition_name=self.last_submitted_partition_name,
            error=self.error,
            asset_selection=self.asset_selection,
            serialized_asset_backfill_data=self.serialized_asset_backfill_data,
        )

    def with_partition_checkpoint(self, last_submitted_partition_name):
        check.str_param(last_submitted_partition_name, "last_submitted_partition_name")
        return PartitionBackfill(
            status=self.status,
            backfill_id=self.backfill_id,
            partition_set_origin=self.partition_set_origin,
            partition_names=self.partition_names,
            from_failure=self.from_failure,
            reexecution_steps=self.reexecution_steps,
            tags=self.tags,
            backfill_timestamp=self.backfill_timestamp,
            last_submitted_partition_name=last_submitted_partition_name,
            error=self.error,
            asset_selection=self.asset_selection,
            serialized_asset_backfill_data=self.serialized_asset_backfill_data,
        )

    def with_error(self, error):
        check.opt_inst_param(error, "error", SerializableErrorInfo)
        return PartitionBackfill(
            status=self.status,
            backfill_id=self.backfill_id,
            partition_set_origin=self.partition_set_origin,
            partition_names=self.partition_names,
            from_failure=self.from_failure,
            reexecution_steps=self.reexecution_steps,
            tags=self.tags,
            backfill_timestamp=self.backfill_timestamp,
            last_submitted_partition_name=self.last_submitted_partition_name,
            error=error,
            asset_selection=self.asset_selection,
            serialized_asset_backfill_data=self.serialized_asset_backfill_data,
        )

    def with_asset_backfill_data(
        self, asset_backfill_data: AssetBackfillData
    ) -> "PartitionBackfill":
        return PartitionBackfill(
            status=self.status,
            backfill_id=self.backfill_id,
            partition_set_origin=self.partition_set_origin,
            partition_names=self.partition_names,
            from_failure=self.from_failure,
            reexecution_steps=self.reexecution_steps,
            tags=self.tags,
            backfill_timestamp=self.backfill_timestamp,
            last_submitted_partition_name=self.last_submitted_partition_name,
            error=self.error,
            asset_selection=self.asset_selection,
            serialized_asset_backfill_data=asset_backfill_data.serialize(),
        )

    @classmethod
    def from_asset_partitions(
        cls,
        backfill_id: str,
        asset_graph: AssetGraph,
        partition_names: Sequence[str],
        asset_selection: Sequence[AssetKey],
        backfill_timestamp: float,
        tags: Mapping[str, str],
    ) -> "PartitionBackfill":
        target_subsets_by_asset_key: Dict[AssetKey, PartitionsSubset] = {}
        non_partitioned_asset_keys: Set[AssetKey] = set()
        for asset_key in asset_selection:
            partitions_def = asset_graph.get_partitions_def(asset_key)
            if partitions_def:
                target_subsets_by_asset_key[
                    asset_key
                ] = partitions_def.empty_subset().with_partition_keys(partition_names)
            else:
                non_partitioned_asset_keys.add(asset_key)

        return cls(
            backfill_id=backfill_id,
            status=BulkActionStatus.REQUESTED,
            from_failure=False,
            tags=tags,
            backfill_timestamp=backfill_timestamp,
            asset_selection=asset_selection,
            serialized_asset_backfill_data=AssetBackfillData.empty(
                AssetGraphSubset(
                    asset_graph, target_subsets_by_asset_key, non_partitioned_asset_keys
                )
            ).serialize(),
        )
