from pydantic import BaseModel

from ...utils import kubernetes


class ServiceAccount(BaseModel):
    create: bool
    name: str
    annotations: kubernetes.Annotations
