from collections.abc import Mapping, Sequence
from datetime import datetime  # noqa
from os import PathLike  # noqa
from typing import Any, Generic, TypeVar

from dagster_shared.check.decorator import checked
from dagster_shared.record import IHaveNew, LegacyNamedTupleMixin, record_custom

import dagster._check as check
from dagster._annotations import PublicAttr, public
from dagster._core.definitions.asset_checks.asset_check_result import AssetCheckResult
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.metadata import (  # noqa
    MetadataValue,
    RawMetadataMapping,
    TableColumnLineage,
    TableSchema,
)
from dagster._core.definitions.utils import NoValueSentinel


@checked
def coerce_asset_result_args(
    asset_key: CoercibleToAssetKey | None,
    metadata: RawMetadataMapping | None,
    check_results: Sequence[AssetCheckResult] | None,
    data_version: DataVersion | None,
    tags: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    from dagster._core.definitions.events import validate_asset_event_tags

    return dict(
        asset_key=AssetKey.from_coercible(asset_key) if asset_key else None,
        metadata=metadata,
        check_results=check_results or [],
        data_version=data_version,
        tags=validate_asset_event_tags(tags),
    )


class AssetResult:
    """Base class for MaterializeResult and ObserveResult."""

    asset_key: PublicAttr[AssetKey | None]
    metadata: PublicAttr[RawMetadataMapping | None]
    check_results: PublicAttr[Sequence[AssetCheckResult]]
    data_version: PublicAttr[DataVersion | None]
    tags: PublicAttr[Mapping[str, str] | None]

    def check_result_named(self, check_name: str) -> AssetCheckResult:
        for check_result in self.check_results:
            if check_result.check_name == check_name:
                return check_result

        check.failed(f"Could not find check result named {check_name}")


T = TypeVar("T")


@record_custom(checked=False)
@public
class MaterializeResult(AssetResult, Generic[T], IHaveNew, LegacyNamedTupleMixin):
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

    asset_key: PublicAttr[AssetKey | None]
    metadata: PublicAttr[RawMetadataMapping | None]
    check_results: PublicAttr[Sequence[AssetCheckResult]]
    data_version: PublicAttr[DataVersion | None]
    tags: PublicAttr[Mapping[str, str] | None]
    value: PublicAttr[T]

    def __new__(
        cls,
        asset_key: CoercibleToAssetKey | None = None,
        metadata: RawMetadataMapping | None = None,
        check_results: Sequence[AssetCheckResult] | None = None,
        data_version: DataVersion | None = None,
        tags: Mapping[str, str] | None = None,
        value: T = NoValueSentinel,
    ):
        return super().__new__(
            cls,
            **coerce_asset_result_args(
                asset_key=asset_key,
                metadata=metadata,
                check_results=check_results,
                data_version=data_version,
                tags=tags,
            ),
            value=value,
        )


@public
@record_custom(checked=False)
class ObserveResult(AssetResult, IHaveNew, LegacyNamedTupleMixin):
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

    asset_key: PublicAttr[AssetKey | None]
    metadata: PublicAttr[RawMetadataMapping | None]
    check_results: PublicAttr[Sequence[AssetCheckResult]]
    data_version: PublicAttr[DataVersion | None]
    tags: PublicAttr[Mapping[str, str] | None]

    def __new__(
        cls,
        asset_key: CoercibleToAssetKey | None = None,
        metadata: RawMetadataMapping | None = None,
        check_results: Sequence[AssetCheckResult] | None = None,
        data_version: DataVersion | None = None,
        tags: Mapping[str, str] | None = None,
    ):
        return super().__new__(
            cls,
            **coerce_asset_result_args(
                asset_key=asset_key,
                metadata=metadata,
                check_results=check_results,
                data_version=data_version,
                tags=tags,
            ),
        )
