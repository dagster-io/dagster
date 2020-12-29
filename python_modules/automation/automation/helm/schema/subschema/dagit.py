from typing import Optional

from pydantic import BaseModel  # pylint: disable=E0611

from . import kubernetes


class Dagit(BaseModel):
    replicaCount: int
    image: kubernetes.Image
    service: kubernetes.Service
    nodeSelector: Optional[kubernetes.NodeSelector]
    affinity: Optional[kubernetes.Affinity]
    tolerations: Optional[kubernetes.Tolerations]
    podSecurityContext: Optional[kubernetes.PodSecurityContext]
    securityContext: Optional[kubernetes.SecurityContext]
    resources: Optional[kubernetes.Resources]
    livenessProbe: Optional[kubernetes.LivenessProbe]
    startupProbe: Optional[kubernetes.StartupProbe]
    annotations: Optional[kubernetes.Annotations]
