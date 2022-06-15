from enum import Enum
from typing import Any, NamedTuple

import dagster._check as check
from dagster.core.storage.pipeline_run import RunsFilter
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
class RunTerminationAction(NamedTuple("RunTerminationAction", [("runs_filter", RunsFilter)])):
    def __new__(cls, runs_filter: RunsFilter):
        return super(RunTerminationAction, cls).__new__(
            cls, check.inst_param(runs_filter, "runs_filter", RunsFilter)
        )


@whitelist_for_serdes
class BulkAction(
    NamedTuple(
        "_BulkAction",
        [
            ("action_id", str),
            ("type", BulkActionType),
            ("status", BulkActionStatus),
            ("timestamp", float),
            ("action_data", Any),
        ],
    )
):
    def __new__(
        cls,
        action_id: str,
        type: BulkActionType,
        status: BulkActionStatus,
        timestamp: float,
        action_data: Any,
    ):
        check.str_param(action_id, "action_id")
        check.inst_param(type, "type", BulkActionType)
        check.inst_param(status, "status", BulkActionStatus)
        check.float_param(timestamp, "timestamp")

        if type == BulkActionType.RUN_TERMINATION:
            check.inst_param(action_data, "action_data", RunTerminationAction)

        return super(BulkAction, cls).__new__(cls, action_id, type, status, timestamp, action_data)

    def with_status(self, status: BulkActionStatus):
        check.inst_param(status, "status", BulkActionStatus)
        return BulkAction(self.action_id, self.type, status, self.timestamp, self.action_data)
