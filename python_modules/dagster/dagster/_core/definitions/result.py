from typing import NamedTuple, Optional

from dagster._annotations import PublicAttr, experimental

from .events import (
    AssetKey,
    CoercibleToAssetKey,
)
from .metadata import MetadataUserInput


@experimental
class MaterializeResult(
    NamedTuple(
        "_MaterializeResult",
        [
            ("asset_key", PublicAttr[Optional[AssetKey]]),
            ("metadata", PublicAttr[Optional[MetadataUserInput]]),
        ],
    )
):
    """An object representing a successful materialization of an asset. These can be returned from
    @asset and @multi_asset decorated functions to pass metadata or specify specific assets were
    materialized.

    Attributes:
        asset_key (Optional[AssetKey]): Optional in @asset, required in @multi_asset to discern which asset this refers to.
        metadata (Optional[MetadataUserInput]): Metadata to record with the corresponding AssetMaterialization event.
    """

    def __new__(
        cls,
        *,  # enforce kwargs
        asset_key: Optional[CoercibleToAssetKey] = None,
        metadata: Optional[MetadataUserInput] = None,
    ):
        asset_key = AssetKey.from_coercible(asset_key) if asset_key else None

        return super().__new__(
            cls,
            asset_key=asset_key,
            metadata=metadata,  # check?
        )
