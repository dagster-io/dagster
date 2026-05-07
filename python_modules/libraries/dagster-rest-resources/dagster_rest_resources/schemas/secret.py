from pydantic import BaseModel

from dagster_rest_resources.schemas.util import DgApiTruncatedList


class DgApiUpdatedBy(BaseModel):
    email: str


class DgApiSecret(BaseModel):
    id: str
    name: str
    value: str | None = None
    location_names: list[str]
    full_deployment_scope: bool
    all_branch_deployments_scope: bool
    specific_branch_deployment_scope: str | None = None
    local_deployment_scope: bool
    can_view_secret_value: bool
    can_edit_secret: bool
    updated_by: DgApiUpdatedBy | None = None
    update_timestamp: float | None = None


class DgApiSecretList(DgApiTruncatedList["DgApiSecret"]):
    pass
