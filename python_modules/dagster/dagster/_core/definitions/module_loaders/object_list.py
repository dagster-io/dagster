from collections import defaultdict
from functools import cached_property
from types import ModuleType
from typing import Callable, Dict, Iterable, Mapping, Optional, Sequence, Union, cast

from dagster._core.definitions.asset_checks import AssetChecksDefinition, has_only_asset_checks
from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKeyPrefix
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.module_loaders.utils import (
    KeyScopedAssetObjects,
    LoadableAssetTypes,
    find_objects_in_module_of_types,
    key_iterator,
    replace_keys_in_asset,
)
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.utils import DEFAULT_GROUP_NAME
from dagster._core.errors import DagsterInvalidDefinitionError


class LoadedAssetsList:
    def __init__(
        self,
        assets_per_module: Mapping[str, Sequence[LoadableAssetTypes]],
    ):
        self.assets_per_module = assets_per_module
        self._do_collision_detection()

    @classmethod
    def from_modules(cls, modules: Iterable[ModuleType]) -> "LoadedAssetsList":
        return cls(
            {
                module.__name__: list(
                    find_objects_in_module_of_types(
                        module,
                        (AssetsDefinition, SourceAsset, CacheableAssetsDefinition, AssetSpec),
                    )
                )
                for module in modules
            },
        )

    @cached_property
    def flat_object_list(self) -> Sequence[LoadableAssetTypes]:
        return [
            asset_object for objects in self.assets_per_module.values() for asset_object in objects
        ]

    @cached_property
    def objects_by_id(self) -> Dict[int, LoadableAssetTypes]:
        return {id(asset_object): asset_object for asset_object in self.flat_object_list}

    @cached_property
    def deduped_objects(self) -> Sequence[LoadableAssetTypes]:
        return list(self.objects_by_id.values())

    @cached_property
    def assets_defs(self) -> Sequence[AssetsDefinition]:
        return [asset for asset in self.deduped_objects if isinstance(asset, AssetsDefinition)]

    @cached_property
    def source_assets(self) -> Sequence[SourceAsset]:
        return [asset for asset in self.deduped_objects if isinstance(asset, SourceAsset)]

    @cached_property
    def module_name_by_id(self) -> Dict[int, str]:
        return {
            id(asset_object): module_name
            for module_name, objects in self.assets_per_module.items()
            for asset_object in objects
        }

    @cached_property
    def objects_by_key(self) -> Mapping[AssetKey, Sequence[Union[SourceAsset, AssetsDefinition]]]:
        objects_by_key = defaultdict(list)
        for asset_object in self.flat_object_list:
            if not isinstance(asset_object, KeyScopedAssetObjects):
                continue
            for key in key_iterator(asset_object):
                objects_by_key[key].append(asset_object)
        return objects_by_key

    def _do_collision_detection(self) -> None:
        for key, asset_objects in self.objects_by_key.items():
            # If there is more than one asset_object in the list for a given key, and the objects do not refer to the same asset_object in memory, we have a collision.
            num_distinct_objects_for_key = len(
                set(id(asset_object) for asset_object in asset_objects)
            )
            if len(asset_objects) > 1 and num_distinct_objects_for_key > 1:
                asset_objects_str = ", ".join(
                    set(self.module_name_by_id[id(asset_object)] for asset_object in asset_objects)
                )
                raise DagsterInvalidDefinitionError(
                    f"Asset key {key.to_user_string()} is defined multiple times. Definitions found in modules: {asset_objects_str}."
                )

    def to_post_load(self) -> "ResolvedAssetObjectList":
        return ResolvedAssetObjectList(self.deduped_objects)


