"""Run event schema definitions."""

from pydantic import BaseModel

from dagster_rest_resources.schemas.enums import DgApiLogLevel
from dagster_rest_resources.schemas.util import DgApiPaginatedList


class DgApiErrorInfo(BaseModel):
    """Error information model."""

    message: str
    className: str | None = None
    stack: list[str] | None = None
    cause: "DgApiErrorInfo | None" = None

    def get_stack_trace_string(self) -> str:
        if not self.stack:
            return ""
        return "\n".join(self.stack)


class DgApiRunEvent(BaseModel):
    """Single run event model."""

    run_id: str
    message: str
    timestamp: str
    level: DgApiLogLevel
    step_key: str | None = None
    event_type: str | None = None
    error: DgApiErrorInfo | None = None


class DgApiRunEventList(DgApiPaginatedList["DgApiRunEvent"]):
    pass
