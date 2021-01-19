from typing import Dict, List, Optional

from pydantic import BaseModel  # pylint: disable=E0611

from .kubernetes import (
    Affinity,
    Image,
    LivenessProbe,
    NodeSelector,
    PodSecurityContext,
    Resources,
    SecurityContext,
    StartupProbe,
    Tolerations,
)


class UserDeployment(BaseModel):
    name: str
    image: Image
    dagsterApiGrpcArgs: List[str]
    port: int
    env: Optional[Dict[str, str]]
    env_config_maps: Optional[List[str]]
    env_secrets: Optional[List[str]]
    nodeSelector: Optional[NodeSelector]
    affinity: Optional[Affinity]
    tolerations: Optional[Tolerations]
    podSecurityContext: Optional[PodSecurityContext]
    securityContext: Optional[SecurityContext]
    resources: Optional[Resources]
    replicaCount: Optional[int]
    livenessProbe: Optional[LivenessProbe]
    startupProbe: Optional[StartupProbe]


class UserDeployments(BaseModel):
    enabled: bool
    deployments: List[UserDeployment]
