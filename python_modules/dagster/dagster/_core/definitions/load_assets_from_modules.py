import inspect
import pkgutil
from collections import defaultdict
from functools import cached_property
from importlib import import_module
from types import ModuleType
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple, Type, Union

import dagster._check as check
from dagster._core.definitions.asset_key import (
    AssetKey,
    CoercibleToAssetKeyPrefix,
    check_opt_coercible_to_asset_key_prefix_param,
)
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


LoadableAssetTypes = Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]
KeyScopedAssetObjects = (AssetsDefinition, SourceAsset)


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
                        module, (AssetsDefinition, SourceAsset, CacheableAssetsDefinition)
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

    @cached_property
    def sources(self) -> Sequence[SourceAsset]:
        return [asset for asset in self.deduped_objects if isinstance(asset, SourceAsset)]

    @cached_property
    def assets_defs(self) -> Sequence[AssetsDefinition]:
        return [
            asset
            for asset in self.deduped_objects
            if isinstance(asset, AssetsDefinition) and asset.keys
        ]

    @cached_property
    def cacheable_assets_defs(self) -> Sequence[CacheableAssetsDefinition]:
        return [
            asset for asset in self.deduped_objects if isinstance(asset, CacheableAssetsDefinition)
        ]

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


def assets_from_modules(
    modules: Iterable[ModuleType],
) -> Tuple[Sequence[AssetsDefinition], Sequence[SourceAsset], Sequence[CacheableAssetsDefinition]]:
    """Constructs three lists, a list of assets, a list of source assets, and a list of cacheable
    assets from the given modules.

    Args:
        modules (Iterable[ModuleType]): The Python modules to look for assets inside.
        extra_source_assets (Optional[Sequence[SourceAsset]]): Source assets to include in the
            group in addition to the source assets found in the modules.

    Returns:
        Tuple[Sequence[AssetsDefinition], Sequence[SourceAsset], Sequence[CacheableAssetsDefinition]]]:
            A tuple containing a list of assets, a list of source assets, and a list of
            cacheable assets defined in the given modules.
    """
    assets_list = LoadedAssetsList.from_modules(modules)
    return assets_list.assets_defs, assets_list.sources, assets_list.cacheable_assets_defs


def key_iterator(asset: Union[AssetsDefinition, SourceAsset]) -> Iterator[AssetKey]:
    return iter(asset.keys) if isinstance(asset, AssetsDefinition) else iter([asset.key])


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
) -> Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]:
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
    group_name = check.opt_str_param(group_name, "group_name")
    key_prefix = check_opt_coercible_to_asset_key_prefix_param(key_prefix, "key_prefix")
    freshness_policy = check.opt_inst_param(freshness_policy, "freshness_policy", FreshnessPolicy)
    backfill_policy = check.opt_inst_param(backfill_policy, "backfill_policy", BackfillPolicy)

    (
        assets,
        source_assets,
        cacheable_assets,
    ) = assets_from_modules(modules)

    return assets_with_attributes(
        assets,
        source_assets,
        cacheable_assets,
        key_prefix=key_prefix,
        group_name=group_name,
        freshness_policy=freshness_policy,
        automation_condition=resolve_automation_condition(
            automation_condition, auto_materialize_policy
        ),
        backfill_policy=backfill_policy,
        source_key_prefix=source_key_prefix,
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
) -> Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]:
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
    )


def assets_from_package_module(
    package_module: ModuleType,
) -> Tuple[Sequence[AssetsDefinition], Sequence[SourceAsset], Sequence[CacheableAssetsDefinition]]:
    """Constructs three lists, a list of assets, a list of source assets, and a list of cacheable assets
    from the given package module.

    Args:
        package_module (ModuleType): The package module to looks for assets inside.
        extra_source_assets (Optional[Sequence[SourceAsset]]): Source assets to include in the
            group in addition to the source assets found in the modules.

    Returns:
        Tuple[Sequence[AssetsDefinition], Sequence[SourceAsset], Sequence[CacheableAssetsDefinition]]:
            A tuple containing a list of assets, a list of source assets, and a list of cacheable assets
            defined in the given modules.
    """
    return assets_from_modules(find_modules_in_package(package_module))


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
) -> Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]:
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
    group_name = check.opt_str_param(group_name, "group_name")
    key_prefix = check_opt_coercible_to_asset_key_prefix_param(key_prefix, "key_prefix")
    freshness_policy = check.opt_inst_param(freshness_policy, "freshness_policy", FreshnessPolicy)
    backfill_policy = check.opt_inst_param(backfill_policy, "backfill_policy", BackfillPolicy)

    (
        assets,
        source_assets,
        cacheable_assets,
    ) = assets_from_package_module(package_module)
    return assets_with_attributes(
        assets,
        source_assets,
        cacheable_assets,
        key_prefix=key_prefix,
        group_name=group_name,
        freshness_policy=freshness_policy,
        automation_condition=resolve_automation_condition(
            automation_condition, auto_materialize_policy
        ),
        backfill_policy=backfill_policy,
        source_key_prefix=source_key_prefix,
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
) -> Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]:
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