class ResolvedAssetObjectList:
    def __init__(
        self,
        loaded_objects: Sequence[LoadableAssetTypes],
    ):
        self.loaded_objects = loaded_objects

    @cached_property
    def assets_defs_and_specs(self) -> Sequence[Union[AssetsDefinition, AssetSpec]]:
        return [
            asset
            for asset in self.loaded_objects
            if (isinstance(asset, AssetsDefinition) and asset.keys) or isinstance(asset, AssetSpec)
        ]

    @cached_property
    def assets_defs(self) -> Sequence[AssetsDefinition]:
        return [asset for asset in self.loaded_objects if isinstance(asset, AssetsDefinition)]

    @cached_property
    def checks_defs(self) -> Sequence[AssetChecksDefinition]:
        return [
            cast(AssetChecksDefinition, asset)
            for asset in self.loaded_objects
            if isinstance(asset, AssetsDefinition) and has_only_asset_checks(asset)
        ]

    @cached_property
    def assets_defs_specs_and_checks_defs(
        self,
    ) -> Sequence[Union[AssetsDefinition, AssetSpec, AssetChecksDefinition]]:
        return [*self.assets_defs_and_specs, *self.checks_defs]

    @cached_property
    def source_assets(self) -> Sequence[SourceAsset]:
        return [asset for asset in self.loaded_objects if isinstance(asset, SourceAsset)]

    @cached_property
    def cacheable_assets(self) -> Sequence[CacheableAssetsDefinition]:
        return [
            asset for asset in self.loaded_objects if isinstance(asset, CacheableAssetsDefinition)
        ]

    def get_objects(
        self, filter_fn: Callable[[LoadableAssetTypes], bool]
    ) -> Sequence[LoadableAssetTypes]:
        return [asset for asset in self.loaded_objects if filter_fn(asset)]

    def assets_with_loadable_prefix(
        self, key_prefix: CoercibleToAssetKeyPrefix
    ) -> "ResolvedAssetObjectList":
        # There is a tricky edge case here where if a non-cacheable asset depends on a cacheable asset,
        # and the assets are prefixed, the non-cacheable asset's dependency will not be prefixed since
        # at prefix-time it is not known that its dependency is one of the cacheable assets.
        # https://github.com/dagster-io/dagster/pull/10389#pullrequestreview-1170913271
        result_list = []
        all_asset_keys = {
            key
            for asset_object in self.assets_defs_specs_and_checks_defs
            for key in key_iterator(asset_object, included_targeted_keys=True)
        }
        all_check_keys = {
            check_key for asset_object in self.assets_defs for check_key in asset_object.check_keys
        }

        key_replacements = {key: key.with_prefix(key_prefix) for key in all_asset_keys}
        check_key_replacements = {
            check_key: check_key.with_asset_key_prefix(key_prefix) for check_key in all_check_keys
        }
        for asset_object in self.loaded_objects:
            if isinstance(asset_object, CacheableAssetsDefinition):
                result_list.append(asset_object.with_prefix_for_all(key_prefix))
            elif isinstance(asset_object, AssetsDefinition):
                result_list.append(
                    replace_keys_in_asset(asset_object, key_replacements, check_key_replacements)
                )
            else:
                # We don't replace the key for SourceAssets.
                result_list.append(asset_object)
        return ResolvedAssetObjectList(result_list)

    def assets_with_source_prefix(
        self, key_prefix: CoercibleToAssetKeyPrefix
    ) -> "ResolvedAssetObjectList":
        result_list = []
        key_replacements = {
            source_asset.key: source_asset.key.with_prefix(key_prefix)
            for source_asset in self.source_assets
        }
        for asset_object in self.loaded_objects:
            if isinstance(asset_object, KeyScopedAssetObjects):
                result_list.append(
                    replace_keys_in_asset(asset_object, key_replacements, check_key_replacements={})
                )
            else:
                result_list.append(asset_object)
        return ResolvedAssetObjectList(result_list)

    def with_attributes(
        self,
        key_prefix: Optional[CoercibleToAssetKeyPrefix],
        source_key_prefix: Optional[CoercibleToAssetKeyPrefix],
        group_name: Optional[str],
        freshness_policy: Optional[FreshnessPolicy],
        automation_condition: Optional[AutomationCondition],
        backfill_policy: Optional[BackfillPolicy],
    ) -> "ResolvedAssetObjectList":
        assets_list = self.assets_with_loadable_prefix(key_prefix) if key_prefix else self
        assets_list = (
            assets_list.assets_with_source_prefix(source_key_prefix)
            if source_key_prefix
            else assets_list
        )
        return_list = []
        for asset in assets_list.loaded_objects:
            if isinstance(asset, AssetsDefinition):
                new_asset = asset.map_asset_specs(
                    _spec_mapper_disallow_group_override(group_name, automation_condition)
                ).with_attributes(
                    backfill_policy=backfill_policy, freshness_policy=freshness_policy
                )
                return_list.append(
                    new_asset.coerce_to_checks_def()
                    if has_only_asset_checks(new_asset)
                    else new_asset
                )
            elif isinstance(asset, SourceAsset):
                return_list.append(
                    asset.with_attributes(group_name=group_name if group_name else asset.group_name)
                )
            elif isinstance(asset, AssetSpec):
                return_list.append(
                    _spec_mapper_disallow_group_override(group_name, automation_condition)(asset)
                )
            else:
                return_list.append(
                    asset.with_attributes_for_all(
                        group_name,
                        freshness_policy=freshness_policy,
                        auto_materialize_policy=automation_condition.as_auto_materialize_policy()
                        if automation_condition
                        else None,
                        backfill_policy=backfill_policy,
                    )
                )
        return ResolvedAssetObjectList(return_list)


def _spec_mapper_disallow_group_override(
    group_name: Optional[str], automation_condition: Optional[AutomationCondition]
) -> Callable[[AssetSpec], AssetSpec]:
    def _inner(spec: AssetSpec) -> AssetSpec:
        if (
            group_name is not None
            and spec.group_name is not None
            and group_name != spec.group_name
            and spec.group_name != DEFAULT_GROUP_NAME
        ):
            raise DagsterInvalidDefinitionError(
                f"Asset spec {spec.key.to_user_string()} has group name {spec.group_name}, which conflicts with the group name {group_name} provided in load_assets_from_modules."
            )
        return spec.replace_attributes(
            group_name=group_name if group_name else ...,
            automation_condition=automation_condition if automation_condition else ...,
        )

    return _inner
