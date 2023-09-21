from typing import NamedTuple, Optional, Sequence

import dagster._check as check
from dagster._annotations import PublicAttr, experimental
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.data_version import DataVersion

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
            ("check_results", PublicAttr[Optional[Sequence[AssetCheckResult]]]),
            ("data_version", PublicAttr[Optional[DataVersion]]),
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
        check_results: Optional[Sequence[AssetCheckResult]] = None,
        data_version: Optional[DataVersion] = None,
    ):
        asset_key = AssetKey.from_coercible(asset_key) if asset_key else None

        return super().__new__(
            cls,
            asset_key=asset_key,
            metadata=check.opt_nullable_mapping_param(
                metadata,
                "metadata",
                key_type=str,
            ),
            check_results=check.opt_nullable_sequence_param(
                check_results, "check_results", of_type=AssetCheckResult
            ),
            data_version=check.opt_inst_param(data_version, "data_version", DataVersion),
        )
