import inspect
import os
import pkgutil
from importlib import import_module
from types import ModuleType
from typing import Dict, Generator, Iterable, List, Optional, Sequence, Set, Tuple, Union

import dagster._check as check
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.errors import DagsterInvalidDefinitionError

from .assets import AssetsDefinition
from .asset_checks import AssetChecksDefinition
from .cacheable_assets import CacheableAssetsDefinition
from .events import (
    AssetKey,
    CoercibleToAssetKeyPrefix,
    check_opt_coercible_to_asset_key_prefix_param,
)
from .source_asset import SourceAsset


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
        for check in _find_checks_in_module(module):
            checks.append(check)
    return checks


def _checks_with_attributes(
    checks_defs: Sequence[AssetChecksDefinition],
    group_name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
) -> Sequence[AssetChecksDefinition]:
    modified_checks = []
    for check in checks_defs:
        modified_checks.append(
            check.with_attributes(
                group_name=group_name,
                key_prefix=key_prefix,
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

    return assets_with_attributes(
        assets,
        source_assets,
        cacheable_assets,
        key_prefix=key_prefix,
        group_name=group_name,
        freshness_policy=freshness_policy,
        auto_materialize_policy=auto_materialize_policy,
        backfill_policy=backfill_policy,
        source_key_prefix=source_key_prefix,
    )
