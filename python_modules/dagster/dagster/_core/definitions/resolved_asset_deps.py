from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Optional

from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET,
    AssetSpec,
)
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.warnings import beta_warning


def resolve_similar_asset_names(
    target_asset_key: AssetKey,
    asset_keys: Iterable[AssetKey],
) -> Sequence[AssetKey]:
    """Given a target asset key (an upstream dependency which we can't find), produces a list of
    similar asset keys from the list of asset definitions. We use this list to produce a helpful
    error message that can help users debug their asset dependencies.
    """
    similar_names: list[AssetKey] = []

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


def _build_input_error_msg(
    input_name: str, upstream_key: AssetKey, asset_keys: Iterable[AssetKey]
) -> str:
    msg = f'Input asset "{upstream_key.to_string()}" is not produced by any of the provided asset ops and is not one of the provided sources.'
    similar_names = resolve_similar_asset_names(upstream_key, asset_keys)
    if similar_names:
        # Arbitrarily limit to 10 similar names to avoid a huge error message
        subset_similar_names = similar_names[:10]
        similar_to_string = ", ".join(similar.to_string() for similar in subset_similar_names)
        msg += f" Did you mean one of the following?\n\t{similar_to_string}"
    return msg


def resolve_assets_def_deps(assets_defs: list[AssetsDefinition]) -> list[AssetsDefinition]:
    specs = [spec for assets_def in assets_defs for spec in assets_def.specs]
    asset_keys = {spec.key for spec in specs}

    # build mapping from group and name to asset keys
    keys_by_group_and_name: dict[tuple[Optional[str], str], list[AssetKey]] = defaultdict(list)
    for spec in specs:
        if spec.group_name is not None:
            keys_by_group_and_name[(spec.group_name, spec.key.path[-1])].append(spec.key)

    # build mapping from table name to asset keys
    keys_by_table_name: dict[Optional[str], list[AssetKey]] = defaultdict(list)
    for spec in specs:
        table_name = TableMetadataSet.extract(spec.metadata).table_name
        if table_name is not None:
            keys_by_table_name[table_name].append(spec.key)

    # analyze each assets definition for unresolved dependencies and attempt to resolve them
    warned = False
    resolved_assets_defs: list[AssetsDefinition] = []
    for assets_def in assets_defs:
        replacements: dict[AssetKey, AssetKey] = {}
        for spec in assets_def.specs:
            for dep in spec.deps:
                # dep's key already maps to an existing spec
                if dep.asset_key in asset_keys:
                    continue

                input_name = assets_def.input_names_by_node_key.get(dep.asset_key)
                input_def = assets_def.node_def.input_def_named(input_name) if input_name else None
                table_name = TableMetadataSet.extract(dep.metadata).table_name

                # attempt to match by name and group
                matching_asset_keys = keys_by_group_and_name[
                    (spec.group_name, dep.asset_key.path[0])
                ]
                if (
                    # no prefix explicitly provided
                    len(dep.asset_key.path) == 1
                    # unambiguous match
                    and len(matching_asset_keys) == 1
                    # not remapping to self
                    and matching_asset_keys[0] not in assets_def.keys
                ):
                    replacements[dep.asset_key] = matching_asset_keys[0]
                    if not warned:
                        beta_warning(
                            f"Asset {spec.key.to_string()}'s dependency"
                            f" '{input_name or dep.asset_key.to_string()}' was resolved to upstream asset"
                            f" {matching_asset_keys[0].to_string()}, because the name matches and they're in the"
                            " same group. This is a beta functionality that may change in a"
                            " future release"
                        )
                        warned = True
                    continue

                # attempt to match by table name
                matching_asset_keys = keys_by_table_name[table_name]
                if len(matching_asset_keys) > 0:
                    if len(matching_asset_keys) > 1:
                        raise DagsterInvalidDefinitionError(
                            f'Multiple upstream assets found with table name "{table_name}": {matching_asset_keys}. '
                            f"Unable to resolve dependency {dep.asset_key.to_string()} for asset {spec.key.to_string()}."
                        )
                    replacements[dep.asset_key] = matching_asset_keys[0]
                    if not warned:
                        beta_warning(
                            f"Asset {spec.key.to_string()}'s dependency"
                            f" '{input_name or dep.asset_key.to_string()}' was resolved to upstream asset"
                            f" {matching_asset_keys[0].to_string()}, because the table name matches. This is a beta functionality that may change in a"
                            " future release"
                        )
                        warned = True
                    continue

                # could not resolve the dependency, and input requires a real upstream assets def
                if input_name and input_def and not input_def.dagster_type.is_nothing:
                    raise DagsterInvalidDefinitionError(
                        _build_input_error_msg(input_name, dep.asset_key, asset_keys)
                    )

        # only update the object if replacements were necessary
        resolved_assets_defs.append(
            assets_def.with_attributes(asset_key_replacements=replacements)
            if replacements
            else assets_def
        )

    return resolved_assets_defs


def resolve_stub_assets_defs(assets_defs: list[AssetsDefinition]) -> list[AssetsDefinition]:
    defined_keys: set[AssetKey] = set()
    deps_metadata_by_key: dict[AssetKey, list[Mapping[str, Any]]] = defaultdict(list)

    for assets_def in assets_defs:
        for spec in assets_def.specs:
            defined_keys.add(spec.key)
            for dep in spec.deps:
                deps_metadata_by_key[dep.asset_key].append(dep.metadata)
        # treat the asset keys defined for asset checks as AssetDeps with no metadata
        for check_spec in assets_def.check_specs:
            deps_metadata_by_key[check_spec.asset_key].append({})

    stub_assets_defs: list[AssetsDefinition] = []

    # iterate through the set of keys that are a dependency but have no definition
    for key in deps_metadata_by_key.keys() - defined_keys:
        # combine metadata from all dependencies and error if there are conflicts
        metadata = {}
        for dep_metadata in deps_metadata_by_key[key]:
            if not dep_metadata:
                continue

            # metadata set, but conflicts
            if metadata and dep_metadata != metadata:
                raise DagsterInvalidDefinitionError(
                    f"Conflicting metadata found on AssetDeps referencing {key.to_string()}: {metadata} != {dep_metadata}. "
                    "All metadata for AssetDeps referencing a given key must be identical or empty."
                )
            metadata = dict(dep_metadata)

        # add in flag to indicate that this is a stub asset
        metadata[SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET] = True
        stub_assets_defs.append(AssetsDefinition(specs=[AssetSpec(key=key, metadata=metadata)]))

    return stub_assets_defs
