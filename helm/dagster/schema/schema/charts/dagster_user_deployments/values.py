from typing import List

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from ..utils import kubernetes
from .subschema.user_deployments import UserDeployment


class DagsterUserDeploymentsHelmValues(BaseModel):
    __doc__ = "@" + "generated"

    deployments: List[UserDeployment]
    imagePullSecrets: List[kubernetes.SecretRef]
