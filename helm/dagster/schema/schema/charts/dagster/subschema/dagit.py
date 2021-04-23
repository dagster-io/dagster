from typing import Dict, List, Optional

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from ...utils import kubernetes


class Server(BaseModel):
    host: str
    port: int


class Workspace(BaseModel):
    enabled: bool
    servers: List[Server]


class Dagit(BaseModel):
    image: kubernetes.Image
    service: kubernetes.Service
    workspace: Workspace
    replicaCount: Optional[int] = 1
    env: Optional[Dict[str, str]] = {}
    envConfigMaps: Optional[List[kubernetes.ConfigMapEnvSource]] = []
    envSecrets: Optional[List[kubernetes.SecretEnvSource]] = []
    nodeSelector: Optional[kubernetes.NodeSelector] = {}
    affinity: Optional[kubernetes.Affinity] = {}
    tolerations: Optional[kubernetes.Tolerations] = []
    podSecurityContext: Optional[kubernetes.PodSecurityContext] = {}
    securityContext: Optional[kubernetes.SecurityContext] = {}
    resources: Optional[kubernetes.Resources] = {}
    livenessProbe: kubernetes.LivenessProbe
    startupProbe: kubernetes.StartupProbe
    annotations: Optional[kubernetes.Annotations] = {}
