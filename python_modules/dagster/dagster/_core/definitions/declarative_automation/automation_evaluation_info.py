from typing import NamedTuple, Optional

from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, AssetSlice
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AssetSubsetWithMetadata,
)
from dagster._core.definitions.metadata import MetadataMapping


class AssetSliceWithMetadata(NamedTuple):
    asset_slice: AssetSlice
    metadata: MetadataMapping

    @staticmethod
    def from_asset_subset_with_metadata(
        *, asset_graph_view: AssetGraphView, asset_subset_with_metadata: AssetSubsetWithMetadata
    ) -> Optional["AssetSliceWithMetadata"]:
        metadata = asset_subset_with_metadata.metadata
        if metadata is None:
            return None
        asset_slice = asset_graph_view.get_asset_slice_from_subset(
            asset_subset_with_metadata.subset
        )
        if asset_slice is None:
            return None
        return AssetSliceWithMetadata(asset_slice=asset_slice, metadata=metadata)
