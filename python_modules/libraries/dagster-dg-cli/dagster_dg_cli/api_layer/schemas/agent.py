"""Agent models for REST-like API."""

from enum import Enum

from pydantic import BaseModel


class DgApiAgentStatus(str, Enum):
    """Agent status enum for FastAPI compatibility."""

    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    NOT_RUNNING = "NOT_RUNNING"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


class DgApiAgentMetadataEntry(BaseModel):
    """Agent metadata key-value pair."""

    key: str
    value: str


class DgApiAgent(BaseModel):
    """Agent resource model."""

    id: str  # Agent IDs are strings in the GraphQL schema
    agent_label: str | None  # Can be None in some cases
    status: DgApiAgentStatus
    last_heartbeat_time: float | None
    metadata: list[DgApiAgentMetadataEntry]

    class Config:
        from_attributes = True  # For future ORM compatibility


class DgApiAgentList(BaseModel):
    """GET /api/agents response."""

    items: list[DgApiAgent]
    total: int
