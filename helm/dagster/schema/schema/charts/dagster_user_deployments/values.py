from typing import Union

from pydantic import BaseModel, Field, field_validator

from schema.charts.dagster.subschema import Global, ServiceAccount
from schema.charts.dagster_user_deployments.subschema.user_deployments import (
    UserDeployment,
    UserDeploymentDictEntry,
    normalize_deployments,
)
from schema.charts.utils import kubernetes


class DagsterUserDeploymentsHelmValues(BaseModel):
    __doc__ = "@" + "generated"

    dagsterHome: str
    postgresqlSecretName: str
    celeryConfigSecretName: str
    includeInstance: bool
    deployments: Union[list[UserDeployment], dict[str, UserDeploymentDictEntry]]
    imagePullSecrets: list[kubernetes.SecretRef]
    serviceAccount: ServiceAccount
    global_: Global = Field(..., alias="global")

    @field_validator("deployments", mode="before")
    @classmethod
    def convert_deployments_dict_to_list(
        cls, v: Union[list[UserDeployment], dict[str, UserDeploymentDictEntry]]
    ) -> list[UserDeployment]:
        return normalize_deployments(v)
