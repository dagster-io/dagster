from pydantic import BaseModel
from typing import List, Optional

from ...utils import kubernetes

class Migrate(BaseModel):
    enabled: bool
    customMigrateCommand: Optional[List[str]]
    extraContainers: Optional[List[kubernetes.Container]]
    initContainers: Optional[List[kubernetes.Container]]