def prefix_assets(
    assets_defs: Sequence[AssetsDefinition],
    key_prefix: CoercibleToAssetKeyPrefix,
    source_assets: Sequence[SourceAsset],
    source_key_prefix: Optional[CoercibleToAssetKeyPrefix],
) -> Tuple[Sequence[AssetsDefinition], Sequence[SourceAsset]]:
    """Given a list of assets, prefix the input and output asset keys and check specs with key_prefix.
    The prefix is not added to source assets.

    Input asset keys that reference other assets within assets_defs are "brought along" -
    i.e. prefixed as well.

    Example with a single asset:

        .. code-block:: python

            @asset
            def asset1():
                ...

            result = prefixed_asset_key_replacements([asset_1], "my_prefix")
            assert result.assets[0].asset_key == AssetKey(["my_prefix", "asset1"])

    Example with dependencies within the list of assets:

        .. code-block:: python

            @asset
            def asset1():
                ...

            @asset
            def asset2(asset1):
                ...

            result = prefixed_asset_key_replacements([asset1, asset2], "my_prefix")
            assert result.assets[0].asset_key == AssetKey(["my_prefix", "asset1"])
            assert result.assets[1].asset_key == AssetKey(["my_prefix", "asset2"])
            assert result.assets[1].dependency_keys == {AssetKey(["my_prefix", "asset1"])}

    """
    asset_keys = {asset_key for assets_def in assets_defs for asset_key in assets_def.keys}
    check_target_keys = {
        key.asset_key for assets_def in assets_defs for key in assets_def.check_keys
    }
    source_asset_keys = {source_asset.key for source_asset in source_assets}

    if isinstance(key_prefix, str):
        key_prefix = [key_prefix]
    key_prefix = check.is_list(key_prefix, of_type=str)

    if isinstance(source_key_prefix, str):
        source_key_prefix = [source_key_prefix]

    result_assets: List[AssetsDefinition] = []
    for assets_def in assets_defs:
        output_asset_key_replacements = {
            asset_key: AssetKey([*key_prefix, *asset_key.path])
            for asset_key in (
                assets_def.keys | {check_key.asset_key for check_key in assets_def.check_keys}
            )
        }
        input_asset_key_replacements = {}
        for dep_asset_key in assets_def.keys_by_input_name.values():
            if dep_asset_key in asset_keys or dep_asset_key in check_target_keys:
                input_asset_key_replacements[dep_asset_key] = AssetKey(
                    [*key_prefix, *dep_asset_key.path]
                )
            elif source_key_prefix and dep_asset_key in source_asset_keys:
                input_asset_key_replacements[dep_asset_key] = AssetKey(
                    [*source_key_prefix, *dep_asset_key.path]
                )

        result_assets.append(
            assets_def.with_attributes(
                output_asset_key_replacements=output_asset_key_replacements,
                input_asset_key_replacements=input_asset_key_replacements,
            )
        )

    if source_key_prefix:
        result_source_assets = [
            source_asset.with_attributes(key=AssetKey([*source_key_prefix, *source_asset.key.path]))
            for source_asset in source_assets
        ]
    else:
        result_source_assets = source_assets

    return result_assets, result_source_assets


def assets_with_attributes(
    assets_defs: Sequence[AssetsDefinition],
    source_assets: Sequence[SourceAsset],
    cacheable_assets: Sequence[CacheableAssetsDefinition],
    key_prefix: Optional[Sequence[str]],
    group_name: Optional[str],
    freshness_policy: Optional[FreshnessPolicy],
    automation_condition: Optional[AutomationCondition],
    backfill_policy: Optional[BackfillPolicy],
    source_key_prefix: Optional[Sequence[str]],
) -> Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]:
    # There is a tricky edge case here where if a non-cacheable asset depends on a cacheable asset,
    # and the assets are prefixed, the non-cacheable asset's dependency will not be prefixed since
    # at prefix-time it is not known that its dependency is one of the cacheable assets.
    # https://github.com/dagster-io/dagster/pull/10389#pullrequestreview-1170913271
    if key_prefix:
        assets_defs, source_assets = prefix_assets(
            assets_defs, key_prefix, source_assets, source_key_prefix
        )
        cacheable_assets = [
            cached_asset.with_prefix_for_all(key_prefix) for cached_asset in cacheable_assets
        ]

    if group_name or freshness_policy or automation_condition or backfill_policy:
        assets_defs = [
            asset.with_attributes(
                group_names_by_key=(
                    {asset_key: group_name for asset_key in asset.keys}
                    if group_name is not None
                    else {}
                ),
                freshness_policy=freshness_policy,
                automation_condition=automation_condition,
                backfill_policy=backfill_policy,
            )
            for asset in assets_defs
        ]
        if group_name:
            source_assets = [
                source_asset.with_attributes(group_name=group_name)
                for source_asset in source_assets
            ]
        cacheable_assets = [
            cached_asset.with_attributes_for_all(
                group_name,
                freshness_policy=freshness_policy,
                auto_materialize_policy=automation_condition.as_auto_materialize_policy()
                if automation_condition
                else None,
                backfill_policy=backfill_policy,
            )
            for cached_asset in cacheable_assets
        ]

    return [*assets_defs, *source_assets, *cacheable_assets]
