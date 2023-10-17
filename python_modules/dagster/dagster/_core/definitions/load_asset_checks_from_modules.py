from types import ModuleType
from typing import Generator, Iterable, Optional, Sequence

import dagster._check as check

from .asset_checks import AssetChecksDefinition
from .events import (
    CoercibleToAssetKeyPrefix,
    check_opt_coercible_to_asset_key_prefix_param,
)


def _find_checks_in_module(
    module: ModuleType,
) -> Generator[AssetChecksDefinition, None, None]:
    """Finds assets in the given module and adds them to the given sets of assets and source assets."""
    for attr in dir(module):
        value = getattr(module, attr)
        if isinstance(value, AssetChecksDefinition):
            yield value
        elif isinstance(value, list) and all(isinstance(el, AssetChecksDefinition) for el in value):
            yield from value


def _checks_from_modules(modules: Iterable[ModuleType]) -> Sequence[AssetChecksDefinition]:
    checks = []
    for module in modules:
        for c in _find_checks_in_module(module):
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
    group_name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
) -> Sequence[AssetChecksDefinition]:
    """Constructs a list of assets and source assets from the given modules.

    Args:
        modules (Iterable[ModuleType]): The Python modules to look for checks inside.
        group_name (Optional[str]):
            Group name to apply to the loaded checks. The returned checks will be copies of the
            loaded objects, with the group name added.
        key_prefix (Optional[Union[str, Sequence[str]]]):
            Prefix to prepend to the keys of the loaded checks. The returned checks will be copies
            of the loaded objects, with the prefix prepended.

    Returns:
        Sequence[AssetChecksDefinition]:
            A list containing checks defined in the given modules.
    """
    group_name = check.opt_str_param(group_name, "group_name")
    key_prefix = check_opt_coercible_to_asset_key_prefix_param(key_prefix, "key_prefix")

    return _checks_with_attributes(_checks_from_modules(modules), asset_key_prefix=key_prefix)
