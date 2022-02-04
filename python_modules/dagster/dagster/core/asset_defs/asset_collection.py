from typing import Dict, List, NamedTuple

from ..definitions.resource_definition import ResourceDefinition
from .asset import AssetsDefinition


class AssetCollection(NamedTuple):
    assets: List[AssetsDefinition]
    resource_defs: Dict[str, ResourceDefinition]

    @staticmethod
    def from_list(assets, resource_defs=None) -> "AssetCollection":
        return AssetCollection(assets=assets, resource_defs=resource_defs)

    @staticmethod
    def from_package(path, resource_defs=None) -> "AssetCollection":
        pass

    def execute_in_process(self, instance):
        pass
