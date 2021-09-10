from typing import List, Union

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from ...utils import kubernetes


class IngressTLSConfiguration(BaseModel):
    enabled: bool
    secretName: str


# Enforce as HTTPIngressPath: see https://github.com/dagster-io/dagster/issues/3184
class IngressPath(BaseModel):
    path: str
    serviceName: str
    servicePort: Union[str, int]


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
    readOnlyDagit: DagitIngressConfiguration
    flower: FlowerIngressConfiguration
