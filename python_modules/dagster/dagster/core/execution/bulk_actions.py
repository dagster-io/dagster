from enum import Enum
from typing import TYPE_CHECKING, NamedTuple, Optional

import dagster._check as check
from dagster.serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from .backfill import PartitionBackfill


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
class BulkActionType(Enum):
    PARITION_BACKFILL = "PARTITION_BACKFILL"
    RUN_TERMINATION = "RUN_TERMINATION"


@whitelist_for_serdes
class BulkAction(
    NamedTuple(
        "BulkAction",
        [
            ("action_id", str),
            ("action_type", BulkActionType),
            ("status", BulkActionStatus),
            ("timestamp", float),
            ("parition_backfill", Optional["PartitionBackfill"]),
        ],
    )
):
    def __new__(cls, action_id, action_type, status, timestamp, partition_backfill=None):
        from .backfill import PartitionBackfill

        return super().__new__(
            cls,
            check.str_param(action_id, "action_id"),
            check.inst_param(action_type, "action_type", BulkActionType),
            check.inst_param(status, "status", BulkActionStatus),
            check.float_param(timestamp, "timestamp"),
            check.opt_inst_param(partition_backfill, "partition_backfill", PartitionBackfill),
        )

    @classmethod
    def from_partition_backfill(cls, partition_backfill: "PartitionBackfill"):
        from .backfill import PartitionBackfill

        check.inst_param(partition_backfill, "partition_backfill", PartitionBackfill)
        return cls(
            action_id=partition_backfill.backfill_id,
            action_type=BulkActionType.PARITION_BACKFILL,
            status=partition_backfill.status,
            timestamp=partition_backfill.backfill_timestamp,
            partition_backfill=partition_backfill,
        )
