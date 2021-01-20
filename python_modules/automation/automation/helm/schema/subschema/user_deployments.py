from typing import Dict, List, Optional

from pydantic import BaseModel  # pylint: disable=E0611

from . import kubernetes


class UserDeployment(BaseModel):
    name: str
    image: kubernetes.Image
    dagsterApiGrpcArgs: List[str]
    port: int
    env: Optional[Dict[str, str]]
    envConfigMaps: Optional[List[kubernetes.ConfigMapEnvSource]]
    envSecrets: Optional[List[kubernetes.SecretEnvSource]]
    nodeSelector: Optional[kubernetes.NodeSelector]
    affinity: Optional[kubernetes.Affinity]
    tolerations: Optional[kubernetes.Tolerations]
    podSecurityContext: Optional[kubernetes.PodSecurityContext]
    securityContext: Optional[kubernetes.SecurityContext]
    resources: Optional[kubernetes.Resources]
    replicaCount: Optional[int]
    livenessProbe: Optional[kubernetes.LivenessProbe]
    startupProbe: Optional[kubernetes.StartupProbe]


class UserDeployments(BaseModel):
    enabled: bool
    deployments: List[UserDeployment]
