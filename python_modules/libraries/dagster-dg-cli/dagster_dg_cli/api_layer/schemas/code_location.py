"""Code location models for REST-like API."""

from typing import Any

from pydantic import BaseModel


class DgApiCodeSource(BaseModel):
    """Code source configuration for a code location."""

    python_file: str | None = None
    module_name: str | None = None
    package_name: str | None = None
    autoload_defs_module_name: str | None = None


class DgApiGitMetadata(BaseModel):
    """Git metadata for a code location."""

    commit_hash: str | None = None
    url: str | None = None


class DgApiCodeLocationDocument(BaseModel):
    """Input document for adding or updating a code location."""

    location_name: str
    image: str | None = None
    code_source: DgApiCodeSource | None = None
    working_directory: str | None = None
    executable_path: str | None = None
    attribute: str | None = None
    git: DgApiGitMetadata | None = None

    def to_document_dict(self) -> dict[str, Any]:
        """Convert to a document dict suitable for the GraphQL mutation, stripping None values recursively."""
        return self.model_dump(exclude_none=True)


class DgApiAddCodeLocationResult(BaseModel):
    """Result of adding or updating a code location."""

    location_name: str
