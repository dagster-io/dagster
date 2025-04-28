from typing import Optional

from pydantic import BaseModel

from schema.charts.utils import kubernetes


class Flower(BaseModel):
    enabled: bool
    service: kubernetes.Service
    nodeSelector: kubernetes.NodeSelector
    affinity: kubernetes.Affinity
    tolerations: kubernetes.Tolerations
    podSecurityContext: kubernetes.PodSecurityContext
    securityContext: kubernetes.SecurityContext
    checkDbReadyInitContainer: Optional[bool] = None
    resources: kubernetes.Resources
    livenessProbe: kubernetes.LivenessProbe
    startupProbe: kubernetes.StartupProbe
    annotations: Optional[kubernetes.Annotations] = None
    schedulerName: Optional[str] = None
