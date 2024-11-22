from typing import Optional, Union

from schema.charts.utils import kubernetes
from schema.charts.utils.utils import BaseModel


class Server(BaseModel):
    host: str
    port: int
    name: Optional[str] = None
    ssl: Optional[bool] = None


class Workspace(BaseModel):
    enabled: bool
    servers: list[Server]
    externalConfigmap: Optional[str] = None


class Webserver(BaseModel, extra="forbid"):
    replicaCount: int
    image: kubernetes.Image
    nameOverride: str
    pathPrefix: Optional[str] = None
    service: kubernetes.Service
    workspace: Workspace
    env: Union[dict[str, str], list[kubernetes.EnvVar]]
    envConfigMaps: list[kubernetes.ConfigMapEnvSource]
    envSecrets: list[kubernetes.SecretEnvSource]
    deploymentLabels: dict[str, str]
    labels: dict[str, str]
    nodeSelector: kubernetes.NodeSelector
    affinity: kubernetes.Affinity
    tolerations: kubernetes.Tolerations
    podSecurityContext: kubernetes.PodSecurityContext
    securityContext: kubernetes.SecurityContext
    resources: kubernetes.Resources
    readinessProbe: kubernetes.ReadinessProbe
    livenessProbe: kubernetes.LivenessProbe
    startupProbe: kubernetes.StartupProbe
    annotations: kubernetes.Annotations
    enableReadOnly: bool
    dbStatementTimeout: Optional[int] = None
    dbPoolRecycle: Optional[int] = None
    logLevel: Optional[str] = None
    schedulerName: Optional[str] = None
    volumeMounts: Optional[list[kubernetes.VolumeMount]] = None
    volumes: Optional[list[kubernetes.Volume]] = None
    initContainerResources: Optional[kubernetes.Resources] = None
