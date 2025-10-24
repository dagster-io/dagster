"""Secret models for REST-like API."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DgApiSecretScope(str, Enum):
    """Secret scope enum for filtering."""

    DEPLOYMENT = "deployment"
    ORGANIZATION = "organization"


class DgApiUpdatedBy(BaseModel):
    """User who last updated the secret."""

    email: str


class DgApiSecret(BaseModel):
    """Secret resource model."""

    id: str
    name: str = Field(alias="secretName")  # GraphQL field is secretName
    value: Optional[str] = Field(
        alias="secretValue", default=None
    )  # Hidden by default for security
    location_names: list[str] = Field(alias="locationNames")
    full_deployment_scope: bool = Field(alias="fullDeploymentScope")
    all_branch_deployments_scope: bool = Field(alias="allBranchDeploymentsScope")
    specific_branch_deployment_scope: Optional[str] = Field(
        alias="specificBranchDeploymentScope", default=None
    )
    local_deployment_scope: bool = Field(alias="localDeploymentScope")
    can_view_secret_value: bool = Field(alias="canViewSecretValue")
    can_edit_secret: bool = Field(alias="canEditSecret")
    updated_by: Optional[DgApiUpdatedBy] = Field(alias="updatedBy", default=None)
    update_timestamp: Optional[datetime] = Field(alias="updateTimestamp", default=None)

    class Config:
        from_attributes = True  # For future ORM compatibility
        populate_by_name = True  # Allow both alias and field name (Pydantic V2)


class DgApiSecretList(BaseModel):
    """GET /api/secrets response."""

    items: list[DgApiSecret]
    total: int


class DgApiSecretScopesInput(BaseModel):
    """GraphQL SecretScopesInput type for filtering."""

    full_deployment_scope: Optional[bool] = Field(alias="fullDeploymentScope", default=None)
    all_branch_deployments_scope: Optional[bool] = Field(
        alias="allBranchDeploymentsScope", default=None
    )
    specific_branch_deployment_scope: Optional[str] = Field(
        alias="specificBranchDeploymentScope", default=None
    )
    local_deployment_scope: Optional[bool] = Field(alias="localDeploymentScope", default=None)

    class Config:
        populate_by_name = True  # Pydantic V2 equivalent of allow_population_by_field_name

    def to_dict(self) -> dict:
        """Convert to dict for GraphQL variables, excluding None values."""
        result = {}
        if self.full_deployment_scope is not None:
            result["fullDeploymentScope"] = self.full_deployment_scope
        if self.all_branch_deployments_scope is not None:
            result["allBranchDeploymentsScope"] = self.all_branch_deployments_scope
        if self.specific_branch_deployment_scope is not None:
            result["specificBranchDeploymentScope"] = self.specific_branch_deployment_scope
        if self.local_deployment_scope is not None:
            result["localDeploymentScope"] = self.local_deployment_scope
        return result
