from typing import Dict, List, Optional, Union

from schema.charts.utils import kubernetes
from schema.charts.utils.utils import BaseModel


class Server(BaseModel):
    host: str
    port: int
    name: Optional[str] = None
    ssl: Optional[bool] = None


class Workspace(BaseModel):
    enabled: bool
    servers: List[Server]
    externalConfigmap: Optional[str] = None


class Webserver(BaseModel, extra="forbid"):
    replicaCount: int
    image: kubernetes.Image
    nameOverride: str
    pathPrefix: Optional[str] = None
    service: kubernetes.Service
    workspace: Workspace
    env: Union[Dict[str, str], List[kubernetes.EnvVar]]
    envConfigMaps: List[kubernetes.ConfigMapEnvSource]
    envSecrets: List[kubernetes.SecretEnvSource]
    deploymentLabels: Dict[str, str]
    labels: Dict[str, str]
    nodeSelector: kubernetes.NodeSelector
    affinity: kubernetes.Affinity
    tolerations: kubernetes.Tolerations
    podSecurityContext: kubernetes.PodSecurityContext
    securityContext: kubernetes.SecurityContext
    checkDbReadyInitContainer: Optional[bool] = None
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
    volumeMounts: Optional[List[kubernetes.VolumeMount]] = None
    volumes: Optional[List[kubernetes.Volume]] = None
    initContainerResources: Optional[kubernetes.Resources] = None
