"""Agent models for REST-like API."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AgentStatus(str, Enum):
    """Agent status enum for FastAPI compatibility."""

    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    NOT_RUNNING = "NOT_RUNNING"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


class AgentMetadataEntry(BaseModel):
    """Agent metadata key-value pair."""

    key: str
    value: str


class Agent(BaseModel):
    """Agent resource model."""

    id: str  # Agent IDs are strings in the GraphQL schema
    agent_label: Optional[str]  # Can be None in some cases
    status: AgentStatus
    last_heartbeat_time: Optional[float]
    metadata: list[AgentMetadataEntry]

    class Config:
        from_attributes = True  # For future ORM compatibility


class AgentList(BaseModel):
    """GET /api/agents response."""

    items: list[Agent]
    total: int
