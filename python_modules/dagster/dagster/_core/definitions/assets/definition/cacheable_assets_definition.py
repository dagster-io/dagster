import hashlib
import json
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import AbstractSet, Any, NamedTuple, Optional, Union  # noqa: UP035

from dagster_shared.serdes import serialize_value
from dagster_shared.serdes.errors import SerializationError
from dagster_shared.utils.hash import hash_collection

import dagster._check as check
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKeyPrefix
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.resource_requirement import ResourceAddable
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes(
    storage_field_names={
        "legacy_freshness_policies_by_output_name": "freshness_policies_by_output_name",
    }
)
class AssetsDefinitionCacheableData(
    NamedTuple(
        "_AssetsDefinitionCacheableData",
        [
            ("keys_by_input_name", Optional[Mapping[str, AssetKey]]),
            ("keys_by_output_name", Optional[Mapping[str, AssetKey]]),
            ("internal_asset_deps", Optional[Mapping[str, AbstractSet[AssetKey]]]),
            ("group_name", Optional[str]),
            ("metadata_by_output_name", Optional[Mapping[str, RawMetadataMapping]]),
            ("key_prefix", Optional[CoercibleToAssetKeyPrefix]),
            ("can_subset", bool),
            ("extra_metadata", Optional[Mapping[Any, Any]]),
            (
                "legacy_freshness_policies_by_output_name",
                Optional[Mapping[str, LegacyFreshnessPolicy]],
            ),
            (
                "auto_materialize_policies_by_output_name",
                Optional[Mapping[str, AutoMaterializePolicy]],
            ),
            ("backfill_policy", Optional[BackfillPolicy]),
        ],
    )
):
    """Data representing cacheable metadata about assets, which can be used to generate
    AssetsDefinition objects in other processes.
    """

    def __new__(
        cls,
        keys_by_input_name: Optional[Mapping[str, AssetKey]] = None,
        keys_by_output_name: Optional[Mapping[str, AssetKey]] = None,
        internal_asset_deps: Optional[Mapping[str, AbstractSet[AssetKey]]] = None,
        group_name: Optional[str] = None,
        metadata_by_output_name: Optional[Mapping[str, RawMetadataMapping]] = None,
        key_prefix: Optional[Sequence[str]] = None,
        can_subset: bool = False,
        extra_metadata: Optional[Mapping[Any, Any]] = None,
        legacy_freshness_policies_by_output_name: Optional[
            Mapping[str, LegacyFreshnessPolicy]
        ] = None,
        auto_materialize_policies_by_output_name: Optional[
            Mapping[str, AutoMaterializePolicy]
        ] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
    ):
        extra_metadata = check.opt_nullable_mapping_param(extra_metadata, "extra_metadata")
        try:
            # check that the value can pass through the serdes layer
            serialize_value(extra_metadata)
        except SerializationError:
            check.failed("Value for `extra_metadata` is not JSON serializable.")

        return super().__new__(
            cls,
            keys_by_input_name=check.opt_nullable_mapping_param(
                keys_by_input_name, "keys_by_input_name", key_type=str, value_type=AssetKey
            ),
            keys_by_output_name=check.opt_nullable_mapping_param(
                keys_by_output_name, "keys_by_output_name", key_type=str, value_type=AssetKey
            ),
            internal_asset_deps=check.opt_nullable_mapping_param(
                internal_asset_deps,
                "internal_asset_deps",
                key_type=str,
                value_type=(set, frozenset),
            ),
            group_name=check.opt_str_param(group_name, "group_name"),
            metadata_by_output_name=check.opt_nullable_mapping_param(
                metadata_by_output_name, "metadata_by_output_name", key_type=str
            ),
            key_prefix=(
                [key_prefix]
                if isinstance(key_prefix, str)
                else check.opt_list_param(key_prefix, "key_prefix", of_type=str)
            ),
            can_subset=check.opt_bool_param(can_subset, "can_subset", default=False),
            extra_metadata=extra_metadata,
            legacy_freshness_policies_by_output_name=check.opt_nullable_mapping_param(
                legacy_freshness_policies_by_output_name,
                "legacy_freshness_policies_by_output_name",
                key_type=str,
                value_type=LegacyFreshnessPolicy,
            ),
            auto_materialize_policies_by_output_name=check.opt_nullable_mapping_param(
                auto_materialize_policies_by_output_name,
                "auto_materialize_policies_by_output_name",
                key_type=str,
                value_type=AutoMaterializePolicy,
            ),
            backfill_policy=check.opt_inst_param(
                backfill_policy, "backfill_policy", BackfillPolicy
            ),
        )

    # Allow this to be hashed for use in `lru_cache`. This is needed because:
    # - `ReconstructableJob` uses `lru_cache`
    # - `ReconstructableJob` has a `ReconstructableRepository` attribute
    # - `ReconstructableRepository` has a `RepositoryLoadData` attribute
    # - `RepositoryLoadData` has a `Mapping` attribute containing `AssetsDefinitionCacheableData`
    # - `AssetsDefinitionCacheableData` has collection attributes that are unhashable by default
    def __hash__(self) -> int:
        if not hasattr(self, "_hash"):
            self._hash = hash_collection(self)
        return self._hash


