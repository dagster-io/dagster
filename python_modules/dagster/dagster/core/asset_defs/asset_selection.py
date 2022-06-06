import re
from abc import ABC, abstractmethod
from functools import reduce
from typing import AbstractSet, Dict, MutableSet, Pattern, Set, TypeVar

from typing_extensions import TypeAlias

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

    def downstream(self) -> "DownstreamAssetSelection":
        return DownstreamAssetSelection(self)

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
    def __init__(self, child: AssetSelection):
        self.children = (child,)

    # TODO
    def resolve(self, all_assets: AssetSet) -> AssetSet:
        child = self.children[0].resolve(all_assets)
        return reduce(
            lambda acc, asset: acc | _gather_downstream_assets(asset, all_assets), child, set()
        )


class GroupsAssetSelection(AssetSelection):
    def __init__(self, *children: str):
        self.children = children

    def resolve(self, all_assets: AssetSet) -> AssetSet:
        return {
            a
            for a in all_assets
            if any(_match_group_pattern(a, pattern) for pattern in self.children)
        }


class KeysAssetSelection(AssetSelection):
    def __init__(self, *children: str):
        self.children = children

    def resolve(self, all_assets: AssetSet) -> AssetSet:
        return {
            a
            for a in all_assets
            if any(_match_key_pattern(a, pattern) for pattern in self.children)
        }


class OrAssetSelection(AssetSelection):
    def __init__(self, child_1: AssetSelection, child_2: AssetSelection):
        self.children = (child_1, child_2)

    def resolve(self, all_assets: AssetSet) -> AssetSet:
        child_1, child_2 = [child.resolve(all_assets) for child in self.children]
        return child_1 | child_2


# ########################
# ##### UTILITY
# ########################


def _gather_downstream_assets(asset: AssetsDefinition, all_assets: AssetSet) -> AssetSet:
    return frozenset(_gather_downstream_assets_rec(asset, all_assets, set()))


def _gather_downstream_assets_rec(
    asset: AssetsDefinition, all_assets: AssetSet, asset_set: MutableSet[AssetsDefinition]
) -> MutableSet[AssetsDefinition]:
    asset_set.add(asset)
    direct_downstream_assets = {a for a in all_assets if _has_dependency(a, asset)}
    return reduce(
        lambda acc, asset: _gather_downstream_assets_rec(asset, all_assets, acc),
        direct_downstream_assets,
        asset_set,
    )


def _has_dependency(asset_1: AssetsDefinition, asset_2: AssetsDefinition) -> bool:
    asset_1_deps = asset_1.dependency_asset_keys
    return any(k in asset_1_deps for k in asset_2.asset_keys)


def _match_key_pattern(asset: AssetsDefinition, pattern: str) -> bool:
    regex = _pattern_to_regex(pattern)
    return any(regex.match(key.to_user_string()) for key in asset.asset_keys)


def _match_group_pattern(asset: AssetsDefinition, pattern: str) -> bool:
    regex = _pattern_to_regex(pattern)
    return any(regex.match(group_name) for group_name in asset.group_names.values())


_pattern_cache: Dict[str, Pattern[str]] = {}


def _pattern_to_regex(pattern: str) -> Pattern[str]:
    if pattern not in _pattern_cache:
        regex = re.compile(f'^{pattern.replace("*", ".*")}$')
        _pattern_cache[pattern] = regex
    return _pattern_cache[pattern]
