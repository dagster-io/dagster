import enum
from typing import NamedTuple, Optional

from dagster import EventLogEntry


class AssetCheckExecutionStatus(enum.Enum):
    PLANNED = "PLANNED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class AssetCheckExecutionRecord(NamedTuple):
    id: int
    run_id: str
    status: AssetCheckExecutionStatus
    evaluation_event: Optional[EventLogEntry]
    create_timestamp: float
