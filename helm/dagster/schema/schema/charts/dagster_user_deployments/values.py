from typing import List

from pydantic import BaseModel, Field

from schema.charts.dagster.subschema import Global, ServiceAccount
from schema.charts.dagster_user_deployments.subschema.user_deployments import UserDeployment
from schema.charts.utils import kubernetes


class DagsterUserDeploymentsHelmValues(BaseModel):
    __doc__ = "@" + "generated"

    dagsterHome: str
    postgresqlSecretName: str
    celeryConfigSecretName: str
    deployments: List[UserDeployment]
    imagePullSecrets: List[kubernetes.SecretRef]
    serviceAccount: ServiceAccount
    global_: Global = Field(..., alias="global")
