"""Alert policy models for REST-like API."""

from typing import Any

from pydantic import BaseModel


class AlertPolicyDocument(BaseModel):
    """Alert policies as a document (YAML-compatible dict)."""

    alert_policies: list[dict[str, Any]]


class AlertPolicySyncResult(BaseModel):
    """Result of syncing alert policies."""

    synced_policies: list[str]
