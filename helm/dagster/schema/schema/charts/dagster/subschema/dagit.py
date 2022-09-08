from typing import Dict, List, Optional

from pydantic import Extra

from ...utils import kubernetes
from ...utils.utils import BaseModel


class Server(BaseModel):
    host: str
    port: int
    name: Optional[str]


class Workspace(BaseModel):
    enabled: bool
    servers: List[Server]
    externalConfigmap: Optional[str]


class Dagit(BaseModel):
    replicaCount: int
    image: kubernetes.Image
    nameOverride: str
    service: kubernetes.Service
    workspace: Workspace
    env: Dict[str, str]
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
    dbStatementTimeout: Optional[int]
    logLevel: Optional[str]
    schedulerName: Optional[str]

    class Config:
        extra = Extra.forbid
