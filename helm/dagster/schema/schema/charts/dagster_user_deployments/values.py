from typing import List

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from .subschema.user_deployments import UserDeployment
from ..utils import kubernetes


class DagsterUserDeploymentsHelmValues(BaseModel):
    __doc__ = "@" + "generated"

    deployments: List[UserDeployment]
    imagePullSecrets: List[kubernetes.SecretRef]
