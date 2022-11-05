import inspect
import os
import pkgutil
from importlib import import_module
from types import ModuleType
from typing import Dict, Generator, Iterable, List, Optional, Sequence, Set, Tuple, Union

import dagster._check as check
from dagster._core.errors import DagsterInvalidDefinitionError

from .assets import AssetsDefinition
from .events import AssetKey, CoercibleToAssetKeyPrefix
from .source_asset import SourceAsset


def _find_assets_in_module(
    module: ModuleType,
) -> Generator[Union[AssetsDefinition, SourceAsset], None, None]:
    """
    Finds assets in the given module and adds them to the given sets of assets and source assets.
    """
    for attr in dir(module):
        value = getattr(module, attr)
        if isinstance(value, (AssetsDefinition, SourceAsset)):
            yield value
        elif isinstance(value, list) and all(
            isinstance(el, (AssetsDefinition, SourceAsset)) for el in value
        ):
            yield from value


def assets_and_source_assets_from_modules(
    modules: Iterable[ModuleType], extra_source_assets: Optional[Sequence[SourceAsset]] = None
) -> Tuple[List[AssetsDefinition], List[SourceAsset]]:
    """
    Constructs two lists, a list of assets and a list of source assets, from the given modules.

    Args:
        modules (Iterable[ModuleType]): The Python modules to look for assets inside.
        extra_source_assets (Optional[Sequence[SourceAsset]]): Source assets to include in the
            group in addition to the source assets found in the modules.

    Returns:
        Tuple[List[AssetsDefinition], List[SourceAsset]]:
            A tuple containing a list of assets and a list of source assets defined in the given modules.
    """
    asset_ids: Set[int] = set()
    asset_keys: Dict[AssetKey, ModuleType] = dict()
    source_assets: List[SourceAsset] = list(
        check.opt_sequence_param(extra_source_assets, "extra_source_assets", of_type=SourceAsset)
    )
    assets: Dict[AssetKey, AssetsDefinition] = {}
    for module in modules:
        for asset in _find_assets_in_module(module):
            if id(asset) not in asset_ids:
                asset_ids.add(id(asset))
                keys = asset.keys if isinstance(asset, AssetsDefinition) else [asset.key]
                for key in keys:
                    if key in asset_keys:
                        modules_str = ", ".join(set([asset_keys[key].__name__, module.__name__]))
                        error_str = f"Asset key {key} is defined multiple times. Definitions found in modules: {modules_str}. "

                        if key in assets and isinstance(asset, AssetsDefinition):
                            if assets[key].node_def == asset.node_def:
                                error_str += (
                                    "One possible cause of this bug is a call to with_resources outside of "
                                    "a repository definition, causing a duplicate asset definition."
                                )

                        raise DagsterInvalidDefinitionError(error_str)
                    else:
                        asset_keys[key] = module
                        if isinstance(asset, AssetsDefinition):
                            assets[key] = asset
                if isinstance(asset, SourceAsset):
                    source_assets.append(asset)
    return list(set(assets.values())), source_assets


def load_assets_from_modules(
    modules: Iterable[ModuleType],
    group_name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
) -> List[Union[AssetsDefinition, SourceAsset]]:
    """
    Constructs a list of assets and source assets from the given modules.

    Args:
        modules (Iterable[ModuleType]): The Python modules to look for assets inside.
        group_name (Optional[str]):
            Group name to apply to the loaded assets. The returned assets will be copies of the
            loaded objects, with the group name added.
        key_prefix (Optional[Union[str, List[str]]]):
            Prefix to prepend to the keys of the loaded assets. The returned assets will be copies
            of the loaded objects, with the prefix prepended.

    Returns:
        List[Union[AssetsDefinition, SourceAsset]]:
            A list containing assets and source assets defined in the given modules.
    """
    group_name = check.opt_str_param(group_name, "group_name")
    key_prefix = check.opt_inst_param(key_prefix, "key_prefix", (str, list))

    assets, source_assets = assets_and_source_assets_from_modules(modules)
    if key_prefix:
        assets = prefix_assets(assets, key_prefix)
    if group_name:
        assets = [
            asset.with_prefix_or_group(
                group_names_by_key={asset_key: group_name for asset_key in asset.keys}
            )
            for asset in assets
        ]
        source_assets = [source_asset.with_group_name(group_name) for source_asset in source_assets]

    return [*assets, *source_assets]


def load_assets_from_current_module(
    group_name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
) -> List[Union[AssetsDefinition, SourceAsset]]:
    """
    Constructs a list of assets and source assets from the module where this function is called.

    Args:
        group_name (Optional[str]):
            Group name to apply to the loaded assets. The returned assets will be copies of the
            loaded objects, with the group name added.
        key_prefix (Optional[Union[str, List[str]]]):
            Prefix to prepend to the keys of the loaded assets. The returned assets will be copies
            of the loaded objects, with the prefix prepended.

    Returns:
        List[Union[AssetsDefinition, SourceAsset]]:
            A list containing assets and source assets defined in the module.
    """
    caller = inspect.stack()[1]
    module = inspect.getmodule(caller[0])
    if module is None:
        check.failed("Could not find a module for the caller")

    return load_assets_from_modules(
        [module],
        group_name=group_name,
        key_prefix=key_prefix,
    )


