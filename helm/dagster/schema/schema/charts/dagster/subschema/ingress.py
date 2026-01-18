from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel

from schema.charts.utils import kubernetes


class IngressPathType(str, Enum):
    EXACT = "Exact"
    PREFIX = "Prefix"
    IMPLEMENTATION_SPECIFIC = "ImplementationSpecific"


class IngressTLSConfiguration(BaseModel):
    enabled: bool
    secretName: str


# Enforce as HTTPIngressPath: see https://github.com/dagster-io/dagster/issues/3184
class IngressPath(BaseModel):
    path: str
    pathType: IngressPathType
    serviceName: str
    servicePort: Union[str, int]


class WebserverIngressConfiguration(BaseModel):
    host: str
    path: str
    pathType: IngressPathType
    tls: IngressTLSConfiguration
    precedingPaths: list[IngressPath]
    succeedingPaths: list[IngressPath]


class FlowerIngressConfiguration(BaseModel):
    host: str
    path: str
    pathType: IngressPathType
    tls: IngressTLSConfiguration
    precedingPaths: list[IngressPath]
    succeedingPaths: list[IngressPath]


# We have `extra="allow"` here to support passing `dagit` as an alias for `dagsterWebserver` when
# constructing without validation. This can be removed in 2.0 since we will no longer support the
# dagit alias. It is possible there is a better way to do this using Pydantic field aliases, but the
# current solution does work.
class Ingress(BaseModel, extra="allow"):
    enabled: bool
    apiVersion: Optional[str] = None
    labels: kubernetes.Labels
    annotations: kubernetes.Annotations
    flower: FlowerIngressConfiguration
    dagsterWebserver: WebserverIngressConfiguration
    readOnlyDagsterWebserver: WebserverIngressConfiguration
