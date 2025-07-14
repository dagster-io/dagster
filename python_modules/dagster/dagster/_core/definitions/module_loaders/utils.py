import pkgutil
from collections.abc import Iterable, Iterator, Mapping
from importlib import import_module
from types import ModuleType
from typing import Union

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.source_asset import SourceAsset


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
) -> Iterator:
    """Yields instances or subclasses of the given type(s)."""
    for attr in dir(module):
        value = getattr(module, attr)
        if isinstance(value, type) and issubclass(value, types):
            yield value


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
) -> Union[AssetsDefinition, AssetSpec, SourceAsset]:
    if isinstance(asset, SourceAsset):
        return asset.with_attributes(key=key_replacements.get(asset.key, asset.key))
    if isinstance(asset, AssetSpec):
        return asset.replace_attributes(
            key=key_replacements.get(asset.key, asset.key),
        )
    else:
        updated_object = asset.with_attributes(asset_key_replacements=key_replacements)
        return updated_object
