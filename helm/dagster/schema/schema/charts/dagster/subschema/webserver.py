from typing import Dict, List, Optional, Union

from pydantic import Extra

from ...utils import kubernetes
from ...utils.utils import BaseModel


class Server(BaseModel):
    name: Optional[str] = None
    ssl: Optional[bool] = None
    host: str
    port: int


class Workspace(BaseModel):
    externalConfigmap: Optional[str] = None
    enabled: bool
    servers: List[Server]


class Webserver(BaseModel, extra="allow"):
    dbStatementTimeout: Optional[int] = None
    dbPoolRecycle: Optional[int] = None
    logLevel: Optional[str] = None
    schedulerName: Optional[str] = None
    volumeMounts: Optional[List[kubernetes.VolumeMount]] = None
    volumes: Optional[List[kubernetes.Volume]] = None
    pathPrefix: Optional[str] = None
    replicaCount: int
    image: kubernetes.Image
    nameOverride: str
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
    resources: kubernetes.Resources
    readinessProbe: kubernetes.ReadinessProbe
    livenessProbe: kubernetes.LivenessProbe
    startupProbe: kubernetes.StartupProbe
    annotations: kubernetes.Annotations
    enableReadOnly: bool

    class Config:
        extra = Extra.forbid
