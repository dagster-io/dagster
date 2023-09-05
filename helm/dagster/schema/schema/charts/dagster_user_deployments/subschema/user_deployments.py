from typing import Dict, List, Optional, Union

from pydantic import BaseModel, create_model

from ...utils import kubernetes


class UserDeploymentIncludeConfigInLaunchedRuns(BaseModel):
    enabled: bool


ReadinessProbeWithEnabled = create_model(
    "ReadinessProbeWithEnabled", __base__=(kubernetes.ReadinessProbe), enabled=(bool, ...)
)


class UserDeployment(BaseModel):
    name: str
    image: kubernetes.Image
    port: int
    dagsterApiGrpcArgs: Optional[List[str]] = None
    codeServerArgs: Optional[List[str]] = None
    includeConfigInLaunchedRuns: Optional[UserDeploymentIncludeConfigInLaunchedRuns] = None
    env: Optional[Union[Dict[str, str], List[kubernetes.EnvVar]]] = None
    envConfigMaps: Optional[List[kubernetes.ConfigMapEnvSource]] = None
    envSecrets: Optional[List[kubernetes.SecretEnvSource]] = None
    annotations: Optional[kubernetes.Annotations] = None
    nodeSelector: Optional[kubernetes.NodeSelector] = None
    affinity: Optional[kubernetes.Affinity] = None
    tolerations: Optional[kubernetes.Tolerations] = None
    podSecurityContext: Optional[kubernetes.PodSecurityContext] = None
    securityContext: Optional[kubernetes.SecurityContext] = None
    resources: Optional[kubernetes.Resources] = None
    livenessProbe: Optional[kubernetes.LivenessProbe] = None
    readinessProbe: Optional[ReadinessProbeWithEnabled] = None
    startupProbe: Optional[kubernetes.StartupProbe] = None
    labels: Optional[Dict[str, str]] = None
    volumeMounts: Optional[List[kubernetes.VolumeMount]] = None
    volumes: Optional[List[kubernetes.Volume]] = None
    schedulerName: Optional[str] = None


class UserDeployments(BaseModel):
    enabled: bool
    enableSubchart: bool
    imagePullSecrets: List[kubernetes.SecretRef]
    deployments: List[UserDeployment]
