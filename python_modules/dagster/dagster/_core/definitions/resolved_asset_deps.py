from collections import defaultdict
from typing import AbstractSet, Dict, Iterable, List, Mapping, Tuple, cast

from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.warnings import experimental_warning

from .assets import AssetsDefinition
from .source_asset import SourceAsset


class ResolvedAssetDependencies:
    """An asset can depend on another asset without specifying the full asset key for the upstream
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
    """For each AssetsDefinition, resolves its inputs to upstream asset keys. Matches based on either
    of two criteria:
    - The input asset key exactly matches an asset key.
    - The input asset key has one component, that component matches the final component of an asset
        key, and they're both in the same asset group.

    The returned dictionary only contains entries for assets definitions with group-resolved asset
    dependencies.
    """
    group_names_by_key: Dict[AssetKey, str] = {}
    for assets_def in assets_defs:
        group_names_by_key.update(assets_def.group_names_by_key)
    for source_asset in source_assets:
        group_names_by_key[source_asset.key] = source_asset.group_name

    all_asset_keys = group_names_by_key.keys()

    asset_keys_by_group_and_name: Dict[Tuple[str, str], List[AssetKey]] = defaultdict(list)

    for key, group in group_names_by_key.items():
        asset_keys_by_group_and_name[(group, key.path[-1])].append(key)

    warned = False

    result: Dict[int, Mapping[AssetKey, AssetKey]] = {}
    for assets_def in assets_defs:
        # If all keys have the same group name, use that
        group_names = set(assets_def.group_names_by_key.values())
        group_name = next(iter(group_names)) if len(group_names) == 1 else None

        resolved_keys_by_unresolved_key: Dict[AssetKey, AssetKey] = {}
        for input_name, upstream_key in assets_def.keys_by_input_name.items():
            group_and_upstream_name = (group_name, upstream_key.path[-1])
            matching_asset_keys = asset_keys_by_group_and_name.get(
                cast(Tuple[str, str], group_and_upstream_name)
            )
            if upstream_key in all_asset_keys:
                pass
            elif (
                group_name is not None
                and len(upstream_key.path) == 1
                and matching_asset_keys
                and len(matching_asset_keys) == 1
                and matching_asset_keys[0] not in assets_def.keys
            ):
                resolved_key = matching_asset_keys[0]
                resolved_keys_by_unresolved_key[upstream_key] = resolved_key

                if not warned:
                    experimental_warning(
                        f"Asset {next(iter(assets_def.keys)).to_string()}'s dependency"
                        f" '{upstream_key.path[-1]}' was resolved to upstream asset"
                        f" {resolved_key.to_string()}, because the name matches and they're in the"
                        " same group. This is experimental functionality that may change in a"
                        " future release"
                    )

                    warned = True
            elif not assets_def.node_def.input_def_named(input_name).dagster_type.is_nothing:
                raise DagsterInvalidDefinitionError(
                    f"Input asset '{upstream_key.to_string()}' for asset "
                    f"'{next(iter(assets_def.keys)).to_string()}' is not "
                    "produced by any of the provided asset ops and is not one of the provided "
                    "sources"
                )

        if resolved_keys_by_unresolved_key:
            result[id(assets_def)] = resolved_keys_by_unresolved_key

    return result
