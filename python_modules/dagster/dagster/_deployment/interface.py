from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Sequence

from dagster._core.event_api import EventLogRecord


@dataclass(frozen=True)
class FetchRunEventRecordsResponse:
    records: Sequence[EventLogRecord]
    ...


class IDeploymentServer(ABC):
    @abstractmethod
    # TODO: rethink "of_type" parameter on get_records_for_run
    def fetch_event_records_for_run(
        self, *, run_id: str, cursor: Optional[str] = None, limit: int = 100, ascending: bool = True
    ) -> FetchRunEventRecordsResponse: ...
