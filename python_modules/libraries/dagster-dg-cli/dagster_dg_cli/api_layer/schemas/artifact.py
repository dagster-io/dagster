"""Artifact upload/download models."""

from pydantic import BaseModel


class ArtifactUploadResult(BaseModel):
    """Result of an artifact upload operation."""

    key: str
    scope: str
    deployment: str | None = None


class ArtifactDownloadResult(BaseModel):
    """Result of an artifact download operation."""

    key: str
    path: str
    scope: str
    deployment: str | None = None
