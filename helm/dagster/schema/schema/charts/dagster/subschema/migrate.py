from typing import List, Optional

from pydantic import BaseModel

from schema.charts.utils import kubernetes


class Migrate(BaseModel):
    enabled: bool
    extraContainers: Optional[List[kubernetes.Container]]
    initContainers: Optional[List[kubernetes.Container]]
