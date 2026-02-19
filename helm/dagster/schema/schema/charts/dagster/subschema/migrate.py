from pydantic import BaseModel

from schema.charts.utils import kubernetes


class Migrate(BaseModel):
    enabled: bool
    extraContainers: list[kubernetes.Container] | None
    initContainers: list[kubernetes.Container] | None
