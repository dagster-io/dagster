from typing import Optional

from pydantic import BaseModel

from ...utils import kubernetes


class Flower(BaseModel):
    enabled: bool
    service: kubernetes.Service
    nodeSelector: kubernetes.NodeSelector
    affinity: kubernetes.Affinity
    tolerations: kubernetes.Tolerations
    podSecurityContext: kubernetes.PodSecurityContext
    securityContext: kubernetes.SecurityContext
    resources: kubernetes.Resources
    livenessProbe: kubernetes.LivenessProbe
    startupProbe: kubernetes.StartupProbe
    annotations: Optional[kubernetes.Annotations]
    schedulerName: Optional[str]
