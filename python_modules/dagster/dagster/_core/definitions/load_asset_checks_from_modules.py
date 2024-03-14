import inspect
from importlib import import_module
from types import ModuleType
from typing import Iterable, Optional, Sequence, cast

import dagster._check as check
from dagster._core.definitions.assets import AssetsDefinition

from .asset_checks import AssetChecksDefinition, has_only_asset_checks
from .asset_key import (
    CoercibleToAssetKeyPrefix,
    check_opt_coercible_to_asset_key_prefix_param,
)
from .load_assets_from_modules import (
    find_modules_in_package,
    find_objects_in_module_of_types,
    prefix_assets,
)


def _checks_from_modules(modules: Iterable[ModuleType]) -> Sequence[AssetChecksDefinition]:
    checks = []
    for module in modules:
        for c in find_objects_in_module_of_types(module, AssetsDefinition):
            if has_only_asset_checks(c):
                checks.append(cast(AssetChecksDefinition, c))
    return checks


def _checks_with_attributes(
    checks_defs: Sequence[AssetChecksDefinition],
    asset_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
) -> Sequence[AssetChecksDefinition]:
    modified_checks = []
    if asset_key_prefix:
        modified_checks, _ = prefix_assets(checks_defs, asset_key_prefix, [], None)
        return cast(Sequence[AssetChecksDefinition], modified_checks)
    else:
        return checks_defs


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
    asset_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
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
