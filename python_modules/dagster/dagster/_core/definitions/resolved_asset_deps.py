import itertools
from collections import defaultdict
from typing import AbstractSet, Dict, Iterable, List, Mapping, Sequence, Tuple, cast

from dagster import _check as check
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.warnings import experimental_warning


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
        return {
            resolved_keys_by_unresolved_key.get(unresolved_dep.asset_key, unresolved_dep.asset_key)
            for unresolved_dep in assets_def.specs_by_key[asset_key].deps
        }

    def get_resolved_asset_key_for_input(
        self, assets_def: AssetsDefinition, input_name: str
    ) -> AssetKey:
        unresolved_asset_key_for_input = assets_def.node_keys_by_input_name[input_name]
        return self._deps_by_assets_def_id.get(id(assets_def), {}).get(
            unresolved_asset_key_for_input, unresolved_asset_key_for_input
        )


def resolve_similar_asset_names(
    target_asset_key: AssetKey,
    asset_keys: Iterable[AssetKey],
) -> Sequence[AssetKey]:
    """Given a target asset key (an upstream dependency which we can't find), produces a list of
    similar asset keys from the list of asset definitions. We use this list to produce a helpful
    error message that can help users debug their asset dependencies.
    """
    similar_names: List[AssetKey] = []

    target_asset_key_split = ("/".join(target_asset_key.path)).split("/")

    for asset_key in asset_keys:
        *target_asset_key_prefix, target_asset_key_name = target_asset_key.path
        *asset_key_prefix, asset_key_name = asset_key.path

        try:
            from rapidfuzz import fuzz

            is_similar_name = bool(
                fuzz.ratio(asset_key_name, target_asset_key_name, score_cutoff=80)
            )
            is_similar_prefix = bool(
                fuzz.ratio(
                    " ".join(asset_key_prefix),
                    " ".join(target_asset_key_prefix),
                    score_cutoff=80,
                )
            )
        except ImportError:
            from difflib import get_close_matches

            is_similar_name = bool(
                get_close_matches(asset_key_name, [target_asset_key_name], cutoff=0.8)
            )
            is_similar_prefix = bool(
                get_close_matches(
                    " ".join(asset_key_prefix), [" ".join(target_asset_key_prefix)], cutoff=0.8
                )
            )

        # Whether the asset key or upstream key has the same prefix and a similar
        # name
        # e.g. [snowflake, elementl, key] and [snowflake, elementl, ey]
        is_same_prefix_similar_name = (
            asset_key_prefix == target_asset_key_prefix and is_similar_name
        )

        # Whether the asset key or upstream key has a similar prefix and the same
        # name
        # e.g. [snowflake, elementl, key] and [nowflake, elementl, key]
        is_similar_prefix_same_name = asset_key_name == target_asset_key_name and is_similar_prefix

        # Whether the asset key or upstream key has one more prefix component than
        # the other, and the same name
        # e.g. [snowflake, elementl, key] and [snowflake, elementl, prod, key]
        is_off_by_one_prefix_component_same_name = (
            asset_key.path[-1] == target_asset_key.path[-1]
            and len(set(asset_key.path).symmetric_difference(set(target_asset_key.path))) == 1
            and max(len(asset_key.path), len(target_asset_key.path)) > 1
        )

        # If the asset key provided has no prefix and the upstream key has
        # the same name but a prefix of any length
        no_prefix_but_is_match_with_prefix = (
            len(target_asset_key.path) == 1 and asset_key.path[-1] == target_asset_key.path[-1]
        )

        matches_slashes_turned_to_prefix_gaps = asset_key.path == target_asset_key_split

        if (
            is_same_prefix_similar_name
            or is_similar_prefix_same_name
            or is_off_by_one_prefix_component_same_name
            or no_prefix_but_is_match_with_prefix
            or matches_slashes_turned_to_prefix_gaps
        ):
            similar_names.append(asset_key)
    return sorted(similar_names, key=lambda key: key.to_string())


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
        for spec in assets_def.specs:
            group_names_by_key[spec.key] = check.not_none(spec.group_name)
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
        group_names = {spec.group_name for spec in assets_def.specs}
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
                msg = (
                    f"Input asset '{upstream_key.to_string()}' for asset "
                    f"'{next(iter(assets_def.keys)).to_string()}' is not "
                    "produced by any of the provided asset ops and is not one of the provided "
                    "sources."
                )
                similar_names = resolve_similar_asset_names(
                    upstream_key,
                    list(
                        itertools.chain.from_iterable(asset_def.keys for asset_def in assets_defs)
                    ),
                )
                if similar_names:
                    # Arbitrarily limit to 10 similar names to avoid a huge error message
                    subset_similar_names = similar_names[:10]
                    similar_to_string = ", ".join(
                        (similar.to_string() for similar in subset_similar_names)
                    )
                    msg += f" Did you mean one of the following?\n\t{similar_to_string}"
                raise DagsterInvalidDefinitionError(msg)

        if resolved_keys_by_unresolved_key:
            result[id(assets_def)] = resolved_keys_by_unresolved_key

    return result
