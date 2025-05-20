from functools import cached_property

from dagster_shared import check

from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey, CoercibleToAssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.external_asset import create_external_asset_from_source_asset
from dagster._core.definitions.source_asset import SourceAsset


def canonicalize_assets_in_definitions(
    definitions: Definitions,
) -> tuple[
    dict[AssetKey, AssetSpec],
    dict[AssetKey, AssetsDefinition],
    dict[AssetCheckKey, AssetChecksDefinition],
]:
    asset_specs: dict[AssetKey, AssetSpec] = {}
    assets_defs: dict[AssetKey, AssetsDefinition] = {}
    asset_checks_defs: dict[AssetCheckKey, AssetChecksDefinition] = {}

    for asset_or_asset_check in list(definitions.assets or []) + list(
        definitions.asset_checks or []
    ):
        if isinstance(asset_or_asset_check, CacheableAssetsDefinition):
            raise ValueError(
                "CacheableAssetsDefinitions are not allowed in components. Convert to AssetsDefinition"
            )
        elif isinstance(asset_or_asset_check, SourceAsset):
            external_assets_def = create_external_asset_from_source_asset(asset_or_asset_check)
            if asset_or_asset_check.is_observable:
                assets_defs[asset_or_asset_check.key] = external_assets_def
                asset_specs[asset_or_asset_check.key] = external_assets_def.get_asset_spec(
                    asset_or_asset_check.key
                )
            else:
                for key in external_assets_def.keys:
                    asset_specs[key] = external_assets_def.get_asset_spec(key)
        elif isinstance(asset_or_asset_check, AssetSpec):
            asset_specs[asset_or_asset_check.key] = asset_or_asset_check
        # AssetsDefinitions or AssetChecksDefinitions can be passed to either definitions.assets or definitions.asset_checks
        elif isinstance(asset_or_asset_check, AssetChecksDefinition):
            for key in asset_or_asset_check.check_keys:
                asset_checks_defs[key] = asset_or_asset_check
        elif isinstance(asset_or_asset_check, AssetsDefinition):
            for key in asset_or_asset_check.keys:
                assets_defs[key] = asset_or_asset_check
                asset_specs[key] = asset_or_asset_check.get_asset_spec(key)
        else:
            check.failed(f"Unexpected asset type: {type(asset_or_asset_check)}")
    return asset_specs, assets_defs, asset_checks_defs


class Defs:
    """Represents all the definitions in a particular defs module. This can also be used as a convenience wrapper class around
    _any_ `Definitions` object.

    Defs is a read-only class guaranteed to not instigate a binding step that could result in missing resource errors.

    Defs also canonicalizes and denormalizes definitions strewn about the Definitions object.

    * definitions.assets and definitions.asset_checks can _both_ contain AssetsDefinitions and AssetChecksDefinitions (oy vey).
      We canonicalize this. An AssetsCheckDefinition passed to asset or asset_checks will end up in the asset_checks_def dictionary and
      not the assets_defs dictionary. Similarly, an AssetsDefinition passed to asset or asset_checks will end up in the assets_defs dictionary
      and not the asset_checks_defs dictionary.


    """

    def __init__(self, definitions: Definitions):
        asset_specs, assets_defs, asset_checks_defs = canonicalize_assets_in_definitions(
            definitions
        )

        self.asset_specs = asset_specs
        self._assets_defs = assets_defs
        self.asset_checks_defs = asset_checks_defs

    @property
    def assets_defs(self) -> dict[AssetKey, AssetsDefinition]:
        return self._assets_defs

    def get_asset_spec(self, asset_key: CoercibleToAssetKey) -> AssetSpec:
        return self.asset_specs[AssetKey.from_coercible(asset_key)]

    # TODO add coercible to asset check key
    def get_asset_check_spec(self, check_key: AssetCheckKey) -> AssetCheckSpec:
        return self.asset_check_specs[check_key]

    @cached_property
    def asset_check_specs(self) -> dict[AssetCheckKey, AssetCheckSpec]:
        asset_check_specs: dict[AssetCheckKey, AssetCheckSpec] = {}
        for assets_def in self.assets_defs.values():
            for check_key in assets_def.check_keys:
                asset_check_specs[check_key] = assets_def.get_spec_for_check_key(check_key)

        for asset_check_def in self.asset_checks_defs.values():
            for check_key in asset_check_def.check_keys:
                asset_check_specs[check_key] = asset_check_def.get_spec_for_check_key(check_key)

        return asset_check_specs

    @cached_property
    def asset_specs(self) -> dict[AssetKey, AssetSpec]:
        return {
            **{
                assets_def.key: assets_def.get_asset_spec(assets_def.key)
                for assets_def in self.assets_defs.values()
            },
            **self.asset_specs,
        }

    def get_assets_def(self, asset_key: CoercibleToAssetKey) -> AssetsDefinition:
        return self.assets_defs[AssetKey.from_coercible(asset_key)]

    def get_assets_def_for_check_key(self, check_key: AssetCheckKey) -> AssetsDefinition:
        for assets_def in self.assets_defs.values():
            if check_key in assets_def.check_keys:
                return assets_def
        check.failed(f"AssetsDefinition not found for check key: {check_key}")

    @cached_property
    def asset_checks_defs(self) -> dict[AssetCheckKey, AssetChecksDefinition]:
        asset_checks_defs: dict[AssetCheckKey, AssetChecksDefinition] = {}
        for asset_checks_def in self.asset_checks_defs.values():
            for asset_check_key in asset_checks_def.check_keys:
                asset_checks_defs[asset_check_key] = asset_checks_def
        return asset_checks_defs
