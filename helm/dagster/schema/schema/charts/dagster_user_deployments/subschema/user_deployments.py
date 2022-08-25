from typing import Dict, List, Optional

from pydantic import BaseModel

from ...utils import kubernetes


class UserDeploymentIncludeConfigInLaunchedRuns(BaseModel):
    enabled: bool


class UserDeployment(BaseModel):
    name: str
    image: kubernetes.Image
    dagsterApiGrpcArgs: List[str]
    includeConfigInLaunchedRuns: Optional[UserDeploymentIncludeConfigInLaunchedRuns]
    port: int
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
    readinessProbe: Optional[kubernetes.ReadinessProbe]
    startupProbe: Optional[kubernetes.StartupProbe]
    labels: Optional[Dict[str, str]]
    volumeMounts: Optional[List[kubernetes.VolumeMount]]
    volumes: Optional[List[kubernetes.Volume]]
    schedulerName: Optional[str]


class UserDeployments(BaseModel):
    enabled: bool
    enableSubchart: bool
    imagePullSecrets: List[kubernetes.SecretRef]
    deployments: List[UserDeployment]
