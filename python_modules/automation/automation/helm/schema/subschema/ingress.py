from typing import List, Union

from pydantic import BaseModel  # pylint: disable=E0611

from . import kubernetes


# Enforce as HTTPIngressPath: see https://github.com/dagster-io/dagster/issues/3184
class IngressPath(BaseModel):
    path: str
    serviceName: str
    servicePort: Union[str, int]


class DagitIngressConfiguration(BaseModel):
    host: str
    precedingPaths: List[IngressPath]
    succeedingPaths: List[IngressPath]


class FlowerIngressConfiguration(BaseModel):
    host: str
    path: str
    precedingPaths: List[IngressPath]
    succeedingPaths: List[IngressPath]


class Ingress(BaseModel):
    enabled: bool
    annotations: kubernetes.Annotations
    dagit: DagitIngressConfiguration
    flower: FlowerIngressConfiguration
