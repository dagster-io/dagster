from abc import ABC, abstractmethod
from functools import reduce
from typing import AbstractSet, Dict, Literal, MutableSet, Optional, Pattern, TypeVar

from typing_extensions import TypeAlias

import dagster._check as check
from dagster.core.asset_defs.assets import AssetsDefinition

T = TypeVar("T")
AssetSet: TypeAlias = AbstractSet[AssetsDefinition]  # makes sigs more readable


class AssetSelection(ABC):
    @staticmethod
    def keys(*patterns: str) -> "KeysAssetSelection":
        return KeysAssetSelection(*patterns)

    @staticmethod
    def groups(*groups) -> "GroupsAssetSelection":
        return GroupsAssetSelection(*groups)

    def downstream(self, depth: Optional[int] = None) -> "DownstreamAssetSelection":
        return DownstreamAssetSelection(self, depth=depth)

    def upstream(self, depth: Optional[int] = None) -> "UpstreamAssetSelection":
        return UpstreamAssetSelection(self, depth=depth)

    def __or__(self, other: "AssetSelection") -> "OrAssetSelection":
        return OrAssetSelection(self, other)

    def __and__(self, other: "AssetSelection") -> "AndAssetSelection":
        return AndAssetSelection(self, other)

    # def to_job(self, assets: AssetSet, *args):
    #     selected_assets = self.resolve(assets)
    #     return OwensFrankenJob(selected_assets, *args)

    @abstractmethod
    def resolve(self, all_assets: AssetSet) -> AssetSet:
        ...


class AndAssetSelection(AssetSelection):
    def __init__(self, child_1: AssetSelection, child_2: AssetSelection):
        self.children = (child_1, child_2)

    def resolve(self, all_assets: AssetSet) -> AssetSet:
        child_1, child_2 = [child.resolve(all_assets) for child in self.children]
        return child_1 & child_2


class DownstreamAssetSelection(AssetSelection):
    def __init__(self, child: AssetSelection, *, depth: Optional[int] = None):
        self.children = (child,)
        self.depth = depth

    def resolve(self, all_assets: AssetSet) -> AssetSet:
        child = self.children[0].resolve(all_assets)
        return reduce(
            lambda acc, asset: acc
            | _gather_downstream_assets(asset, all_assets, max_depth=self.depth),
            child,
            set(),
        )


class GroupsAssetSelection(AssetSelection):
    def __init__(self, *children: str):
        self.children = children

    def resolve(self, all_assets: AssetSet) -> AssetSet:
        return {a for a in all_assets if any(_match_group(a, pattern) for pattern in self.children)}


class KeysAssetSelection(AssetSelection):
    def __init__(self, *children: str):
        self.children = children

    def resolve(self, all_assets: AssetSet) -> AssetSet:
        return {a for a in all_assets if any(_match_key(a, key) for key in self.children)}


class OrAssetSelection(AssetSelection):
    def __init__(self, child_1: AssetSelection, child_2: AssetSelection):
        self.children = (child_1, child_2)

    def resolve(self, all_assets: AssetSet) -> AssetSet:
        child_1, child_2 = [child.resolve(all_assets) for child in self.children]
        return child_1 | child_2


class UpstreamAssetSelection(AssetSelection):
    def __init__(self, child: AssetSelection, *, depth: Optional[int] = None):
        self.children = (child,)
        self.depth = depth

    def resolve(self, all_assets: AssetSet) -> AssetSet:
        child = self.children[0].resolve(all_assets)
        return reduce(
            lambda acc, asset: acc
            | _gather_upstream_assets(asset, all_assets, max_depth=self.depth),
            child,
            set(),
        )


# ########################
# ##### UTILITY
# ########################


def _gather_downstream_assets(
    asset: AssetsDefinition, all_assets: AssetSet, *, max_depth: Optional[int] = None
) -> AssetSet:
    return frozenset(
        _gather_connected_assets_rec(
            asset,
            all_assets,
            set(),
            direction="downstream",
            depth=max_depth,
        )
    )


def _gather_upstream_assets(
    asset: AssetsDefinition, all_assets: AssetSet, *, max_depth: Optional[int] = None
) -> AssetSet:
    return frozenset(
        _gather_connected_assets_rec(
            asset, all_assets, set(), direction="upstream", depth=max_depth
        )
    )


_Direction = Literal["upstream", "downstream"]


def _gather_connected_assets_rec(
    asset: AssetsDefinition,
    all_assets: AssetSet,
    asset_set: MutableSet[AssetsDefinition],
    *,
    direction: _Direction,
    depth: Optional[int] = None,
) -> MutableSet[AssetsDefinition]:
    asset_set.add(asset)
    directly_connected_assets = _get_directly_connected_assets(asset, all_assets, direction)
    if depth is None or depth > 0:
        pass_depth = depth if depth is None else depth - 1
        asset_set = reduce(
            lambda acc, asset: _gather_connected_assets_rec(
                asset, all_assets, acc, direction=direction, depth=pass_depth
            ),
            directly_connected_assets,
            asset_set,
        )
    return asset_set


def _get_directly_connected_assets(
    asset: AssetsDefinition, all_assets: AssetSet, direction: _Direction
) -> AssetSet:
    if direction == "downstream":
        return {a for a in all_assets if _has_dependency(a, asset)}
    elif direction == "upstream":
        return {a for a in all_assets if _has_dependency(asset, a)}
    else:
        check.failed("Unknown direction: {direction}".format(direction=direction))


def _has_dependency(asset_1: AssetsDefinition, asset_2: AssetsDefinition) -> bool:
    asset_1_deps = asset_1.dependency_asset_keys
    return any(k in asset_1_deps for k in asset_2.asset_keys)


def _match_key(asset: AssetsDefinition, key_str: str) -> bool:
    return any(key_str == key.to_user_string() for key in asset.asset_keys)


def _match_group(asset: AssetsDefinition, group_str: str) -> bool:
    return any(group_str == group_name for group_name in asset.group_names.values())
