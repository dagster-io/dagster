from enum import Enum
from typing import List, NamedTuple

import dagster._check as check
from dagster.serdes import whitelist_for_serdes


@whitelist_for_serdes
class BulkActionType(Enum):
    PARTITION_BACKFILL = "PARTITION_BACKFILL"
    RUN_TERMINATION = "RUN_TERMINATION"


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
class BulkRunAction(
    NamedTuple(
        "_BulkRunAction",
        [
            ("action_id", str),
            ("action_type", BulkActionType),
            ("status", BulkActionStatus),
            ("timestamp", float),
            ("run_ids", List[str]),
        ],
    )
):
    def __new__(
        cls,
        action_id: str,
        action_type: BulkActionType,
        status: BulkActionStatus,
        timestamp: float,
        run_ids: List[str],
    ):
        return super(BulkRunAction, cls).__new__(
            cls,
            check.str_param(action_id, "action_id"),
            check.inst_param(action_type, "action_type", BulkActionType),
            check.inst_param(status, "status", BulkActionStatus),
            check.float_param(timestamp, "timestamp"),
            check.list_param(run_ids, "run_ids", of_type=str),
        )

    def with_status(self, status: BulkActionStatus):
        check.inst_param(status, "status", BulkActionStatus)
        return BulkRunAction(self.action_id, self.action_type, status, self.timestamp, self.run_ids)
