from typing import List

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from .subschema.user_deployments import UserDeployment
from ..dagster.subschema import Global, ServiceAccount
from ..utils import kubernetes


class DagsterUserDeploymentsHelmValues(BaseModel):
    __doc__ = "@" + "generated"

    dagsterHome: str
    postgresqlSecretName: str
    deployments: List[UserDeployment]
    imagePullSecrets: List[kubernetes.SecretRef]
    serviceAccount: ServiceAccount
    global_: Global = Field(..., alias="global")
