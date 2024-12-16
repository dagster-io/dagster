import inspect
import pkgutil
from collections import defaultdict
from functools import cached_property
from importlib import import_module
from types import ModuleType
from typing import (
    Callable,
    Dict,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

import dagster._check as check
from dagster._core.definitions.asset_checks import AssetChecksDefinition, has_only_asset_checks
from dagster._core.definitions.asset_key import (
    AssetCheckKey,
    AssetKey,
    CoercibleToAssetKeyPrefix,
    check_opt_coercible_to_asset_key_prefix_param,
)
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.utils import resolve_automation_condition
from dagster._core.errors import DagsterInvalidDefinitionError


def find_objects_in_module_of_types(
    module: ModuleType,
    types: Union[Type, Tuple[Type, ...]],
) -> Iterator:
    """Yields instances or subclasses of the given type(s)."""
    for attr in dir(module):
        value = getattr(module, attr)
        if isinstance(value, types):
            yield value
        elif isinstance(value, list) and all(isinstance(el, types) for el in value):
            yield from value


def find_subclasses_in_module(
    module: ModuleType,
    types: Union[Type, Tuple[Type, ...]],
) -> Iterator:
    """Yields instances or subclasses of the given type(s)."""
    for attr in dir(module):
        value = getattr(module, attr)
        if isinstance(value, type) and issubclass(value, types):
            yield value


LoadableAssetTypes = Union[AssetsDefinition, AssetSpec, SourceAsset, CacheableAssetsDefinition]
KeyScopedAssetObjects = (AssetsDefinition, AssetSpec, SourceAsset)


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
                affected_modules = set(
                    self.module_name_by_id[id(asset_object)] for asset_object in asset_objects
                )
                asset_objects_str = ", ".join(affected_modules)
                modules_str = (
                    f"Definitions found in modules: {asset_objects_str}."
                    if len(affected_modules) > 1
                    else ""
                )
                raise DagsterInvalidDefinitionError(
                    f"Asset key {key.to_user_string()} is defined multiple times. {modules_str}".strip()
                )

    def to_post_load(self) -> "ResolvedAssetObjectList":
        return ResolvedAssetObjectList(self.deduped_objects)


def key_iterator(
    asset: Union[AssetsDefinition, SourceAsset, AssetSpec], included_targeted_keys: bool = False
) -> Iterator[AssetKey]:
    return (
        iter(
            [
                *asset.keys,
                *(
                    [check_key.asset_key for check_key in asset.check_keys]
                    if included_targeted_keys
                    else []
                ),
            ]
        )
        if isinstance(asset, AssetsDefinition)
        else iter([asset.key])
    )


def load_assets_from_modules(
    modules: Iterable[ModuleType],
    group_name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    *,
    freshness_policy: Optional[FreshnessPolicy] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
    automation_condition: Optional[AutomationCondition] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    source_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    include_specs: bool = False,
) -> Sequence[Union[AssetsDefinition, AssetSpec, SourceAsset, CacheableAssetsDefinition]]:
    """Constructs a list of assets and source assets from the given modules.

    Args:
        modules (Iterable[ModuleType]): The Python modules to look for assets inside.
        group_name (Optional[str]):
            Group name to apply to the loaded assets. The returned assets will be copies of the
            loaded objects, with the group name added.
        key_prefix (Optional[Union[str, Sequence[str]]]):
            Prefix to prepend to the keys of the loaded assets. The returned assets will be copies
            of the loaded objects, with the prefix prepended.
        freshness_policy (Optional[FreshnessPolicy]): FreshnessPolicy to apply to all the loaded
            assets.
        automation_condition (Optional[AutomationCondition]): AutomationCondition to apply
            to all the loaded assets.
        backfill_policy (Optional[AutoMaterializePolicy]): BackfillPolicy to apply to all the loaded assets.
        source_key_prefix (bool): Prefix to prepend to the keys of loaded SourceAssets. The returned
            assets will be copies of the loaded objects, with the prefix prepended.

    Returns:
        Sequence[Union[AssetsDefinition, SourceAsset]]:
            A list containing assets and source assets defined in the given modules.
    """

    def _asset_filter(asset: LoadableAssetTypes) -> bool:
        if isinstance(asset, AssetsDefinition):
            # We don't load asset checks with asset module loaders.
            return not has_only_asset_checks(asset)
        if isinstance(asset, AssetSpec):
            return include_specs
        return True

    return (
        LoadedAssetsList.from_modules(modules)
        .to_post_load()
        .with_attributes(
            key_prefix=check_opt_coercible_to_asset_key_prefix_param(key_prefix, "key_prefix"),
            source_key_prefix=check_opt_coercible_to_asset_key_prefix_param(
                source_key_prefix, "source_key_prefix"
            ),
            group_name=check.opt_str_param(group_name, "group_name"),
            freshness_policy=check.opt_inst_param(
                freshness_policy, "freshness_policy", FreshnessPolicy
            ),
            automation_condition=resolve_automation_condition(
                automation_condition, auto_materialize_policy
            ),
            backfill_policy=check.opt_inst_param(
                backfill_policy, "backfill_policy", BackfillPolicy
            ),
        )
        .get_objects(_asset_filter)
    )


def load_assets_from_current_module(
    group_name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    *,
    freshness_policy: Optional[FreshnessPolicy] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
    automation_condition: Optional[AutomationCondition] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    source_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    include_specs: bool = False,
) -> Sequence[Union[AssetsDefinition, AssetSpec, SourceAsset, CacheableAssetsDefinition]]:
    """Constructs a list of assets, source assets, and cacheable assets from the module where
    this function is called.

    Args:
        group_name (Optional[str]):
            Group name to apply to the loaded assets. The returned assets will be copies of the
            loaded objects, with the group name added.
        key_prefix (Optional[Union[str, Sequence[str]]]):
            Prefix to prepend to the keys of the loaded assets. The returned assets will be copies
            of the loaded objects, with the prefix prepended.
        freshness_policy (Optional[FreshnessPolicy]): FreshnessPolicy to apply to all the loaded
            assets.
        automation_condition (Optional[AutomationCondition]): AutomationCondition to apply
            to all the loaded assets.
        backfill_policy (Optional[AutoMaterializePolicy]): BackfillPolicy to apply to all the loaded assets.
        source_key_prefix (bool): Prefix to prepend to the keys of loaded SourceAssets. The returned
            assets will be copies of the loaded objects, with the prefix prepended.

    Returns:
        Sequence[Union[AssetsDefinition, SourceAsset, CachableAssetsDefinition]]:
            A list containing assets, source assets, and cacheable assets defined in the module.
    """
    caller = inspect.stack()[1]
    module = inspect.getmodule(caller[0])
    if module is None:
        check.failed("Could not find a module for the caller")

    return load_assets_from_modules(
        [module],
        group_name=group_name,
        key_prefix=key_prefix,
        freshness_policy=freshness_policy,
        automation_condition=resolve_automation_condition(
            automation_condition, auto_materialize_policy
        ),
        backfill_policy=backfill_policy,
        source_key_prefix=source_key_prefix,
        include_specs=include_specs,
    )


def load_assets_from_package_module(
    package_module: ModuleType,
    group_name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    *,
    freshness_policy: Optional[FreshnessPolicy] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
    automation_condition: Optional[AutomationCondition] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    source_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    include_specs: bool = False,
) -> Sequence[LoadableAssetTypes]:
    """Constructs a list of assets and source assets that includes all asset
    definitions, source assets, and cacheable assets in all sub-modules of the given package module.

    A package module is the result of importing a package.

    Args:
        package_module (ModuleType): The package module to looks for assets inside.
        group_name (Optional[str]):
            Group name to apply to the loaded assets. The returned assets will be copies of the
            loaded objects, with the group name added.
        key_prefix (Optional[Union[str, Sequence[str]]]):
            Prefix to prepend to the keys of the loaded assets. The returned assets will be copies
            of the loaded objects, with the prefix prepended.
        freshness_policy (Optional[FreshnessPolicy]): FreshnessPolicy to apply to all the loaded
            assets.
        automation_condition (Optional[AutomationCondition]): AutomationCondition to apply
            to all the loaded assets.
        backfill_policy (Optional[AutoMaterializePolicy]): BackfillPolicy to apply to all the loaded assets.
        source_key_prefix (bool): Prefix to prepend to the keys of loaded SourceAssets. The returned
            assets will be copies of the loaded objects, with the prefix prepended.

    Returns:
        Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]:
            A list containing assets, source assets, and cacheable assets defined in the module.
    """
    return load_assets_from_modules(
        [*find_modules_in_package(package_module)],
        group_name,
        key_prefix,
        freshness_policy=freshness_policy,
        auto_materialize_policy=auto_materialize_policy,
        automation_condition=automation_condition,
        backfill_policy=backfill_policy,
        source_key_prefix=source_key_prefix,
        include_specs=include_specs,
    )


def load_assets_from_package_name(
    package_name: str,
    group_name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    *,
    freshness_policy: Optional[FreshnessPolicy] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    source_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    include_specs: bool = False,
) -> Sequence[Union[AssetsDefinition, AssetSpec, SourceAsset, CacheableAssetsDefinition]]:
    """Constructs a list of assets, source assets, and cacheable assets that includes all asset
    definitions and source assets in all sub-modules of the given package.

    Args:
        package_name (str): The name of a Python package to look for assets inside.
        group_name (Optional[str]):
            Group name to apply to the loaded assets. The returned assets will be copies of the
            loaded objects, with the group name added.
        key_prefix (Optional[Union[str, Sequence[str]]]):
            Prefix to prepend to the keys of the loaded assets. The returned assets will be copies
            of the loaded objects, with the prefix prepended.
        freshness_policy (Optional[FreshnessPolicy]): FreshnessPolicy to apply to all the loaded
            assets.
        auto_materialize_policy (Optional[AutoMaterializePolicy]): AutoMaterializePolicy to apply
            to all the loaded assets.
        backfill_policy (Optional[AutoMaterializePolicy]): BackfillPolicy to apply to all the loaded assets.
        source_key_prefix (bool): Prefix to prepend to the keys of loaded SourceAssets. The returned
            assets will be copies of the loaded objects, with the prefix prepended.

    Returns:
        Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]:
            A list containing assets, source assets, and cacheable assets defined in the module.
    """
    package_module = import_module(package_name)
    return load_assets_from_package_module(
        package_module,
        group_name=group_name,
        key_prefix=key_prefix,
        freshness_policy=freshness_policy,
        auto_materialize_policy=auto_materialize_policy,
        backfill_policy=backfill_policy,
        source_key_prefix=source_key_prefix,
        include_specs=include_specs,
    )


def find_modules_in_package(package_module: ModuleType) -> Iterable[ModuleType]:
    yield package_module
    if package_module.__file__:
        for _, modname, is_pkg in pkgutil.walk_packages(
            package_module.__path__, prefix=package_module.__name__ + "."
        ):
            submodule = import_module(modname)
            if is_pkg:
                yield from find_modules_in_package(submodule)
            else:
                yield submodule
    else:
        raise ValueError(
            f"Tried to find modules in package {package_module}, but its __file__ is None"
        )


def replace_keys_in_asset(
    asset: Union[AssetsDefinition, AssetSpec, SourceAsset],
    key_replacements: Mapping[AssetKey, AssetKey],
    check_key_replacements: Mapping[AssetCheckKey, AssetCheckKey],
) -> Union[AssetsDefinition, AssetSpec, SourceAsset]:
    if isinstance(asset, SourceAsset):
        return asset.with_attributes(key=key_replacements.get(asset.key, asset.key))
    if isinstance(asset, AssetSpec):
        return asset.replace_attributes(
            key=key_replacements.get(asset.key, asset.key),
        )
    else:
        updated_object = asset.with_attributes(
            asset_key_replacements=key_replacements,
        )
        return (
            updated_object.coerce_to_checks_def()
            if has_only_asset_checks(updated_object)
            else updated_object
        )


class ResolvedAssetObjectList:
    def __init__(
        self,
        loaded_objects: Sequence[LoadableAssetTypes],
    ):
        self.loaded_objects = loaded_objects

    @cached_property
    def assets_defs_and_specs(self) -> Sequence[Union[AssetsDefinition, AssetSpec]]:
        return [
            dagster_object
            for dagster_object in self.loaded_objects
            if (isinstance(dagster_object, AssetsDefinition) and dagster_object.keys)
            or isinstance(dagster_object, AssetSpec)
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
            updated_object = asset.with_attributes(
                group_name=group_name,
                freshness_policy=freshness_policy,
                automation_condition=automation_condition,
                backfill_policy=backfill_policy,
            )
            return_list.append(
                updated_object.coerce_to_checks_def()
                if isinstance(updated_object, AssetsDefinition)
                and has_only_asset_checks(updated_object)
                else updated_object
            )
        return ResolvedAssetObjectList(return_list)
