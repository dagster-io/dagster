import datetime
from typing import Optional
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKey
from dagster._utils import CachingInstanceQueryer

class CachingDataTimeResolver:

    _instance_queryer: CachingInstanceQueryer
    _asset_graph: Optional["AssetGraph"]

    def __init__(self, instance_queryer: CachingInstanceQueryer, asset_graph: AssetGraph):
        self._instance_queryer = instance_queryer
        self._asset_graph = asset_graph

    def get_current_data_time(self, asset_key: AssetKey) -> Optional[datetime.datetime]:
        pass

    def get_effective_data_time(self, asset_key: AssetKey) -> Optional[datetime.datetime]:
        pass
