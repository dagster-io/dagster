"""Deployment models for REST-like API."""

from enum import Enum

from pydantic import BaseModel


class DeploymentType(str, Enum):
    """Deployment type enum for FastAPI compatibility."""

    PRODUCTION = "PRODUCTION"
    BRANCH = "BRANCH"


class Deployment(BaseModel):
    """Deployment resource model."""

    id: int  # Deployment IDs are integers in the GraphQL schema
    name: str
    type: DeploymentType

    class Config:
        from_attributes = True  # For future ORM compatibility


class DeploymentList(BaseModel):
    """GET /api/deployments response."""

    items: list[Deployment]
    total: int
