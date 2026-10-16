from typing import Any

from pydantic import BaseModel

from dagster_rest_resources.__generated__.enums import DeploymentAgentType, DeploymentStatus
from dagster_rest_resources.schemas.enums import DgApiDagsterCloudDeploymentType
from dagster_rest_resources.schemas.util import DgApiTruncatedList


class DgApiDeployment(BaseModel):
    id: int
    name: str
    type: DgApiDagsterCloudDeploymentType
    status: DeploymentStatus | None = None
    agent_type: DeploymentAgentType | None = None
    is_branch_deployment: bool | None = None
    organization_name: str | None = None


class DgApiDeploymentList(DgApiTruncatedList[DgApiDeployment]):
    pass


class DgApiDeploymentSettings(BaseModel):
    settings: dict[str, Any]
