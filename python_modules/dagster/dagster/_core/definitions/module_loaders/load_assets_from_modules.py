import inspect
from collections.abc import Iterable, Iterator, Sequence
from importlib import import_module
from types import ModuleType
from typing import Optional, Union, cast, get_args

import dagster._check as check
from dagster._core.definitions.asset_checks import has_only_asset_checks
from dagster._core.definitions.asset_key import (
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
from dagster._core.definitions.module_loaders.object_list import ModuleScopedDagsterDefs
from dagster._core.definitions.module_loaders.utils import find_modules_in_package
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.utils import resolve_automation_condition


def find_objects_in_module_of_types(
    module: ModuleType,
    types: Union[type, tuple[type, ...]],
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
    types: Union[type, tuple[type, ...]],
) -> Iterator[type]:
    """Yields instances or subclasses of the given type(s)."""
    for attr in dir(module):
        value = getattr(module, attr)
        if isinstance(value, type) and issubclass(value, types):
            yield value


AssetLoaderTypes = Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition, AssetSpec]


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
) -> Sequence[AssetLoaderTypes]:
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

    def _asset_filter(dagster_object) -> bool:
        if isinstance(dagster_object, AssetsDefinition):
            # We don't load asset checks with asset module loaders.
            return not has_only_asset_checks(dagster_object)
        return True

    types_to_load: tuple[type] = (
        get_args(AssetLoaderTypes)
        if include_specs
        else tuple(t for t in get_args(AssetLoaderTypes) if t != AssetSpec)
    )
    return cast(
        Sequence[AssetLoaderTypes],
        ModuleScopedDagsterDefs.from_modules(modules, types_to_load=types_to_load)
        .get_object_list()
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
        .get_objects(_asset_filter),
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
) -> Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition, AssetSpec]]:
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
) -> Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition, AssetSpec]]:
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
) -> Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition, AssetSpec]]:
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
