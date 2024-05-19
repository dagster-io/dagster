from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance

from .interface import FetchRunEventRecordsResponse, IDeploymentServer


class InMemoryDeploymentServer(IDeploymentServer):
    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

    # TODO: figure out of_type semantics
    def fetch_event_records_for_run(
        self, *, run_id: str, cursor: Optional[str] = None, limit: int = 100, ascending: bool = True
    ) -> FetchRunEventRecordsResponse:
        event_log_conn = self._instance.get_records_for_run(
            run_id=run_id, cursor=cursor, limit=limit, ascending=ascending, of_type=None
        )
        return FetchRunEventRecordsResponse(
            records=event_log_conn.records,
            cursor=event_log_conn.cursor,
            has_more=event_log_conn.has_more,
        )
