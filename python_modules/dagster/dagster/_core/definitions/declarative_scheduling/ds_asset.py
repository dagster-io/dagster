from typing import TYPE_CHECKING, Iterable, Mapping, Optional, Sequence

from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    SchedulingCondition,
)
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.metadata import ArbitraryMetadataMapping

if TYPE_CHECKING:
    from dagster._core.definitions.asset_dep import CoercibleToAssetDep


# shim for building docs
def ds_asset(
    *,
    deps: Optional[Iterable["CoercibleToAssetDep"]] = None,
    description: Optional[str] = None,
    metadata: Optional[ArbitraryMetadataMapping] = None,
    group_name: Optional[str] = None,
    code_version: Optional[str] = None,
    key: Optional[CoercibleToAssetKey] = None,
    scheduling: Optional[SchedulingCondition] = None,
    check_specs: Optional[Sequence[AssetCheckSpec]] = None,
    owners: Optional[Sequence[str]] = None,
    tags: Optional[Mapping[str, str]] = None,
):
    return asset(
        key=key,
        deps=deps,
        description=description,
        metadata=metadata,
        group_name=group_name,
        code_version=code_version,
        auto_materialize_policy=scheduling.as_auto_materialize_policy() if scheduling else None,
        check_specs=check_specs,
        owners=owners,
        tags=tags,
    )
