from typing import Dict, List

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from ...utils import kubernetes


class Dagit(BaseModel):
    replicaCount: int
    image: kubernetes.Image
    service: kubernetes.Service
    env: Dict[str, str]
    envConfigMaps: List[kubernetes.ConfigMapEnvSource]
    envSecrets: List[kubernetes.SecretEnvSource]
    nodeSelector: kubernetes.NodeSelector
    affinity: kubernetes.Affinity
    tolerations: kubernetes.Tolerations
    podSecurityContext: kubernetes.PodSecurityContext
    securityContext: kubernetes.SecurityContext
    resources: kubernetes.Resources
    livenessProbe: kubernetes.LivenessProbe
    startupProbe: kubernetes.StartupProbe
    annotations: kubernetes.Annotations
