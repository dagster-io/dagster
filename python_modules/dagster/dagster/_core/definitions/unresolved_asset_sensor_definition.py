from typing import TYPE_CHECKING, Optional, Sequence

from .asset_selection import AssetSelection
from .sensor_definition import DefaultSensorStatus

if TYPE_CHECKING:
    from dagster._core.definitions import AssetsDefinition, SourceAsset


class UnresolvedAssetSensorDefinition:
    def __init__(
        self,
        asset_selection: AssetSelection,
        name: str,
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    ):
        self._selection = asset_selection
        self._name = name
        self._minimum_interval_seconds = minimum_interval_seconds
        self._description = description
        self._default_status = default_status

    def resolve(
        self,
        assets: Sequence["AssetsDefinition"],
        source_assets: Sequence["SourceAsset"],
    ):
        pass

    @property
    def name(self):
        return self._name
