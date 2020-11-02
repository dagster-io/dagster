from pydantic import BaseModel  # pylint: disable=E0611

from . import kubernetes


class Service(BaseModel):
    annotations: kubernetes.Annotations
    port: int


class Flower(BaseModel):
    enabled: bool
    service: Service
    nodeSelector: kubernetes.NodeSelector
    affinity: kubernetes.Affinity
    tolerations: kubernetes.Tolerations
    podSecurityContext: kubernetes.PodSecurityContext
    securityContext: kubernetes.SecurityContext
    resources: kubernetes.Resources
    livenessProbe: kubernetes.LivenessProbe
    startupProbe: kubernetes.StartupProbe
