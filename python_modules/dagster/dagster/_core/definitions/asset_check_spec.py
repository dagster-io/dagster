from typing import NamedTuple

from dagster._annotations import experimental
from dagster._core.definitions.events import AssetKey


@experimental
class AssetCheckSpec(NamedTuple):
    name: str
    asset_key: AssetKey
    description: str
