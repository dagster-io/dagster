"""Issue schema definitions."""

from enum import Enum

from pydantic import BaseModel


class DgApiIssueStatus(str, Enum):
    """Issue status."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"


class DgApiIssue(BaseModel):
    """Single issue model."""

    id: str
    title: str
    description: str
    status: DgApiIssueStatus
    created_by_email: str
    run_id: str | None = None
    asset_key: list[str] | None = None
    context: str | None = None


class DgApiIssueList(BaseModel):
    """List of issues with pagination support."""

    items: list[DgApiIssue]
    cursor: str | None = None
    has_more: bool = False