class CacheableAssetsDefinition(ResourceAddable, ABC):
    def __init__(self, unique_id: str):
        self._unique_id = unique_id

    @property
    def unique_id(self) -> str:
        """A unique identifier, which can be used to index the cacheable data."""
        return self._unique_id

    @abstractmethod
    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        """Returns an object representing cacheable information about assets which are not defined
        in Python code.
        """
        raise NotImplementedError()

    @abstractmethod
    def build_definitions(
        self, data: Sequence[AssetsDefinitionCacheableData]
    ) -> Sequence[AssetsDefinition]:
        """For a given set of AssetsDefinitionMetadata, return a list of AssetsDefinitions."""
        raise NotImplementedError()

    def with_resources(
        self, resource_defs: Mapping[str, ResourceDefinition]
    ) -> "CacheableAssetsDefinition":
        return ResourceWrappedCacheableAssetsDefinition(self, resource_defs)

    def with_attributes(
        self,
        asset_key_replacements: Optional[Mapping[AssetKey, AssetKey]] = None,
        group_names_by_key: Optional[Mapping[AssetKey, str]] = None,
        legacy_freshness_policy: Optional[
            Union[LegacyFreshnessPolicy, Mapping[AssetKey, LegacyFreshnessPolicy]]
        ] = None,
    ) -> "CacheableAssetsDefinition":
        return PrefixOrGroupWrappedCacheableAssetsDefinition(
            self,
            asset_key_replacements=asset_key_replacements,
            group_names_by_key=group_names_by_key,
            legacy_freshness_policy=legacy_freshness_policy,
        )

    def with_prefix_for_all(self, prefix: CoercibleToAssetKeyPrefix) -> "CacheableAssetsDefinition":
        """Utility method which allows setting an asset key prefix for all assets in this
        CacheableAssetsDefinition, since the keys may not be known at the time of
        construction.
        """
        if isinstance(prefix, str):
            prefix = [prefix]
        prefix = check.is_list(prefix, of_type=str)
        return PrefixOrGroupWrappedCacheableAssetsDefinition(self, prefix_for_all_assets=prefix)

    def with_attributes_for_all(
        self,
        group_name: Optional[str],
        legacy_freshness_policy: Optional[LegacyFreshnessPolicy],
        auto_materialize_policy: Optional[AutoMaterializePolicy],
        backfill_policy: Optional[BackfillPolicy],
    ) -> "CacheableAssetsDefinition":
        """Utility method which allows setting attributes for all assets in this
        CacheableAssetsDefinition, since the keys may not be known at the time of
        construction.
        """
        return PrefixOrGroupWrappedCacheableAssetsDefinition(
            self,
            group_name_for_all_assets=group_name,
            legacy_freshness_policy=legacy_freshness_policy,
            auto_materialize_policy=auto_materialize_policy,
            backfill_policy=backfill_policy,
        )


class WrappedCacheableAssetsDefinition(CacheableAssetsDefinition):
    """Wraps an instance of CacheableAssetsDefinition, applying transformed_assets_def to the
    generated AssetsDefinition objects. This lets e.g. users define resources on
    the cacheable assets at repo creation time which are not actually bound until
    the assets themselves are created.
    """

    def __init__(
        self,
        unique_id: str,
        wrapped: CacheableAssetsDefinition,
    ):
        super().__init__(unique_id)
        self._wrapped = wrapped

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        return self._wrapped.compute_cacheable_data()

    def build_definitions(
        self, data: Sequence[AssetsDefinitionCacheableData]
    ) -> Sequence[AssetsDefinition]:
        return [
            self.transformed_assets_def(assets_def)
            for assets_def in self._wrapped.build_definitions(data)
        ]

    @abstractmethod
    def transformed_assets_def(self, assets_def: AssetsDefinition) -> AssetsDefinition:
        """Implement this method to transform the AssetsDefinition objects
        generated by the underlying, wrapped CacheableAssetsDefinition.
        """
        raise NotImplementedError()


