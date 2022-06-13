import operator
from abc import ABC
from functools import reduce
from typing import AbstractSet, FrozenSet, Optional, Sequence

import dagster._check as check
from dagster.core.asset_defs.assets import AssetsDefinition
from dagster.core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster.core.selector.subset_selector import (
    fetch_connected,
    generate_asset_dep_graph,
    generate_asset_name_to_definition_map,
)


class AssetSelection(ABC):
    @staticmethod
    def all() -> "AllAssetSelection":
        return AllAssetSelection()

    @staticmethod
    def assets(*assets_defs: AssetsDefinition) -> "KeysAssetSelection":
        return KeysAssetSelection(*(key for assets_def in assets_defs for key in assets_def.keys))

    @staticmethod
    def keys(*asset_keys: CoercibleToAssetKey) -> "KeysAssetSelection":
        _asset_keys = [AssetKey.from_coerceable(key) for key in asset_keys]
        return KeysAssetSelection(*_asset_keys)

    @staticmethod
    def groups(*group_strs) -> "GroupsAssetSelection":
        check.tuple_param(group_strs, "group_strs", of_type=str)
        return GroupsAssetSelection(*group_strs)

    def downstream(self, depth: Optional[int] = None) -> "DownstreamAssetSelection":
        check.opt_int_param(depth, "depth")
        return DownstreamAssetSelection(self, depth=depth)

    def upstream(self, depth: Optional[int] = None) -> "UpstreamAssetSelection":
        check.opt_int_param(depth, "depth")
        return UpstreamAssetSelection(self, depth=depth)

    def __or__(self, other: "AssetSelection") -> "OrAssetSelection":
        check.inst_param(other, "other", AssetSelection)
        return OrAssetSelection(self, other)

    def __and__(self, other: "AssetSelection") -> "AndAssetSelection":
        check.inst_param(other, "other", AssetSelection)
        return AndAssetSelection(self, other)

    def resolve(self, all_assets: Sequence[AssetsDefinition]) -> FrozenSet[AssetKey]:
        check.sequence_param(all_assets, "all_assets", AssetsDefinition)
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
    def __init__(self, *children: AssetKey):
        self.children = children


class OrAssetSelection(AssetSelection):
    def __init__(self, child_1: AssetSelection, child_2: AssetSelection):
        self.children = (child_1, child_2)


class UpstreamAssetSelection(AssetSelection):
    def __init__(self, child: AssetSelection, *, depth: Optional[int] = None):
        self.children = (child,)
        self.depth = depth


# ########################
# ##### RESOLUTION
# ########################


class Resolver:
    def __init__(self, all_assets: Sequence[AssetsDefinition]):
        self.all_assets = all_assets
        self.asset_dep_graph = generate_asset_dep_graph(list(all_assets))
        self.all_assets_by_name = generate_asset_name_to_definition_map(all_assets)

    def resolve(self, root_node: AssetSelection) -> FrozenSet[AssetKey]:
        return frozenset(
            {AssetKey.from_user_string(asset_name) for asset_name in self._resolve(root_node)}
        )

    def _resolve(self, node: AssetSelection) -> AbstractSet[str]:
        if isinstance(node, AllAssetSelection):
            return set(self.all_assets_by_name.keys())
        elif isinstance(node, AndAssetSelection):
            child_1, child_2 = [self._resolve(child) for child in node.children]
            return child_1 & child_2
        elif isinstance(node, DownstreamAssetSelection):
            child = self._resolve(node.children[0])
            return reduce(
                operator.or_,
                [
                    {asset_name}
                    | fetch_connected(
                        item=asset_name,
                        graph=self.asset_dep_graph,
                        direction="downstream",
                        depth=node.depth,
                    )
                    for asset_name in child
                ],
            )
        elif isinstance(node, GroupsAssetSelection):
            return reduce(
                operator.or_,
                [_match_groups(assets_def, set(node.children)) for assets_def in self.all_assets],
            )
        elif isinstance(node, KeysAssetSelection):
            return set([child.to_user_string() for child in node.children])
        elif isinstance(node, OrAssetSelection):
            child_1, child_2 = [self._resolve(child) for child in node.children]
            return child_1 | child_2
        elif isinstance(node, UpstreamAssetSelection):
            child = self._resolve(node.children[0])
            return reduce(
                operator.or_,
                [
                    {asset_name}
                    | fetch_connected(
                        item=asset_name,
                        graph=self.asset_dep_graph,
                        direction="upstream",
                        depth=node.depth,
                    )
                    for asset_name in child
                ],
            )
        else:
            check.failed(f"Unknown node type: {type(node)}")


def _match_groups(assets_def: AssetsDefinition, groups: AbstractSet[str]) -> AbstractSet[str]:
    return {
        asset_key.to_user_string()
        for asset_key, group in assets_def.group_names.items()
        if group in groups
    }
