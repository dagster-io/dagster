from typing import List

from pydantic import BaseModel, Field

from ..dagster.subschema import Global, ServiceAccount
from ..utils import kubernetes
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
