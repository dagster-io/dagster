from enum import Enum
from typing import TYPE_CHECKING, Any, Iterable, Mapping, NamedTuple, Optional

import dagster._check as check
from dagster._annotations import PublicAttr, experimental
from dagster._core.errors import DagsterInvariantViolationError

from .auto_materialize_policy import AutoMaterializePolicy
from .events import (
    AssetKey,
    CoercibleToAssetKey,
)
from .freshness_policy import FreshnessPolicy
from .metadata import MetadataUserInput

if TYPE_CHECKING:
    from dagster._core.definitions.asset_dep import AssetDep, CoercibleToAssetDep

# SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE lives on the metadata of an asset
# (which currently ends up on the Output associated with the asset key)
# whih encodes the execution type the of asset. "Unexecutable" assets are assets
# that cannot be materialized in Dagster, but can have events in the event
# log keyed off of them, making Dagster usable as a observability and lineage tool
# for externally materialized assets.
SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE = "dagster/asset_execution_type"


class AssetExecutionType(Enum):
    UNEXECUTABLE = "UNEXECUTABLE"
    MATERIALIZATION = "MATERIALIZATION"

    @staticmethod
    def is_executable(varietal_str: Optional[str]) -> bool:
        return AssetExecutionType.str_to_enum(varietal_str) in {AssetExecutionType.MATERIALIZATION}

    @staticmethod
    def str_to_enum(varietal_str: Optional[str]) -> "AssetExecutionType":
        return (
            AssetExecutionType.MATERIALIZATION
            if varietal_str is None
            else AssetExecutionType(varietal_str)
        )


@experimental
class AssetSpec(
    NamedTuple(
        "_AssetSpec",
        [
            ("key", PublicAttr[AssetKey]),
            ("deps", PublicAttr[Iterable["AssetDep"]]),
            ("description", PublicAttr[Optional[str]]),
            ("metadata", PublicAttr[Optional[Mapping[str, Any]]]),
            ("group_name", PublicAttr[Optional[str]]),
            ("skippable", PublicAttr[bool]),
            ("code_version", PublicAttr[Optional[str]]),
            ("freshness_policy", PublicAttr[Optional[FreshnessPolicy]]),
            ("auto_materialize_policy", PublicAttr[Optional[AutoMaterializePolicy]]),
        ],
    )
):
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

    def __new__(
        cls,
        key: CoercibleToAssetKey,
        *,
        deps: Optional[Iterable["CoercibleToAssetDep"]] = None,
        description: Optional[str] = None,
        metadata: Optional[MetadataUserInput] = None,
        skippable: bool = False,
        group_name: Optional[str] = None,
        code_version: Optional[str] = None,
        freshness_policy: Optional[FreshnessPolicy] = None,
        auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
    ):
        from dagster._core.definitions.asset_dep import AssetDep

        dep_set = {}
        if deps:
            for dep in deps:
                asset_dep = AssetDep.from_coercible(dep)

                # we cannot do deduplication via a set because MultiPartitionMappings have an internal
                # dictionary that cannot be hashed. Instead deduplicate by making a dictionary and checking
                # for existing keys.
                if asset_dep.asset_key in dep_set.keys():
                    raise DagsterInvariantViolationError(
                        f"Cannot set a dependency on asset {asset_dep.asset_key} more than once for"
                        f" AssetSpec {key}"
                    )
                dep_set[asset_dep.asset_key] = asset_dep

        return super().__new__(
            cls,
            key=AssetKey.from_coercible(key),
            deps=list(dep_set.values()),
            description=check.opt_str_param(description, "description"),
            metadata=check.opt_mapping_param(metadata, "metadata", key_type=str),
            skippable=check.bool_param(skippable, "skippable"),
            group_name=check.opt_str_param(group_name, "group_name"),
            code_version=check.opt_str_param(code_version, "code_version"),
            freshness_policy=check.opt_inst_param(
                freshness_policy,
                "freshness_policy",
                FreshnessPolicy,
            ),
            auto_materialize_policy=check.opt_inst_param(
                auto_materialize_policy,
                "auto_materialize_policy",
                AutoMaterializePolicy,
            ),
        )
