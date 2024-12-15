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
from dagster._core.definitions.utils import DEFAULT_GROUP_NAME, resolve_automation_condition
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


def _spec_mapper_disallow_group_override(
    group_name: Optional[str],
    automation_condition: Optional[AutomationCondition],
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


def key_iterator(
    asset: Union[AssetsDefinition, SourceAsset], included_targeted_keys: bool = False
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
        .assets_only
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


def replace_keys_in_asset(
    asset: Union[AssetsDefinition, SourceAsset],
    key_replacements: Mapping[AssetKey, AssetKey],
) -> Union[AssetsDefinition, SourceAsset]:
    updated_object = (
        asset.with_attributes(
            output_asset_key_replacements={
                key: key_replacements.get(key, key)
                for key in key_iterator(asset, included_targeted_keys=True)
            },
            input_asset_key_replacements={
                key: key_replacements.get(key, key) for key in asset.keys_by_input_name.values()
            },
        )
        if isinstance(asset, AssetsDefinition)
        else asset.with_attributes(key=key_replacements.get(asset.key, asset.key))
    )
    if isinstance(asset, AssetChecksDefinition):
        updated_object = cast(AssetsDefinition, updated_object)
        updated_object = AssetChecksDefinition.create(
            keys_by_input_name=updated_object.keys_by_input_name,
            node_def=updated_object.op,
            check_specs_by_output_name=updated_object.check_specs_by_output_name,
            resource_defs=updated_object.resource_defs,
            can_subset=updated_object.can_subset,
        )
    return updated_object


class ResolvedAssetObjectList:
    def __init__(
        self,
        loaded_objects: Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]],
    ):
        self.loaded_objects = loaded_objects

    @cached_property
    def assets_defs(self) -> Sequence[AssetsDefinition]:
        return [
            dagster_object
            for dagster_object in self.loaded_objects
            if isinstance(dagster_object, AssetsDefinition) and dagster_object.keys
        ]

    @cached_property
    def checks_defs(self) -> Sequence[AssetChecksDefinition]:
        return [
            cast(AssetChecksDefinition, asset)
            for asset in self.loaded_objects
            if isinstance(asset, AssetsDefinition) and has_only_asset_checks(asset)
        ]

    @cached_property
    def assets_and_checks_defs(self) -> Sequence[Union[AssetsDefinition, AssetChecksDefinition]]:
        return [*self.assets_defs, *self.checks_defs]

    @cached_property
    def source_assets(self) -> Sequence[SourceAsset]:
        return [asset for asset in self.loaded_objects if isinstance(asset, SourceAsset)]

    @cached_property
    def cacheable_assets(self) -> Sequence[CacheableAssetsDefinition]:
        return [
            asset for asset in self.loaded_objects if isinstance(asset, CacheableAssetsDefinition)
        ]

    @cached_property
    def assets_only(self) -> Sequence[LoadableAssetTypes]:
        return [*self.source_assets, *self.assets_defs, *self.cacheable_assets]

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
            for asset_object in self.assets_and_checks_defs
            for key in key_iterator(asset_object, included_targeted_keys=True)
        }
        key_replacements = {key: key.with_prefix(key_prefix) for key in all_asset_keys}
        for asset_object in self.loaded_objects:
            if isinstance(asset_object, CacheableAssetsDefinition):
                result_list.append(asset_object.with_prefix_for_all(key_prefix))
            elif isinstance(asset_object, AssetsDefinition):
                result_list.append(replace_keys_in_asset(asset_object, key_replacements))
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
                result_list.append(replace_keys_in_asset(asset_object, key_replacements))
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
                if isinstance(asset, AssetChecksDefinition):
                    new_asset = AssetChecksDefinition.create(
                        keys_by_input_name=new_asset.keys_by_input_name,
                        node_def=new_asset.op,
                        check_specs_by_output_name=new_asset.check_specs_by_output_name,
                        resource_defs=new_asset.resource_defs,
                        can_subset=new_asset.can_subset,
                    )
                return_list.append(new_asset)
            elif isinstance(asset, SourceAsset):
                return_list.append(
                    asset.with_attributes(group_name=group_name if group_name else asset.group_name)
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
