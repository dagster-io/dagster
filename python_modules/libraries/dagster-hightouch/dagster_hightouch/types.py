from collections import namedtuple
from typing import Any, NamedTuple


class HightouchOutput(
    NamedTuple(
        "_HightouchOutput",
        [
            ("sync_details", dict[str, Any]),
            ("sync_run_details", dict[str, Any]),
            ("destination_details", dict[str, Any]),
        ],
    )
):
    """Contains recorded information about the state of a Hightouch sync after a sync completes.

    Attributes:
        sync_details (Dict[str, Any]):
            https://hightouch.io/docs/api-reference/#operation/GetSync
        sync_run_details (Dict[str, Any]):
            https://hightouch.io/docs/api-reference/#operation/ListSyncRuns
        destination_details (Dict[str, Any]):
            https://hightouch.io/docs/api-reference/#operation/GetDestination
    """


SyncRunParsedOutput = namedtuple(
    "_SyncRunParsedOutput",
    [
        "created_at",
        "started_at",
        "finished_at",
        "elapsed_seconds",
        "planned_add",
        "planned_change",
        "planned_remove",
        "successful_add",
        "successful_change",
        "successful_remove",
        "failed_add",
        "failed_change",
        "failed_remove",
        "query_size",
        "status",
        "completion_ratio",
        "error",
    ],
)
