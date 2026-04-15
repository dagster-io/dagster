"""SAML operation models."""

from pydantic import BaseModel


class SamlOperationResult(BaseModel):
    """Result of a SAML upload or remove operation."""

    message: str
