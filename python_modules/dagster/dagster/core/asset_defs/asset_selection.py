import operator
from abc import ABC
from functools import reduce
from typing import AbstractSet, FrozenSet, Optional

from typing_extensions import TypeAlias

import dagster._check as check
from dagster.core.asset_defs.assets import AssetsDefinition
from dagster.core.selector.subset_selector import (
    Direction,
    fetch_connected_assets_definitions,
    generate_asset_dep_graph,
    generate_asset_name_to_definition_map,
    parse_clause,
)

AssetSet: TypeAlias = AbstractSet[AssetsDefinition]  # makes sigs more readable


class AssetSelection(ABC):
    @staticmethod
    def all() -> "AllAssetSelection":
        return AllAssetSelection()

    @staticmethod
    def keys(*key_strs: str) -> "KeysAssetSelection":
        return KeysAssetSelection(*key_strs)

    @staticmethod
    def groups(*group_strs) -> "GroupsAssetSelection":
        return GroupsAssetSelection(*group_strs)

    def downstream(self, depth: Optional[int] = None) -> "DownstreamAssetSelection":
        return DownstreamAssetSelection(self, depth=depth)

    def upstream(self, depth: Optional[int] = None) -> "UpstreamAssetSelection":
        return UpstreamAssetSelection(self, depth=depth)

    def __or__(self, other: "AssetSelection") -> "OrAssetSelection":
        return OrAssetSelection(self, other)

    def __and__(self, other: "AssetSelection") -> "AndAssetSelection":
        return AndAssetSelection(self, other)

    def resolve(self, all_assets: AssetSet) -> AssetSet:
        return Resolver(all_assets).resolve(self)


class AllAssetSelection(AssetSelection):
    pass


class AndAssetSelection(AssetSelection):
    def __init__(self, child_1: AssetSelection, child_2: AssetSelection):
        self.children = (child_1, child_2)


class DownstreamAssetSelection(AssetSelection):
    def __init__(self, child: AssetSelection, *, depth: Optional[int] = None):
        self.children = (child,)
        self.depth = depth


class GroupsAssetSelection(AssetSelection):
    def __init__(self, *children: str):
        self.children = children


class KeysAssetSelection(AssetSelection):
    def __init__(self, *children: str):
        self.children = children


class OrAssetSelection(AssetSelection):
    def __init__(self, child_1: AssetSelection, child_2: AssetSelection):
        self.children = (child_1, child_2)


class UpstreamAssetSelection(AssetSelection):
    def __init__(self, child: AssetSelection, *, depth: Optional[int] = None):
        self.children = (child,)
        self.depth = depth


class UpstreamAssetSelection(AssetSelection):
    def __init__(self, child: AssetSelection, *, depth: Optional[int] = None):
        self.children = (child,)
        self.depth = depth


# ########################
# ##### RESOLUTION
# ########################


class Resolver:
    def __init__(self, all_assets: AssetSet):
        self.all_assets = all_assets
        self.asset_dep_graph = generate_asset_dep_graph(list(all_assets))
        self.all_assets_by_name = generate_asset_name_to_definition_map(all_assets)

    def resolve(self, node: AssetSelection) -> Set[str]:
        if isinstance(node, AllAssetSelection):
            return self.all_assets_by_name.keys()
        elif isinstance(node, AndAssetSelection):
            child_1, child_2 = [self.resolve(child) for child in node.children]
            return child_1 & child_2
        elif isinstance(node, DownstreamAssetSelection):
            child = self.resolve(node.children[0])
            return reduce(
                operator.or_,
                [self._gather_connected_assets(asset, "downstream", node.depth) for asset in child],
            )
        elif isinstance(node, GroupsAssetSelection):
            return {
                key for key in
            }
            return reduce(
                operator.or_,
                [

                ]
            )

            return {
                a
                for a in self.all_assets
                if any(_match_group(a, pattern) for pattern in node.children)
            }
        elif isinstance(node, KeysAssetSelection):
            return node.children
        elif isinstance(node, OrAssetSelection):
            child_1, child_2 = [self.resolve(child) for child in node.children]
            return child_1 | child_2
        elif isinstance(node, UpstreamAssetSelection):
            child = self.resolve(node.children[0])
            return reduce(
                operator.or_,
                [self._gather_connected_assets(asset, "upstream", node.depth) for asset in child],
            )
        else:
            check.failed(f"Unknown node type: {type(node)}")

    def _gather_connected_assets(
        self, asset: AssetsDefinition, direction: Direction, depth: Optional[int]
    ) -> FrozenSet[AssetsDefinition]:
        connected = fetch_connected_assets_definitions(
            asset, self.asset_dep_graph, self.all_assets_by_name, direction=direction, depth=depth
        )
        return connected | {asset}


def _match_key(asset: AssetsDefinition, key_str: str) -> bool:
    return any(key_str == key.to_user_string() for key in asset.asset_keys)


def _match_group(asset: AssetsDefinition, group_str: str) -> bool:
    return any(group_str == group_name for group_name in asset.group_names.values())
