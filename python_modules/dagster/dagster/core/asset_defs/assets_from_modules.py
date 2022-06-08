import inspect
import os
import pkgutil
from importlib import import_module
from types import ModuleType
from typing import Dict, Generator, Iterable, List, Optional, Sequence, Set, Tuple, Union

import dagster._check as check
from dagster.core.definitions.events import AssetKey

from ..errors import DagsterInvalidDefinitionError
from .assets import AssetsDefinition
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
    assets: List[AssetsDefinition] = []
    for module in modules:
        for asset in _find_assets_in_module(module):
            if id(asset) not in asset_ids:
                asset_ids.add(id(asset))
                keys = asset.asset_keys if isinstance(asset, AssetsDefinition) else [asset.key]
                for key in keys:
                    if key in asset_keys:
                        modules_str = ", ".join(set([asset_keys[key].__name__, module.__name__]))
                        raise DagsterInvalidDefinitionError(
                            f"Asset key {key} is defined multiple times. Definitions found in modules: {modules_str}."
                        )
                    else:
                        asset_keys[key] = module
                if isinstance(asset, SourceAsset):
                    source_assets.append(asset)
                else:
                    assets.append(asset)
    return assets, source_assets


def assets_from_modules(
    modules: Iterable[ModuleType], extra_source_assets: Optional[Sequence[SourceAsset]] = None
) -> List[Union[AssetsDefinition, SourceAsset]]:
    """
    Constructs a list of assets and source assets from the given modules.

    Args:
        modules (Iterable[ModuleType]): The Python modules to look for assets inside.
        extra_source_assets (Optional[Sequence[SourceAsset]]): Source assets to include in the
            group in addition to the source assets found in the modules.

    Returns:
        List[Union[AssetsDefinition, SourceAsset]]:
            A list containing assets and source assets defined in the given modules.
    """
    assets, source_assets = assets_and_source_assets_from_modules(
        modules, extra_source_assets=extra_source_assets
    )
    return [*assets, *source_assets]


def assets_from_current_module(
    extra_source_assets: Optional[Sequence[SourceAsset]] = None,
) -> List[Union[AssetsDefinition, SourceAsset]]:
    """
    Constructs a list of assets and source assets from the module where this function is called.

    Args:
        extra_source_assets (Optional[Sequence[SourceAsset]]): Source assets to include in the
            group in addition to the source assets found in the modules.

    Returns:
        List[Union[AssetsDefinition, SourceAsset]]:
            A list containing assets and source assets defined in the module.
    """
    caller = inspect.stack()[1]
    module = inspect.getmodule(caller[0])
    if module is None:
        check.failed("Could not find a module for the caller")

    return assets_from_modules([module], extra_source_assets=extra_source_assets)


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


def assets_from_package_module(
    package_module: ModuleType,
    extra_source_assets: Optional[Sequence[SourceAsset]] = None,
) -> List[Union[AssetsDefinition, SourceAsset]]:
    """
    Constructs a list of assets and source assets that includes all asset
    definitions and source assets in all sub-modules of the given package module.

    A package module is the result of importing a package.

    Args:
        package_module (ModuleType): The package module to looks for assets inside.
        extra_source_assets (Optional[Sequence[SourceAsset]]): Source assets to include in the
            group in addition to the source assets found in the modules.

    Returns:
        List[Union[AssetsDefinition, SourceAsset]]:
            A list containing assets and source assets defined in the module.
    """
    assets, source_assets = assets_and_source_assets_from_package_module(
        package_module, extra_source_assets
    )
    return [*assets, *source_assets]


def assets_from_package_name(
    package_name: str, extra_source_assets: Optional[Sequence[SourceAsset]] = None
) -> List[Union[AssetsDefinition, SourceAsset]]:
    """
    Constructs a list of assets and source assets that include all asset
    definitions and source assets in all sub-modules of the given package.

    Args:
        package_name (str): The name of a Python package to look for assets inside.
        extra_source_assets (Optional[Sequence[SourceAsset]]): Source assets to include in the
            group in addition to the source assets found in the modules.

    Returns:
        List[Union[AssetsDefinition, SourceAsset]]:
            A list containing assets and source assets defined in the module.
    """
    package_module = import_module(package_name)
    return assets_from_package_module(package_module, extra_source_assets=extra_source_assets)


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