def assets_and_source_assets_from_package_module(
    package_module: ModuleType,
    extra_source_assets: Optional[Sequence[SourceAsset]] = None,
) -> Tuple[List[AssetsDefinition], List[SourceAsset]]:
    """
    Constructs two lists, a list of assets and a list of source assets, from the given package module.

    Args:
        package_module (ModuleType): The package module to looks for assets inside.
        extra_source_assets (Optional[Sequence[SourceAsset]]): Source assets to include in the
            group in addition to the source assets found in the modules.

    Returns:
        Tuple[List[AssetsDefinition], List[SourceAsset]]:
            A tuple containing a list of assets and a list of source assets defined in the given modules.
    """
    return assets_and_source_assets_from_modules(
        _find_modules_in_package(package_module), extra_source_assets=extra_source_assets
    )


def load_assets_from_package_module(
    package_module: ModuleType,
    group_name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
) -> List[Union[AssetsDefinition, SourceAsset]]:
    """
    Constructs a list of assets and source assets that includes all asset
    definitions and source assets in all sub-modules of the given package module.

    A package module is the result of importing a package.

    Args:
        package_module (ModuleType): The package module to looks for assets inside.
        group_name (Optional[str]):
            Group name to apply to the loaded assets. The returned assets will be copies of the
            loaded objects, with the group name added.
        key_prefix (Optional[Union[str, List[str]]]):
            Prefix to prepend to the keys of the loaded assets. The returned assets will be copies
            of the loaded objects, with the prefix prepended.

    Returns:
        List[Union[AssetsDefinition, SourceAsset]]:
            A list containing assets and source assets defined in the module.
    """
    group_name = check.opt_str_param(group_name, "group_name")
    key_prefix = check.opt_inst_param(key_prefix, "key_prefix", (str, list))

    assets, source_assets = assets_and_source_assets_from_package_module(package_module)
    if key_prefix:
        assets = prefix_assets(assets, key_prefix)
    if group_name:
        assets = list(with_group(assets, group_name))
        source_assets = [asset.with_group_name(group_name) for asset in source_assets]

    return [*assets, *source_assets]


def load_assets_from_package_name(
    package_name: str,
    group_name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
) -> List[Union[AssetsDefinition, SourceAsset]]:
    """
    Constructs a list of assets and source assets that include all asset
    definitions and source assets in all sub-modules of the given package.

    Args:
        package_name (str): The name of a Python package to look for assets inside.
        group_name (Optional[str]):
            Group name to apply to the loaded assets. The returned assets will be copies of the
            loaded objects, with the group name added.
        key_prefix (Optional[Union[str, List[str]]]):
            Prefix to prepend to the keys of the loaded assets. The returned assets will be copies
            of the loaded objects, with the prefix prepended.

    Returns:
        List[Union[AssetsDefinition, SourceAsset]]:
            A list containing assets and source assets defined in the module.
    """
    package_module = import_module(package_name)
    return load_assets_from_package_module(
        package_module,
        group_name=group_name,
        key_prefix=key_prefix,
    )


def _find_modules_in_package(package_module: ModuleType) -> Iterable[ModuleType]:
    yield package_module
    package_path = package_module.__file__
    if package_path:
        for _, modname, is_pkg in pkgutil.walk_packages([os.path.dirname(package_path)]):
            submodule = import_module(f"{package_module.__name__}.{modname}")
            if is_pkg:
                yield from _find_modules_in_package(submodule)
            else:
                yield submodule
    else:
        raise ValueError(
            f"Tried to find modules in package {package_module}, but its __file__ is None"
        )


def prefix_assets(
    assets_defs: Sequence[AssetsDefinition], key_prefix: CoercibleToAssetKeyPrefix
) -> List[AssetsDefinition]:
    """
    Given a list of assets, prefix the input and output asset keys with key_prefix.
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

    if isinstance(key_prefix, str):
        key_prefix = [key_prefix]
    key_prefix = check.is_list(key_prefix, of_type=str)

    result_assets: List[AssetsDefinition] = []
    for assets_def in assets_defs:
        output_asset_key_replacements = {
            asset_key: AssetKey(key_prefix + asset_key.path) for asset_key in assets_def.keys
        }
        input_asset_key_replacements = {}
        for dep_asset_key in assets_def.dependency_keys:
            if dep_asset_key in asset_keys:
                input_asset_key_replacements[dep_asset_key] = AssetKey(
                    key_prefix + dep_asset_key.path
                )

        result_assets.append(
            assets_def.with_prefix_or_group(
                output_asset_key_replacements=output_asset_key_replacements,
                input_asset_key_replacements=input_asset_key_replacements,
            )
        )
    return result_assets


def with_group(
    assets_defs: Sequence[AssetsDefinition], group_name: Optional[str]
) -> Sequence[AssetsDefinition]:
    """
    Given a list of assets, groups them under the group_name.
    """
    group_name = check.opt_str_param(group_name, "group_name")
    if not group_name:
        return assets_defs

    return [
        assets_def.with_prefix_or_group(
            group_names_by_key={asset_key: group_name for asset_key in assets_def.keys}
        )
        for assets_def in assets_defs
    ]
