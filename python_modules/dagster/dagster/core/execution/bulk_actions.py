from enum import Enum
from typing import NamedTuple

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
class BulkAction(
    NamedTuple(
        "_BulkAction",
        [
            ("action_id", str),
            ("type", BulkActionType),
            ("status", BulkActionStatus),
            ("timestamp", float),
        ],
    )
):
    def __new__(
        cls, action_id: str, type: BulkActionType, status: BulkActionStatus, timestamp: float
    ):
        return super(BulkAction, cls).__new__(
            cls, check.str_param(action_id, "action_id"), type, status, timestamp
        )
