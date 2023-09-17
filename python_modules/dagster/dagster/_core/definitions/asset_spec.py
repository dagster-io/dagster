from typing import TYPE_CHECKING, Any, Iterable, Mapping, Optional, Union

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.errors import DagsterInvariantViolationError

from .auto_materialize_policy import AutoMaterializePolicy
from .events import (
    AssetKey,
    CoercibleToAssetKey,
)
from .freshness_policy import FreshnessPolicy
from .metadata import MetadataUserInput

if TYPE_CHECKING:
    from dagster._core.definitions.asset_dep import AssetDep

# dagit is silently not loading a definition with a leading dagster/
# just doing vanilla key for now
SYSTEM_METADATA_KEY_EXECUTABLE = "dagster__executable"
# SYSTEM_METADATA_KEY_EXECUTABLE = "dagster/executable"


@experimental
class ObservableAssetSpec:
    def __init__(
        self,
        key: CoercibleToAssetKey,
        *,
        deps: Optional[
            Iterable[
                Union[CoercibleToAssetKey, "AssetSpec", AssetsDefinition, SourceAsset, "AssetDep"]
            ]
        ] = None,
        description: Optional[str] = None,
        metadata: Optional[MetadataUserInput] = None,
        group_name: Optional[str] = None,
    ):
        from dagster._core.definitions.asset_dep import AssetDep

        dep_set = {}
        if deps:
            for dep in deps:
                if not isinstance(dep, AssetDep):
                    asset_dep = AssetDep(dep)
                else:
                    asset_dep = dep

                # we cannot do deduplication via a set because MultiPartitionMappings have an internal
                # dictionary that cannot be hashed. Instead deduplicate by making a dictionary and checking
                # for existing keys.
                if asset_dep.asset_key in dep_set.keys():
                    raise DagsterInvariantViolationError(
                        f"Cannot set a dependency on asset {asset_dep.asset_key} more than once for"
                        f" AssetSpec {key}"
                    )
                dep_set[asset_dep.asset_key] = asset_dep

        self._key = AssetKey.from_coercible(key)
        self._deps = list(dep_set.values())
        self._description = check.opt_str_param(description, "description")
        self._metadata = check.opt_mapping_param(metadata, "metadata", key_type=str)
        self._group_name = check.opt_str_param(group_name, "group_name")

    @property
    def key(self) -> AssetKey:
        return self._key

    @property
    def deps(self) -> Iterable["AssetDep"]:
        return self._deps

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def metadata(self) -> Optional[Mapping[str, Any]]:
        return self._metadata

    @property
    def group_name(self) -> Optional[str]:
        return self._group_name


@experimental
class AssetSpec(ObservableAssetSpec):
    """Specifies the core attributes of an asset. This object is attached to the decorated
    function that defines how it materialized.

    Attributes:
        key (AssetKey): The unique identifier for this asset.
        deps (Optional[AbstractSet[AssetKey]]): The asset keys for the upstream assets that
            materializing this asset depends on.
        description (Optional[str]): Human-readable description of this asset.
        metadata (Optional[Dict[str, Any]]): A dict of static metadata for this asset.
            For example, users can provide information about the database table this
            asset corresponds to.
        skippable (bool): Whether this asset can be omitted during materialization, causing downstream
            dependencies to skip.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. If
            not provided, the name "default" is used.
        code_version (Optional[str]): The version of the code for this specific asset,
            overriding the code version of the materialization function
        freshness_policy (Optional[FreshnessPolicy]): A policy which indicates how up to date this
            asset is intended to be.
        auto_materialize_policy (Optional[AutoMaterializePolicy]): AutoMaterializePolicy to apply to
            the specified asset.
        backfill_policy (Optional[BackfillPolicy]): BackfillPolicy to apply to the specified asset.
    """

    def __init__(
        self,
        key: CoercibleToAssetKey,
        *,
        deps: Optional[
            Iterable[
                Union[CoercibleToAssetKey, "AssetSpec", AssetsDefinition, SourceAsset, "AssetDep"]
            ]
        ] = None,
        description: Optional[str] = None,
        metadata: Optional[MetadataUserInput] = None,
        group_name: Optional[str] = None,
        code_version: Optional[str] = None,
        skippable: bool = False,
        freshness_policy: Optional[FreshnessPolicy] = None,
        auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
    ):
        self._skippable = check.bool_param(skippable, "skippable")
        self._code_version = check.opt_str_param(code_version, "code_version")
        self._freshness_policy = check.opt_inst_param(
            freshness_policy,
            "freshness_policy",
            FreshnessPolicy,
        )
        self._auto_materialize_policy = check.opt_inst_param(
            auto_materialize_policy,
            "auto_materialize_policy",
            AutoMaterializePolicy,
        )
        super().__init__(
            key=key, deps=deps, description=description, metadata=metadata, group_name=group_name
        )

    @property
    def code_version(self) -> Optional[str]:
        return self._code_version

    @property
    def skippable(self) -> bool:
        return self._skippable

    @property
    def freshness_policy(self) -> Optional[FreshnessPolicy]:
        return self._freshness_policy

    @property
    def auto_materialize_policy(self) -> Optional[AutoMaterializePolicy]:
        return self._auto_materialize_policy
