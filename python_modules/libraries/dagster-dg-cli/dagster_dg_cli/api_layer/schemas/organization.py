"""Organization models for REST-like API."""

from typing import Any

from pydantic import BaseModel


class OrganizationSettings(BaseModel):
    """Organization settings resource model."""

    settings: dict[str, Any]
