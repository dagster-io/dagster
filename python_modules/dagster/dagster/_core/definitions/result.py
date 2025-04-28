from collections.abc import Mapping, Sequence
from typing import NamedTuple, Optional

import dagster._check as check
from dagster._annotations import PublicAttr
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.metadata import RawMetadataMapping


class AssetResult(
    NamedTuple(
        "_AssetResult",
        [
            ("asset_key", PublicAttr[Optional[AssetKey]]),
            ("metadata", PublicAttr[Optional[RawMetadataMapping]]),
            ("check_results", PublicAttr[Sequence[AssetCheckResult]]),
            ("data_version", PublicAttr[Optional[DataVersion]]),
            ("tags", PublicAttr[Optional[Mapping[str, str]]]),
        ],
    )
):
    """Base class for MaterializeResult and ObserveResult."""

    def __new__(
        cls,
        *,  # enforce kwargs
        asset_key: Optional[CoercibleToAssetKey] = None,
        metadata: Optional[RawMetadataMapping] = None,
        check_results: Optional[Sequence[AssetCheckResult]] = None,
        data_version: Optional[DataVersion] = None,
        tags: Optional[Mapping[str, str]] = None,
    ):
        from dagster._core.definitions.events import validate_asset_event_tags

        asset_key = AssetKey.from_coercible(asset_key) if asset_key else None

        return super().__new__(
            cls,
            asset_key=asset_key,
            metadata=check.opt_nullable_mapping_param(
                metadata,
                "metadata",
                key_type=str,
            ),
            check_results=check.opt_sequence_param(
                check_results, "check_results", of_type=AssetCheckResult
            ),
            data_version=check.opt_inst_param(data_version, "data_version", DataVersion),
            tags=validate_asset_event_tags(tags),
        )

    def check_result_named(self, check_name: str) -> AssetCheckResult:
        for check_result in self.check_results:
            if check_result.check_name == check_name:
                return check_result

        check.failed(f"Could not find check result named {check_name}")


class MaterializeResult(AssetResult):
    """An object representing a successful materialization of an asset. These can be returned from
    @asset and @multi_asset decorated functions to pass metadata or specify specific assets were
    materialized.

    Args:
        asset_key (Optional[AssetKey]): Optional in @asset, required in @multi_asset to discern which asset this refers to.
        metadata (Optional[RawMetadataMapping]): Metadata to record with the corresponding AssetMaterialization event.
        check_results (Optional[Sequence[AssetCheckResult]]): Check results to record with the
            corresponding AssetMaterialization event.
        data_version (Optional[DataVersion]): The data version of the asset that was observed.
        tags (Optional[Mapping[str, str]]): Tags to record with the corresponding
            AssetMaterialization event.
    """


class ObserveResult(AssetResult):
    """An object representing a successful observation of an asset. These can be returned from an
    @observable_source_asset decorated function to pass metadata.

    Args:
        asset_key (Optional[AssetKey]): The asset key. Optional to include.
        metadata (Optional[RawMetadataMapping]): Metadata to record with the corresponding
            AssetObservation event.
        check_results (Optional[Sequence[AssetCheckResult]]): Check results to record with the
            corresponding AssetObservation event.
        data_version (Optional[DataVersion]): The data version of the asset that was observed.
        tags (Optional[Mapping[str, str]]): Tags to record with the corresponding AssetObservation
            event.
    """
