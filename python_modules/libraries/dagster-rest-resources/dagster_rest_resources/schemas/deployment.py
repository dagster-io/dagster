from typing import Any

from pydantic import BaseModel

from dagster_rest_resources.schemas.enums import DgApiDagsterCloudDeploymentType
from dagster_rest_resources.schemas.util import DgApiTruncatedList


class DgApiDeployment(BaseModel):
    id: int
    name: str
    type: DgApiDagsterCloudDeploymentType


class DgApiDeploymentList(DgApiTruncatedList[DgApiDeployment]):
    pass


class DgApiDeploymentSettings(BaseModel):
    settings: dict[str, Any]
