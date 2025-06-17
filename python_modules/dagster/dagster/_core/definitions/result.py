from collections.abc import Mapping, Sequence
from datetime import datetime  # noqa
from os import PathLike  # noqa
from typing import Any, Optional

from dagster_shared.check.decorator import checked

import dagster._check as check
from dagster._annotations import PublicAttr
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.metadata import (  # noqa
    MetadataValue,
    RawMetadataMapping,
    TableSchema,
)
from dagster._core.definitions.utils import NoValueSentinel


class AssetResult:
    """Base class for MaterializeResult and ObserveResult."""

    asset_key: PublicAttr[Optional[AssetKey]]
    metadata: PublicAttr[Optional[RawMetadataMapping]]
    check_results: PublicAttr[Sequence[AssetCheckResult]]
    data_version: PublicAttr[Optional[DataVersion]]
    tags: PublicAttr[Optional[Mapping[str, str]]]

    @checked
    def __init__(
        self,
        *,  # enforce kwargs
        asset_key: Optional[CoercibleToAssetKey] = None,
        metadata: Optional[RawMetadataMapping] = None,
        check_results: Optional[Sequence[AssetCheckResult]] = None,
        data_version: Optional[DataVersion] = None,
        tags: Optional[Mapping[str, str]] = None,
    ):
        from dagster._core.definitions.events import validate_asset_event_tags

        self.asset_key = AssetKey.from_coercible(asset_key) if asset_key else None
        self.metadata = metadata
        self.check_results = check_results or []
        self.data_version = data_version
        self.tags = validate_asset_event_tags(tags)

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
        value (Optional[Any]): The output value of the asset that was materialized.
    """

    value: PublicAttr[Any]

    @checked
    def __init__(
        self,
        *,  # enforce kwargs
        asset_key: Optional[CoercibleToAssetKey] = None,
        metadata: Optional[RawMetadataMapping] = None,
        check_results: Optional[Sequence[AssetCheckResult]] = None,
        data_version: Optional[DataVersion] = None,
        tags: Optional[Mapping[str, str]] = None,
        value: Optional[Any] = NoValueSentinel,
    ):
        self._value_unset = value is NoValueSentinel
        self.value = None if self._value_unset else value
        super().__init__(
            asset_key=asset_key,
            metadata=metadata,
            check_results=check_results,
            data_version=data_version,
            tags=tags,
        )

    @property
    def value_unset(self) -> bool:
        return self._value_unset


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
