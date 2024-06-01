from abc import ABC, abstractmethod
from typing import Optional, Sequence

from pydantic import BaseModel

from dagster._core.event_api import EventLogRecord


class FetchRunEventRecordsResponse(BaseModel, arbitrary_types_allowed=True):
    records: Sequence[EventLogRecord]
    cursor: str
    has_more: bool


class IDeploymentServer(ABC):
    @abstractmethod
    # TODO: rethink "of_type" parameter on get_records_for_run
    def fetch_event_records_for_run(
        self, *, run_id: str, cursor: Optional[str] = None, limit: int = 100, ascending: bool = True
    ) -> FetchRunEventRecordsResponse: ...
