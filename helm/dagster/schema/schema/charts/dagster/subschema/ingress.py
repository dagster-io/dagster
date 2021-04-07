from typing import List, Union

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from ...utils import kubernetes


# Enforce as HTTPIngressPath: see https://github.com/dagster-io/dagster/issues/3184
class IngressPath(BaseModel):
    path: str
    serviceName: str
    servicePort: Union[str, int]

class IngressTLSConfiguration(BaseModel):
    secretName: str


class DagitIngressConfiguration(BaseModel):
    host: str
    path: str
    tls: IngressTLSConfiguration
    precedingPaths: List[IngressPath]
    succeedingPaths: List[IngressPath]


class FlowerIngressConfiguration(BaseModel):
    host: str
    path: str
    tls: IngressTLSConfiguration
    precedingPaths: List[IngressPath]
    succeedingPaths: List[IngressPath]


class Ingress(BaseModel):
    enabled: bool
    annotations: kubernetes.Annotations
    dagit: DagitIngressConfiguration
    flower: FlowerIngressConfiguration
