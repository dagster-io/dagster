from typing import AbstractSet, Dict, Iterable, Mapping, Tuple, cast

from dagster.core.definitions.events import AssetKey
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.utils.backcompat import experimental_warning

from .assets import AssetsDefinition
from .source_asset import SourceAsset


class ResolvedAssetDependencies:
    """
    An asset can depend on another asset without specifying the full asset key for the upstream
    asset, if the name and groups match.

    ResolvedAssetDependencies maps these flexible dependencies to precise key-based dependencies.
    """

    def __init__(
        self, assets_defs: Iterable[AssetsDefinition], source_assets: Iterable[SourceAsset]
    ):
        self._deps_by_assets_def_id = resolve_assets_def_deps(assets_defs, source_assets)

    def get_resolved_upstream_asset_keys(
        self, assets_def: AssetsDefinition, asset_key: AssetKey
    ) -> AbstractSet[AssetKey]:
        resolved_keys_by_unresolved_key = self._deps_by_assets_def_id.get(id(assets_def), {})
        unresolved_upstream_keys = assets_def.asset_deps[asset_key]
        return {
            resolved_keys_by_unresolved_key.get(unresolved_key, unresolved_key)
            for unresolved_key in unresolved_upstream_keys
        }

    def get_resolved_asset_key_for_input(
        self, assets_def: AssetsDefinition, input_name: str
    ) -> AssetKey:
        unresolved_asset_key_for_input = assets_def.node_keys_by_input_name[input_name]
        return self._deps_by_assets_def_id.get(id(assets_def), {}).get(
            unresolved_asset_key_for_input, unresolved_asset_key_for_input
        )


def resolve_assets_def_deps(
    assets_defs: Iterable[AssetsDefinition], source_assets: Iterable[SourceAsset]
) -> Mapping[int, Mapping[AssetKey, AssetKey]]:
    """
    For each AssetsDefinition, resolves its inputs to upstream asset keys. Matches based on either
    of two criteria:
    - The input asset key exactly matches an asset key.
    - The input asset key has one component, that component matches the final component of an asset
        key, and they're both in the same asset group.

    The returned dictionary only contains entries for assets definitions with group-resolved asset
    dependencies.
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

    warned = False

    result: Dict[int, Mapping[AssetKey, AssetKey]] = {}
    for assets_def in assets_defs:
        group = (
            next(iter(assets_def.group_names_by_key.values()))
            if len(assets_def.group_names_by_key) == 1
            else None
        )

        resolved_keys_by_unresolved_key: Dict[AssetKey, AssetKey] = {}
        for input_name, upstream_key in assets_def.keys_by_input_name.items():
            if upstream_key not in asset_keys and len(upstream_key) == 1:
                group_and_upstream_name = (group, upstream_key.path[-1])
                if group is not None and group_and_upstream_name in asset_keys_by_group_and_name:
                    resolved_key = asset_keys_by_group_and_name[
                        cast(Tuple[str, str], group_and_upstream_name)
                    ]
                    resolved_keys_by_unresolved_key[upstream_key] = resolved_key

                    if not warned:
                        experimental_warning(
                            f"Asset {next(iter(assets_def.keys)).to_string()}'s dependency "
                            f"'{upstream_key.path[-1]}' was resolved to upstream asset "
                            f"{resolved_key.to_string()}, because the name matches and they're in the same "
                            "group. This is experimental functionality that may change in a future "
                            "release"
                        )

                        warned = True
                elif (
                    upstream_key not in asset_keys
                    and not assets_def.node_def.input_def_named(input_name).dagster_type.is_nothing
                ):
                    raise DagsterInvalidDefinitionError(
                        f"Input asset '{upstream_key.to_string()}' for asset "
                        f"'{next(iter(assets_def.keys)).to_string()}' is not "
                        "produced by any of the provided asset ops and is not one of the provided "
                        "sources"
                    )

        if resolved_keys_by_unresolved_key:
            result[id(assets_def)] = resolved_keys_by_unresolved_key

    return result
