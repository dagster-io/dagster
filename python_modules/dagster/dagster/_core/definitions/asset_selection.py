import operator
from abc import ABC
from functools import reduce
from typing import AbstractSet, FrozenSet, Optional, Sequence, Union

import dagster._check as check
from dagster._annotations import public
from dagster._core.errors import DagsterInvalidSubsetError
from dagster._core.selector.subset_selector import (
    fetch_connected,
    fetch_sinks,
    generate_asset_dep_graph,
    generate_asset_name_to_definition_map,
)

from .assets import AssetsDefinition
from .events import AssetKey, CoercibleToAssetKey
from .source_asset import SourceAsset


class AssetSelection(ABC):
    """
    An AssetSelection defines a query over a set of assets, normally all the assets in a repository.

    You can use the "|", "&", and "-" operators to create unions, intersections, and differences of
    asset selections, respectively.

    AssetSelections are typically used with :py:func:`define_asset_job`.

    Examples:

        .. code-block:: python

            # Select all assets in group "marketing":
            AssetSelection.groups("marketing")

            # Select all assets in group "marketing", as well as the asset with key "promotion":
            AssetSelection.groups("marketing") | AssetSelection.keys("promotion")

            # Select all assets in group "marketing" that are downstream of asset "leads":
            AssetSelection.groups("marketing") & AssetSelection.keys("leads").downstream()

            # Select all assets except for those in group "marketing"
            AssetSelection.all() - AssetSelection.groups("marketing")
    """

    @public  # type: ignore
    @staticmethod
    def all() -> "AllAssetSelection":
        """Returns a selection that includes all assets."""
        return AllAssetSelection()

    @public  # type: ignore
    @staticmethod
    def assets(*assets_defs: AssetsDefinition) -> "KeysAssetSelection":
        """Returns a selection that includes all of the provided assets."""
        return KeysAssetSelection(*(key for assets_def in assets_defs for key in assets_def.keys))

    @public  # type: ignore
    @staticmethod
    def keys(*asset_keys: CoercibleToAssetKey) -> "KeysAssetSelection":
        """Returns a selection that includes assets with any of the provided keys."""
        _asset_keys = [AssetKey.from_coerceable(key) for key in asset_keys]
        return KeysAssetSelection(*_asset_keys)

    @public  # type: ignore
    @staticmethod
    def groups(*group_strs) -> "GroupsAssetSelection":
        """Returns a selection that includes assets that belong to any of the provided groups"""
        check.tuple_param(group_strs, "group_strs", of_type=str)
        return GroupsAssetSelection(*group_strs)

    @public  # type: ignore
    def downstream(
        self, depth: Optional[int] = None, include_self: bool = True
    ) -> "DownstreamAssetSelection":
        """
        Returns a selection that includes all assets that are downstream of any of the assets in
        this selection, selecting the assets in this selection by default. Iterates through each
        asset in this selection and returns the union of all downstream assets.

        depth (Optional[int]): If provided, then only include assets to the given depth. A depth
            of 2 means all assets that are children or grandchildren of the assets in this
            selection.
        include_self (bool): If True, then include the assets in this selection in the result.
            If the include_self flag is False, return each downstream asset that is not part of the
            original selection. By default, set to True.
        """
        check.opt_int_param(depth, "depth")
        check.opt_bool_param(include_self, "include_self")
        return DownstreamAssetSelection(self, depth=depth, include_self=include_self)

    @public  # type: ignore
    def upstream(
        self, depth: Optional[int] = None, include_self: bool = True
    ) -> "UpstreamAssetSelection":
        """
        Returns a selection that includes all assets that are upstream of any of the assets in
        this selection, selecting the assets in this selection by default. Iterates through each
        asset in this selection and returns the union of all downstream assets.

        Args:
            depth (Optional[int]): If provided, then only include assets to the given depth. A depth
                of 2 means all assets that are parents or grandparents of the assets in this
                selection.
            include_self (bool): If True, then include the assets in this selection in the result.
                If the include_self flag is False, return each upstream asset that is not part of the
                original selection. By default, set to True.
        """
        check.opt_int_param(depth, "depth")
        check.opt_bool_param(include_self, "include_self")
        return UpstreamAssetSelection(self, depth=depth, include_self=include_self)

    @public  # type: ignore
    def sinks(self) -> "SinkAssetSelection":
        """
        Given an asset selection, returns a new asset selection that contains all of the sink
        assets within the original asset selection.

        A sink asset is an asset that has no downstream dependencies within the asset selection.
        The sink asset can have downstream dependencies outside of the asset selection."""
        return SinkAssetSelection(self)

    def __or__(self, other: "AssetSelection") -> "OrAssetSelection":
        check.inst_param(other, "other", AssetSelection)
        return OrAssetSelection(self, other)

    def __and__(self, other: "AssetSelection") -> "AndAssetSelection":
        check.inst_param(other, "other", AssetSelection)
        return AndAssetSelection(self, other)

    def __sub__(self, other: "AssetSelection") -> "SubAssetSelection":
        check.inst_param(other, "other", AssetSelection)
        return SubAssetSelection(self, other)

    def resolve(
        self, all_assets: Sequence[Union[AssetsDefinition, SourceAsset]]
    ) -> FrozenSet[AssetKey]:
        check.sequence_param(all_assets, "all_assets", (AssetsDefinition, SourceAsset))
        return Resolver(all_assets).resolve(self)


