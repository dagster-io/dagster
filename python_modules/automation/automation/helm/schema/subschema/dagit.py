from typing import Optional

from pydantic import BaseModel  # pylint: disable=E0611

from .kubernetes import (
    Affinity,
    Image,
    LivenessProbe,
    NodeSelector,
    PodSecurityContext,
    Resources,
    SecurityContext,
    Service,
    StartupProbe,
    Tolerations,
)


class Dagit(BaseModel):
    replicaCount: int
    image: Image
    service: Service
    nodeSelector: Optional[NodeSelector]
    affinity: Optional[Affinity]
    tolerations: Optional[Tolerations]
    podSecurityContext: Optional[PodSecurityContext]
    securityContext: Optional[SecurityContext]
    resources: Optional[Resources]
    livenessProbe: Optional[LivenessProbe]
    startupProbe: Optional[StartupProbe]
