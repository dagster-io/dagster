from typing import TYPE_CHECKING, Any, Iterable, Mapping, Optional, Union

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.metadata import MetadataUserInput
from dagster._core.errors import DagsterInvariantViolationError

from .events import (
    AssetKey,
)

if TYPE_CHECKING:
    from dagster._core.definitions.asset_dep import AssetDep
    from dagster._core.definitions.source_asset import SourceAsset

# TODO
# define the body of an observable asset as a function. It can execute either in the context of a sensor or in the context of a vanilla assets definition


class _ReadonlyAssetSpec:
    """Specifies the core attributes of an asset in the graph.

    Attributes:
        key (AssetKey): The unique identifier for this asset.
        deps (Optional[AbstractSet[AssetKey]]): The asset keys for the upstream assets that
            materializing this asset depends on.
        description (Optional[str]): Human-readable description of this asset.
        metadata (Optional[Dict[str, Any]]): A dict of static metadata for this asset.
            For example, users can provide information about the database table this
            asset corresponds to.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. If
            not provided, the name "default" is used.
    """

    # TODO make these private
    key: AssetKey
    deps: Iterable["AssetDep"]
    description: Optional[str]
    metadata: Optional[Mapping[str, Any]]
    group_name: Optional[str]

    def __init__(
        self,
        key: CoercibleToAssetKey,
        deps: Optional[
            Iterable[
                Union[
                    CoercibleToAssetKey,
                    "ObservableAssetSpec",
                    AssetsDefinition,
                    "SourceAsset",
                    "AssetDep",
                ]
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

        self.key = AssetKey.from_coercible(key)
        self.deps = list(dep_set.values())
        self.description = check.opt_str_param(description, "description")
        self.metadata = check.opt_mapping_param(metadata, "metadata", key_type=str)
        self.group_name = check.opt_str_param(group_name, "group_name")


@experimental
class ObservableAssetSpec(_ReadonlyAssetSpec):
    pass


@experimental
class AssetSpec(_ReadonlyAssetSpec):
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

    # TODO make these private
    skippable: bool
    code_version: Optional[str]
    freshness_policy: Optional[FreshnessPolicy]
    auto_materialize_policy: Optional[AutoMaterializePolicy]

    def __init__(
        self,
        key: CoercibleToAssetKey,
        *,
        deps: Optional[
            Iterable[
                Union[
                    CoercibleToAssetKey,
                    "ObservableAssetSpec",
                    AssetsDefinition,
                    "SourceAsset",
                    "AssetDep",
                ]
            ]
        ] = None,
        description: Optional[str] = None,
        metadata: Optional[MetadataUserInput] = None,
        skippable: bool = False,
        group_name: Optional[str] = None,
        code_version: Optional[str] = None,
        freshness_policy: Optional[FreshnessPolicy] = None,
        auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
    ):
        self.skippable = check.bool_param(skippable, "skippable")
        self.group_name = check.opt_str_param(group_name, "group_name")
        self.code_version = check.opt_str_param(code_version, "code_version")
        self.freshness_policy = check.opt_inst_param(
            freshness_policy,
            "freshness_policy",
            FreshnessPolicy,
        )
        self.auto_materialize_policy = check.opt_inst_param(
            auto_materialize_policy,
            "auto_materialize_policy",
            AutoMaterializePolicy,
        )
        super().__init__(
            key=key,
            deps=deps,
            description=description,
            metadata=metadata,
        )
