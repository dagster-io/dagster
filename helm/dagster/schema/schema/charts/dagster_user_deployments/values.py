from typing import List

from pydantic import Field, BaseModel

from ..utils import kubernetes
from ..dagster.subschema import Global, ServiceAccount
from .subschema.user_deployments import UserDeployment


class DagsterUserDeploymentsHelmValues(BaseModel):
    __doc__ = "@" + "generated"

    dagsterHome: str
    postgresqlSecretName: str
    celeryConfigSecretName: str
    deployments: List[UserDeployment]
    imagePullSecrets: List[kubernetes.SecretRef]
    serviceAccount: ServiceAccount
    global_: Global = Field(..., alias="global")
