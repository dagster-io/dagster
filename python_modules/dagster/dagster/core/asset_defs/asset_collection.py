from typing import Dict, List, NamedTuple, Optional

from ..definitions.executor_definition import ExecutorDefinition
from ..definitions.resource_definition import ResourceDefinition
from .asset import AssetsDefinition


class AssetCollection(NamedTuple):
    assets: List[AssetsDefinition]
    resource_defs: Dict[str, ResourceDefinition]
    executor_def: Optional[ExecutorDefinition]
