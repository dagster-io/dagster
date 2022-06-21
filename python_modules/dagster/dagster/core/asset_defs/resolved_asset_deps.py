from typing import AbstractSet, Dict, Iterable, List, Mapping, Sequence, Set, Tuple

from dagster.core.definitions.events import AssetKey
from dagster.core.errors import DagsterInvalidDefinitionError

from .assets import AssetsDefinition
from .source_asset import SourceAsset


class ResolvedAssetDependencies:
    def __init__(
        self, assets_defs: Iterable[AssetsDefinition], source_assets: Iterable[SourceAsset]
    ):
        self._deps_by_assets_def_id = resolve_assets_def_deps(assets_defs, source_assets)

    def get_resolved_upstream_asset_keys(
        self, assets_def: AssetsDefinition, asset_key: AssetKey
    ) -> AbstractSet[AssetKey]:
        return self._deps_by_assets_def_id[id(assets_def)].values()

    def get_resolved_asset_key_for_input(
        self, assets_def: AssetsDefinition, input_name: str
    ) -> AssetKey:
        return self._deps_by_assets_def_id[id(assets_def)][input_name]


def resolve_assets_def_deps(
    assets_defs: Iterable[AssetsDefinition], source_assets: Iterable[SourceAsset]
) -> Mapping[int, Mapping[str, AssetKey]]:
    """
    For each AssetsDefinition, resolves its inputs to upstream asset keys. Matches based on either
    of two criteria:
    - The input asset key exactly matches an asset key.
    - The input asset key has one component, that component matches the final component of an asset
        key, and they're both in the same asset group.
    """
    asset_keys_by_group_and_name: Dict[Tuple[str, str], AssetKey] = {}
    for assets_def in assets_defs:
        for key in assets_def.keys:
            asset_keys_by_group_and_name[(assets_def.group_names_by_key[key], key.path[-1])] = key
    for source_asset in source_assets:
        asset_keys_by_group_and_name[
            (source_asset.group_name, source_asset.key.path[-1])
        ] = source_asset.key

    asset_keys = set(asset_keys_by_group_and_name.values())

    result: Mapping[int, Mapping[str, AssetKey]] = {}
    for assets_def in assets_defs:
        group = (
            next(iter(assets_def.group_names_by_key.values()))
            if len(assets_def.group_names_by_key) == 1
            else None
        )

        dep_keys_by_input_name: Dict[str, AssetKey] = {}
        for input_name, upstream_asset_key in assets_def.keys_by_input_name.items():
            group_and_upstream_name = (group, upstream_asset_key.path[-1])
            if upstream_asset_key in asset_keys:
                dep_keys_by_input_name[input_name] = upstream_asset_key
            elif group is not None and group_and_upstream_name in asset_keys_by_group_and_name:
                dep_keys_by_input_name[input_name] = asset_keys_by_group_and_name[
                    group_and_upstream_name
                ]
            else:
                raise DagsterInvalidDefinitionError(
                    f"Input asset '{upstream_asset_key.to_string()}' for asset "
                    f"'{next(iter(assets_def.keys)).to_string()}' is not "
                    "produced by any of the provided asset ops and is not one of the provided "
                    "sources"
                )

        result[id(assets_def)] = dep_keys_by_input_name

    return result
