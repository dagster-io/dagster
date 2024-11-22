from typing import Optional, Union

from pydantic import BaseModel, create_model

from schema.charts.utils import kubernetes


class UserDeploymentIncludeConfigInLaunchedRuns(BaseModel):
    enabled: bool


ReadinessProbeWithEnabled = create_model(
    "ReadinessProbeWithEnabled", __base__=(kubernetes.ReadinessProbe), enabled=(bool, ...)
)


class UserDeployment(BaseModel):
    name: str
    image: kubernetes.Image
    dagsterApiGrpcArgs: Optional[list[str]] = None
    codeServerArgs: Optional[list[str]] = None
    includeConfigInLaunchedRuns: Optional[UserDeploymentIncludeConfigInLaunchedRuns] = None
    deploymentNamespace: Optional[str] = None
    port: int
    env: Optional[Union[dict[str, str], list[kubernetes.EnvVar]]] = None
    envConfigMaps: Optional[list[kubernetes.ConfigMapEnvSource]] = None
    envSecrets: Optional[list[kubernetes.SecretEnvSource]] = None
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
    labels: Optional[dict[str, str]] = None
    volumeMounts: Optional[list[kubernetes.VolumeMount]] = None
    volumes: Optional[list[kubernetes.Volume]] = None
    schedulerName: Optional[str] = None
    initContainers: Optional[list[kubernetes.Container]] = None
    sidecarContainers: Optional[list[kubernetes.Container]] = None


class UserDeployments(BaseModel):
    enabled: bool
    enableSubchart: bool
    imagePullSecrets: list[kubernetes.SecretRef]
    deployments: list[UserDeployment]
