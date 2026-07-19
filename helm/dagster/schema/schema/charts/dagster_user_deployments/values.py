from pydantic import BaseModel, Field

from schema.charts.dagster.subschema import Global, ServiceAccount
from schema.charts.dagster_user_deployments.subschema.user_deployments import UserDeploymentsValue
from schema.charts.utils import kubernetes


class DagsterUserDeploymentsHelmValues(BaseModel):
    __doc__ = "@" + "generated"

    dagsterHome: str
    postgresqlSecretName: str
    celeryConfigSecretName: str
    includeInstance: bool
    deployments: UserDeploymentsValue
    imagePullSecrets: list[kubernetes.SecretRef]
    serviceAccount: ServiceAccount
    global_: Global = Field(..., alias="global")
