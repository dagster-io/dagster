import inspect
from importlib import import_module
from types import ModuleType
from typing import Iterable, Optional, Sequence

import dagster._check as check

from .asset_checks import AssetChecksDefinition
from .events import (
    CoercibleToAssetKeyPrefix,
    check_opt_coercible_to_asset_key_prefix_param,
)
from .load_assets_from_modules import find_modules_in_package, find_objects_in_module_of_types


def _checks_from_modules(modules: Iterable[ModuleType]) -> Sequence[AssetChecksDefinition]:
    checks = []
    for module in modules:
        for c in find_objects_in_module_of_types(module, AssetChecksDefinition):
            checks.append(c)
    return checks


def _checks_with_attributes(
    checks_defs: Sequence[AssetChecksDefinition],
    asset_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
) -> Sequence[AssetChecksDefinition]:
    modified_checks = []
    for c in checks_defs:
        modified_checks.append(
            c.with_attributes(
                asset_key_prefix=asset_key_prefix,
            )
        )
    return modified_checks


def load_asset_checks_from_modules(
    modules: Iterable[ModuleType],
    asset_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
) -> Sequence[AssetChecksDefinition]:
    """Constructs a list of asset checks from the given modules. This is most often used in
    conjunction with a call to `load_assets_from_modules`.

    Args:
        modules (Iterable[ModuleType]): The Python modules to look for checks inside.
        asset_key_prefix (Optional[Union[str, Sequence[str]]]):
            The prefix for the asset keys targeted by the loaded checks. This should match the
            key_prefix argument to load_assets_from_modules.

    Returns:
        Sequence[AssetChecksDefinition]:
            A list containing asset checks defined in the given modules.
    """
    asset_key_prefix = check_opt_coercible_to_asset_key_prefix_param(
        asset_key_prefix, "asset_key_prefix"
    )

    return _checks_with_attributes(_checks_from_modules(modules), asset_key_prefix=asset_key_prefix)


def load_asset_checks_from_current_module(
    asset_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None
) -> Sequence[AssetChecksDefinition]:
    """Constructs a list of asset checks from the module where this function is called. This is most
    often used in conjunction with a call to `load_assets_from_current_module`.

    Args:
        asset_key_prefix (Optional[Union[str, Sequence[str]]]):
            The prefix for the asset keys targeted by the loaded checks. This should match the
            key_prefix argument to load_assets_from_current_module.

    Returns:
        Sequence[AssetChecksDefinition]:
            A list containing asset checks defined in the current module.
    """
    caller = inspect.stack()[1]
    module = inspect.getmodule(caller[0])
    if module is None:
        check.failed("Could not find a module for the caller")

    asset_key_prefix = check_opt_coercible_to_asset_key_prefix_param(
        asset_key_prefix, "asset_key_prefix"
    )

    return _checks_with_attributes(
        _checks_from_modules([module]), asset_key_prefix=asset_key_prefix
    )


def load_asset_checks_from_package_module(
    package_module: ModuleType, asset_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None
) -> Sequence[AssetChecksDefinition]:
    """Constructs a list of asset checks from all sub-modules of the given package module. This is
    most often used in conjunction with a call to `load_assets_from_package_module`.

    Args:
        package_module (ModuleType): The Python module to look for checks inside.
        asset_key_prefix (Optional[Union[str, Sequence[str]]]):
            The prefix for the asset keys targeted by the loaded checks. This should match the
            key_prefix argument to load_assets_from_package_module.

    Returns:
        Sequence[AssetChecksDefinition]:
            A list containing asset checks defined in the package.
    """
    asset_key_prefix = check_opt_coercible_to_asset_key_prefix_param(
        asset_key_prefix, "asset_key_prefix"
    )

    return _checks_with_attributes(
        _checks_from_modules(find_modules_in_package(package_module)),
        asset_key_prefix=asset_key_prefix,
    )


def load_asset_checks_from_package_name(
    package_name: str, asset_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None
) -> Sequence[AssetChecksDefinition]:
    """Constructs a list of asset checks from all sub-modules of the given package. This is most
    often used in conjunction with a call to `load_assets_from_package_name`.

    Args:
        package_name (str): The name of the Python package to look for checks inside.
        asset_key_prefix (Optional[Union[str, Sequence[str]]]):
            The prefix for the asset keys targeted by the loaded checks. This should match the
            key_prefix argument to load_assets_from_package_name.

    Returns:
        Sequence[AssetChecksDefinition]:
            A list containing asset checks defined in the package.
    """
    asset_key_prefix = check_opt_coercible_to_asset_key_prefix_param(
        asset_key_prefix, "asset_key_prefix"
    )

    package_module = import_module(package_name)
    return _checks_with_attributes(
        _checks_from_modules(find_modules_in_package(package_module)),
        asset_key_prefix=asset_key_prefix,
    )