def _map_to_hashable(mapping: Mapping[Any, Any]) -> bytes:
    return json.dumps(
        {json.dumps(k, sort_keys=True): v for k, v in mapping.items()},
        sort_keys=True,
    ).encode("utf-8")


class PrefixOrGroupWrappedCacheableAssetsDefinition(WrappedCacheableAssetsDefinition):
    """Represents a CacheableAssetsDefinition that has been wrapped with an asset
    prefix mapping or group name mapping.
    """

    def __init__(
        self,
        wrapped: CacheableAssetsDefinition,
        asset_key_replacements: Optional[Mapping[AssetKey, AssetKey]] = None,
        group_names_by_key: Optional[Mapping[AssetKey, str]] = None,
        group_name_for_all_assets: Optional[str] = None,
        prefix_for_all_assets: Optional[list[str]] = None,
        legacy_freshness_policy: Optional[
            Union[LegacyFreshnessPolicy, Mapping[AssetKey, LegacyFreshnessPolicy]]
        ] = None,
        auto_materialize_policy: Optional[
            Union[AutoMaterializePolicy, Mapping[AssetKey, AutoMaterializePolicy]]
        ] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
    ):
        self._asset_key_replacements = asset_key_replacements or {}
        self._group_names_by_key = group_names_by_key or {}
        self._group_name_for_all_assets = group_name_for_all_assets
        self._prefix_for_all_assets = prefix_for_all_assets
        self._legacy_freshness_policy = legacy_freshness_policy
        self._auto_materialize_policy = auto_materialize_policy
        self._backfill_policy = backfill_policy

        check.invariant(
            not (group_name_for_all_assets and group_names_by_key),
            "Cannot set both group_name_for_all_assets and group_names_by_key",
        )
        check.invariant(
            not (prefix_for_all_assets and (asset_key_replacements)),
            "Cannot set both prefix_for_all_assets and asset_key_replacements",
        )

        super().__init__(
            unique_id=f"{wrapped.unique_id}_prefix_or_group_{self._get_hash()}",
            wrapped=wrapped,
        )

    def _get_hash(self) -> str:
        """Generate a stable hash of the various prefix/group mappings."""
        contents = hashlib.sha1()
        if self._asset_key_replacements:
            contents.update(
                _map_to_hashable(
                    {tuple(k.path): tuple(v.path) for k, v in self._asset_key_replacements.items()}
                )
            )
        if self._group_names_by_key:
            contents.update(
                _map_to_hashable(
                    {tuple(k.path): v for k, v in self._group_names_by_key.items()},
                )
            )
        if self._group_name_for_all_assets:
            contents.update(self._group_name_for_all_assets.encode("utf-8"))
        if self._prefix_for_all_assets:
            contents.update(json.dumps(self._prefix_for_all_assets).encode("utf-8"))
        return contents.hexdigest()

    def transformed_assets_def(self, assets_def: AssetsDefinition) -> AssetsDefinition:
        group_names_by_key = (
            {
                k: self._group_name_for_all_assets
                for k in assets_def.keys
                if self._group_name_for_all_assets
            }
            if self._group_name_for_all_assets
            else self._group_names_by_key
        )
        asset_key_replacements = (
            {
                k: k.with_prefix(self._prefix_for_all_assets) if self._prefix_for_all_assets else k
                for k in assets_def.keys | set(assets_def.dependency_keys)
            }
            if self._prefix_for_all_assets
            else self._asset_key_replacements
        )
        if isinstance(self._auto_materialize_policy, dict):
            automation_condition = {
                k: v.to_automation_condition() for k, v in self._auto_materialize_policy.items()
            }
        elif isinstance(self._auto_materialize_policy, AutoMaterializePolicy):
            automation_condition = self._auto_materialize_policy.to_automation_condition()
        else:
            automation_condition = None
        return assets_def.with_attributes(
            asset_key_replacements=asset_key_replacements,
            group_names_by_key=group_names_by_key,
            legacy_freshness_policy=self._legacy_freshness_policy,
            automation_condition=automation_condition,
            backfill_policy=self._backfill_policy,
        )


class ResourceWrappedCacheableAssetsDefinition(WrappedCacheableAssetsDefinition):
    """Represents a CacheableAssetsDefinition that has been wrapped with resources."""

    def __init__(
        self,
        wrapped: CacheableAssetsDefinition,
        resource_defs: Mapping[str, ResourceDefinition],
    ):
        self._resource_defs = resource_defs

        super().__init__(
            unique_id=f"{wrapped.unique_id}_with_resources",
            wrapped=wrapped,
        )

    def transformed_assets_def(self, assets_def: AssetsDefinition) -> AssetsDefinition:
        return assets_def.with_resources(
            resource_defs=self._resource_defs,
        )
