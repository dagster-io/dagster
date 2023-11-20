from typing import NamedTuple, Optional, Sequence, Union

import dagster._check as check
from dagster._annotations import PublicAttr, experimental
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.data_version import DataVersion, DataVersionsByPartition

from .events import (
    AssetKey,
    CoercibleToAssetKey,
)
from .metadata import MetadataByPartition, MetadataMapping, RawMetadataMapping, normalize_metadata


@experimental
class MaterializeResult(
    NamedTuple(
        "_MaterializeResult",
        [
            ("asset_key", PublicAttr[Optional[AssetKey]]),
            ("metadata", PublicAttr[Optional[Union[MetadataMapping, MetadataByPartition]]]),
            ("check_results", PublicAttr[Sequence[AssetCheckResult]]),
            ("data_version", PublicAttr[Optional[Union[DataVersion, DataVersionsByPartition]]]),
        ],
    )
):
    """An object representing a successful materialization of an asset. These can be returned from
    @asset and @multi_asset decorated functions to pass metadata or specify specific assets were
    materialized.

    Attributes:
        asset_key (Optional[AssetKey]): Optional in @asset, required in @multi_asset to discern which asset this refers to.
        metadata (Optional[RawMetadataMapping]): Metadata to record with the corresponding AssetMaterialization event.
    """

    def __new__(
        cls,
        *,  # enforce kwargs
        asset_key: Optional[CoercibleToAssetKey] = None,
        metadata: Optional[Union[RawMetadataMapping, MetadataByPartition]] = None,
        check_results: Optional[Sequence[AssetCheckResult]] = None,
        data_version: Optional[DataVersion] = None,
    ):
        asset_key = AssetKey.from_coercible(asset_key) if asset_key else None
        if isinstance(metadata, MetadataByPartition):
            normalized_metadata = metadata
        else:
            normalized_metadata = normalize_metadata(
                check.opt_mapping_param(metadata, "metadata", key_type=str),
            )

        return super().__new__(
            cls,
            asset_key=asset_key,
            metadata=normalized_metadata,
            check_results=check.opt_sequence_param(
                check_results, "check_results", of_type=AssetCheckResult
            ),
            data_version=check.opt_inst_param(
                data_version, "data_version", (DataVersion, DataVersionsByPartition)
            ),
        )

    def check_result_named(self, check_name: str) -> AssetCheckResult:
        for check_result in self.check_results:
            if check_result.check_name == check_name:
                return check_result

        check.failed(f"Could not find check result named {check_name}")
