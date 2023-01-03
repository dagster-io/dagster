from enum import Enum
from typing import Mapping, NamedTuple, Optional, Sequence

from dagster import _check as check
from dagster._core.definitions import AssetKey
from dagster._core.host_representation.origin import ExternalPartitionSetOrigin
from dagster._serdes import whitelist_for_serdes
from dagster._utils.error import SerializableErrorInfo


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
    ):
        check.invariant(
            not (asset_selection and reexecution_steps),
            "Can't supply both an asset_selection and reexecution_steps to a PartitionBackfill.",
        )
        return super(PartitionBackfill, cls).__new__(
            cls,
            check.str_param(backfill_id, "backfill_id"),
            check.inst_param(status, "status", BulkActionStatus),
            check.bool_param(from_failure, "from_failure"),
            check.opt_mapping_param(tags, "tags", key_type=str, value_type=str),
            check.float_param(backfill_timestamp, "backfill_timestamp"),
            check.opt_inst_param(error, "error", SerializableErrorInfo),
            check.opt_sequence_param(asset_selection, "asset_selection", of_type=AssetKey),
            check.opt_inst_param(
                partition_set_origin, "partition_set_origin", ExternalPartitionSetOrigin
            ),
            check.opt_sequence_param(partition_names, "partition_names", of_type=str),
            check.opt_str_param(last_submitted_partition_name, "last_submitted_partition_name"),
            check.opt_sequence_param(reexecution_steps, "reexecution_steps", of_type=str),
        )

    @property
    def selector_id(self):
        return self.partition_set_origin.get_selector_id() if self.partition_set_origin else None

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
        )
