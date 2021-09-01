from typing import Dict, List, Optional

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from ...utils import kubernetes


class UserDeployment(BaseModel):
    name: str
    image: kubernetes.Image
    dagsterApiGrpcArgs: List[str]
    port: int
    replicaCount: Optional[int] = 1
    env: Optional[Dict[str, str]]
    envConfigMaps: Optional[List[kubernetes.ConfigMapEnvSource]]
    envSecrets: Optional[List[kubernetes.SecretEnvSource]]
    annotations: Optional[kubernetes.Annotations]
    nodeSelector: Optional[kubernetes.NodeSelector]
    affinity: Optional[kubernetes.Affinity]
    tolerations: Optional[kubernetes.Tolerations]
    podSecurityContext: Optional[kubernetes.PodSecurityContext]
    securityContext: Optional[kubernetes.SecurityContext]
    resources: Optional[kubernetes.Resources]
    livenessProbe: Optional[kubernetes.LivenessProbe]
    startupProbe: Optional[kubernetes.StartupProbe]
    labels: Optional[Dict[str, str]]


class UserDeployments(BaseModel):
    enabled: bool
    enableSubchart: bool
    deployments: List[UserDeployment]
