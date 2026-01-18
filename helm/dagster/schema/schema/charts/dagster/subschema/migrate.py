from typing import Optional

from pydantic import BaseModel

from schema.charts.utils import kubernetes


class Migrate(BaseModel):
    enabled: bool
    extraContainers: Optional[list[kubernetes.Container]]
    initContainers: Optional[list[kubernetes.Container]]