class AllAssetSelection(AssetSelection):
    pass


class AndAssetSelection(AssetSelection):
    def __init__(self, child_1: AssetSelection, child_2: AssetSelection):
        self.children = (child_1, child_2)


class SubAssetSelection(AssetSelection):
    def __init__(self, child_1: AssetSelection, child_2: AssetSelection):
        self.children = (child_1, child_2)


class SinkAssetSelection(AssetSelection):
    def __init__(
        self,
        child: AssetSelection,
    ):
        self.children = (child,)


class DownstreamAssetSelection(AssetSelection):
    def __init__(
        self,
        child: AssetSelection,
        *,
        depth: Optional[int] = None,
        include_self: Optional[bool] = True,
    ):
        self.children = (child,)
        self.depth = depth
        self.include_self = include_self


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
    def __init__(
        self,
        child: AssetSelection,
        *,
        depth: Optional[int] = None,
        include_self: Optional[bool] = True,
    ):
        self.children = (child,)
        self.depth = depth
        self.include_self = include_self


# ########################
# ##### RESOLUTION
# ########################


class Resolver:
    def __init__(self, all_assets: Sequence[Union[AssetsDefinition, SourceAsset]]):
        assets_defs = []
        source_assets = []
        for asset in all_assets:
            if isinstance(asset, SourceAsset):
                source_assets.append(asset)
            elif isinstance(asset, AssetsDefinition):
                assets_defs.append(asset)
            else:
                check.failed(f"Expected SourceAsset or AssetsDefinition, got {type(asset)}")

        self.assets_defs = assets_defs
        self.asset_dep_graph = generate_asset_dep_graph(assets_defs, source_assets)
        self.all_assets_by_key_str = generate_asset_name_to_definition_map(assets_defs)
        self.source_asset_key_strs = {
            source_asset.key.to_user_string() for source_asset in source_assets
        }

    def resolve(self, root_node: AssetSelection) -> FrozenSet[AssetKey]:
        return frozenset(
            {AssetKey.from_user_string(asset_name) for asset_name in self._resolve(root_node)}
        )

    def _resolve(self, node: AssetSelection) -> AbstractSet[str]:
        if isinstance(node, AllAssetSelection):
            return set(self.all_assets_by_key_str.keys())
        elif isinstance(node, AndAssetSelection):
            child_1, child_2 = [self._resolve(child) for child in node.children]
            return child_1 & child_2
        elif isinstance(node, SubAssetSelection):
            child_1, child_2 = [self._resolve(child) for child in node.children]
            return child_1 - child_2
        elif isinstance(node, SinkAssetSelection):
            selection = self._resolve(node.children[0])
            return fetch_sinks(self.asset_dep_graph, selection)
        elif isinstance(node, DownstreamAssetSelection):
            selection = self._resolve(node.children[0])
            return operator.sub(
                reduce(
                    operator.or_,
                    [
                        {asset_name}
                        | fetch_connected(
                            item=asset_name,
                            graph=self.asset_dep_graph,
                            direction="downstream",
                            depth=node.depth,
                        )
                        for asset_name in selection
                    ],
                ),
                selection if not node.include_self else set(),
            )
        elif isinstance(node, GroupsAssetSelection):
            return reduce(
                operator.or_,
                [_match_groups(assets_def, set(node.children)) for assets_def in self.assets_defs],
            )
        elif isinstance(node, KeysAssetSelection):
            specified_key_strs = set([child.to_user_string() for child in node.children])
            invalid_key_strs = specified_key_strs - set(self.all_assets_by_key_str.keys())
            selected_source_asset_key_strs = specified_key_strs & self.source_asset_key_strs
            if selected_source_asset_key_strs:
                raise DagsterInvalidSubsetError(
                    f"AssetKey(s) {selected_source_asset_key_strs} were selected, but these keys are "
                    "supplied by SourceAsset objects, not AssetsDefinition objects. You don't need "
                    "to include source assets in a selection for downstream assets to be able to "
                    "read them."
                )
            if invalid_key_strs:
                raise DagsterInvalidSubsetError(
                    f"AssetKey(s) {invalid_key_strs} were selected, but no AssetsDefinition objects supply "
                    "these keys. Make sure all keys are spelled correctly, and all AssetsDefinitions "
                    "are correctly added to the repository."
                )
            return specified_key_strs
        elif isinstance(node, OrAssetSelection):
            child_1, child_2 = [self._resolve(child) for child in node.children]
            return child_1 | child_2
        elif isinstance(node, UpstreamAssetSelection):
            selection = self._resolve(node.children[0])
            return operator.sub(
                reduce(
                    operator.or_,
                    [
                        {asset_name}
                        | fetch_connected(
                            item=asset_name,
                            graph=self.asset_dep_graph,
                            direction="upstream",
                            depth=node.depth,
                        )
                        for asset_name in selection
                    ],
                ),
                selection if not node.include_self else set(),
            )
        else:
            check.failed(f"Unknown node type: {type(node)}")


def _match_groups(assets_def: AssetsDefinition, groups: AbstractSet[str]) -> AbstractSet[str]:
    return {
        asset_key.to_user_string()
        for asset_key, group in assets_def.group_names_by_key.items()
        if group in groups
    }
