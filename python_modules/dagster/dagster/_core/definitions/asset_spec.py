from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Any, Iterable, Mapping, NamedTuple, Optional, Sequence

import dagster._check as check
from dagster._annotations import PublicAttr, experimental_param
from dagster._core.definitions.utils import validate_asset_owner
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.internal_init import IHasInternalInit

from .auto_materialize_policy import AutoMaterializePolicy
from .events import AssetKey, CoercibleToAssetKey
from .freshness_policy import FreshnessPolicy
from .partition_mapping import PartitionMapping
from .utils import validate_tags_strict

if TYPE_CHECKING:
    from dagster._core.definitions.asset_dep import AssetDep, CoercibleToAssetDep

# SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE lives on the metadata of an asset
# (which currently ends up on the Output associated with the asset key)
# whih encodes the execution type the of asset. "Unexecutable" assets are assets
# that cannot be materialized in Dagster, but can have events in the event
# log keyed off of them, making Dagster usable as a observability and lineage tool
# for externally materialized assets.
SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE = "dagster/asset_execution_type"


# SYSTEM_METADATA_KEY_IO_MANAGER_KEY lives on the metadata of an asset without a node def and
# determines the io_manager_key that can be used to load it. This is necessary because IO manager
# keys are otherwise encoded inside OutputDefinitions within NodeDefinitions.
SYSTEM_METADATA_KEY_IO_MANAGER_KEY = "dagster/io_manager_key"

# SYSTEM_METADATA_KEY_AUTO_OBSERVE_INTERVAL_MINUTES lives on the metadata of
# external assets resulting from a source asset conversion. It contains the
# `auto_observe_interval_minutes` value from the source asset and is consulted
# in the auto-materialize daemon. It should eventually be eliminated in favor
# of an implementation of `auto_observe_interval_minutes` in terms of
# `AutoMaterializeRule`.
SYSTEM_METADATA_KEY_AUTO_OBSERVE_INTERVAL_MINUTES = "dagster/auto_observe_interval_minutes"

# SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET lives on the metadata of external assets that are
# created for undefined but referenced assets during asset graph normalization. For example, in the
# below definitions, `foo` is referenced by upstream `bar` but has no corresponding definition:
#
#
#     @asset(deps=["foo"])
#     def bar(context: AssetExecutionContext):
#         ...
#
#     defs=Definitions(assets=[bar])
#
# During normalization we create a "stub" definition for `foo` and attach this metadata to it.
SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET = "dagster/auto_created_stub_asset"


@whitelist_for_serdes
class AssetExecutionType(Enum):
    OBSERVATION = "OBSERVATION"
    UNEXECUTABLE = "UNEXECUTABLE"
    MATERIALIZATION = "MATERIALIZATION"


@experimental_param(param="owners")
@experimental_param(param="tags")
class AssetSpec(
    NamedTuple(
        "_AssetSpec",
        [
            ("key", PublicAttr[AssetKey]),
            ("deps", PublicAttr[Iterable["AssetDep"]]),
            ("description", PublicAttr[Optional[str]]),
            ("metadata", PublicAttr[Mapping[str, Any]]),
            ("group_name", PublicAttr[Optional[str]]),
            ("skippable", PublicAttr[bool]),
            ("code_version", PublicAttr[Optional[str]]),
            ("freshness_policy", PublicAttr[Optional[FreshnessPolicy]]),
            ("auto_materialize_policy", PublicAttr[Optional[AutoMaterializePolicy]]),
            ("owners", PublicAttr[Sequence[str]]),
            ("tags", PublicAttr[Mapping[str, str]]),
        ],
    ),
    IHasInternalInit,
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
        freshness_policy (Optional[FreshnessPolicy]): (Deprecated) A policy which indicates how up
            to date this asset is intended to be.
        auto_materialize_policy (Optional[AutoMaterializePolicy]): AutoMaterializePolicy to apply to
            the specified asset.
        backfill_policy (Optional[BackfillPolicy]): BackfillPolicy to apply to the specified asset.
        owners (Optional[Sequence[str]]): A list of strings representing owners of the asset. Each
            string can be a user's email address, or a team name prefixed with `team:`,
            e.g. `team:finops`.
        tags (Optional[Mapping[str, str]]): Tags for filtering and organizing. These tags are not
            attached to runs of the asset.
    """

    def __new__(
        cls,
        key: CoercibleToAssetKey,
        *,
        deps: Optional[Iterable["CoercibleToAssetDep"]] = None,
        description: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        skippable: bool = False,
        group_name: Optional[str] = None,
        code_version: Optional[str] = None,
        freshness_policy: Optional[FreshnessPolicy] = None,
        auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
        owners: Optional[Sequence[str]] = None,
        tags: Optional[Mapping[str, str]] = None,
    ):
        from dagster._core.definitions.asset_dep import coerce_to_deps_and_check_duplicates

        key = AssetKey.from_coercible(key)
        asset_deps = coerce_to_deps_and_check_duplicates(deps, key)

        owners = check.opt_sequence_param(owners, "owners", of_type=str)
        for owner in owners:
            validate_asset_owner(owner, key)

        return super().__new__(
            cls,
            key=key,
            deps=asset_deps,
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
            owners=owners,
            tags=validate_tags_strict(tags) or {},
        )

    @staticmethod
    def dagster_internal_init(
        *,
        key: CoercibleToAssetKey,
        deps: Optional[Iterable["CoercibleToAssetDep"]],
        description: Optional[str],
        metadata: Optional[Mapping[str, Any]],
        skippable: bool,
        group_name: Optional[str],
        code_version: Optional[str],
        freshness_policy: Optional[FreshnessPolicy],
        auto_materialize_policy: Optional[AutoMaterializePolicy],
        owners: Optional[Sequence[str]],
        tags: Optional[Mapping[str, str]],
    ) -> "AssetSpec":
        return AssetSpec(
            key=key,
            deps=deps,
            description=description,
            metadata=metadata,
            skippable=skippable,
            group_name=group_name,
            code_version=code_version,
            freshness_policy=freshness_policy,
            auto_materialize_policy=auto_materialize_policy,
            owners=owners,
            tags=tags,
        )

    @cached_property
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:
        return {
            dep.asset_key: dep.partition_mapping
            for dep in self.deps
            if dep.partition_mapping is not None
        }
