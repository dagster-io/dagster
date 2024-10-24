from pydantic import BaseModel
from typing import List, Optional

from ...utils import kubernetes

class Migrate(BaseModel):
    enabled: bool
    extraContainers: Optional[List[kubernetes.Container]]
    initContainers: Optional[List[kubernetes.Container]]
