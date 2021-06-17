from pydantic import BaseModel  # pylint: disable=no-name-in-module

from ...utils import kubernetes


class ServiceAccount(BaseModel):
    create: bool
    name: str
    annotations: kubernetes.Annotations
