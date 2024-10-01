from pydantic import BaseModel

from schema.charts.utils import kubernetes


class ServiceAccount(BaseModel):
    create: bool
    name: str
    annotations: kubernetes.Annotations
