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
    checkDbReadyInitContainer: bool | None = None
    resources: kubernetes.Resources
    livenessProbe: kubernetes.LivenessProbe
    startupProbe: kubernetes.StartupProbe
    annotations: kubernetes.Annotations | None = None
    schedulerName: str | None = None
