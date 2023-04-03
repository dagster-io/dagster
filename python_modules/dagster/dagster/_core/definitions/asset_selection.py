import operator
from abc import ABC, abstractmethod
from functools import reduce
from typing import AbstractSet, Iterable, Optional, Sequence, Union, cast

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import deprecated, public
from dagster._core.errors import DagsterInvalidSubsetError
from dagster._core.selector.subset_selector import (
    fetch_connected,
    fetch_sinks,
    fetch_sources,
    parse_clause,
)
from dagster._utils.backcompat import deprecation_warning

from .asset_graph import AssetGraph
from .assets import AssetsDefinition
from .events import AssetKey, CoercibleToAssetKey
from .source_asset import SourceAsset

CoercibleToAssetSelection: TypeAlias = Union[
    str,
    Sequence[str],
    Sequence[AssetKey],
    Sequence[Union["AssetsDefinition", "SourceAsset"]],
    "AssetSelection",
]


class AssetSelection(ABC):
    """An AssetSelection defines a query over a set of assets, normally all the assets in a code location.

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

            # Select all assets in a list of assets:
            AssetSelection.assets(*my_assets_list)

            # Select all assets except for those in group "marketing"
            AssetSelection.all() - AssetSelection.groups("marketing")

            # Select all assets which are materialized by the same op as "projections":
            AssetSelection.keys("projections").required_multi_asset_neighbors()
    """

    @public
    @staticmethod
    def all() -> "AllAssetSelection":
        """Returns a selection that includes all assets."""
        return AllAssetSelection()

    @public
    @staticmethod
    def assets(*assets_defs: AssetsDefinition) -> "KeysAssetSelection":
        """Returns a selection that includes all of the provided assets."""
        return KeysAssetSelection(*(key for assets_def in assets_defs for key in assets_def.keys))

    @public
    @staticmethod
    def keys(*asset_keys: CoercibleToAssetKey) -> "KeysAssetSelection":
        """Returns a selection that includes assets with any of the provided keys.

        Examples:
            .. code-block:: python

                AssetSelection.keys(AssetKey(["a"]))

                AssetSelection.keys("a")

                AssetSelection.keys(AssetKey(["a"]), AssetKey(["b"]))

                AssetSelection.keys("a", "b")

                asset_key_list = [AssetKey(["a"]), AssetKey(["b"])]
                AssetSelection.keys(*asset_key_list)
        """
        _asset_keys = [
            AssetKey.from_user_string(key)
            if isinstance(key, str)
            else AssetKey.from_coerceable(key)
            for key in asset_keys
        ]
        return KeysAssetSelection(*_asset_keys)

    @public
    @staticmethod
    def groups(*group_strs) -> "GroupsAssetSelection":
        """Returns a selection that includes assets that belong to any of the provided groups."""
        check.tuple_param(group_strs, "group_strs", of_type=str)
        return GroupsAssetSelection(*group_strs)

    @public
    def downstream(
        self, depth: Optional[int] = None, include_self: bool = True
    ) -> "DownstreamAssetSelection":
        """Returns a selection that includes all assets that are downstream of any of the assets in
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

    @public
    def upstream(
        self, depth: Optional[int] = None, include_self: bool = True
    ) -> "UpstreamAssetSelection":
        """Returns a selection that includes all assets that are upstream of any of the assets in
        this selection, selecting the assets in this selection by default. Iterates through each
        asset in this selection and returns the union of all upstream assets.

        Because mixed selections of source and regular assets are currently not supported, keys
        corresponding to `SourceAssets` will not be included as upstream of regular assets.

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

    @public
    def sinks(self) -> "SinkAssetSelection":
        """Given an asset selection, returns a new asset selection that contains all of the sink
        assets within the original asset selection.

        A sink asset is an asset that has no downstream dependencies within the asset selection.
        The sink asset can have downstream dependencies outside of the asset selection.
        """
        return SinkAssetSelection(self)

    @public
    def required_multi_asset_neighbors(self) -> "RequiredNeighborsAssetSelection":
        """Given an asset selection in which some assets are output from a mutli-asset compute op
        which cannot be subset, returns a new asset selection that contains all of the assets
        required to execute the original asset selection.
        """
        return RequiredNeighborsAssetSelection(self)

    @public
    def roots(self) -> "RootAssetSelection":
        """Given an asset selection, returns a new asset selection that contains all of the root
        assets within the original asset selection.

        A root asset is an asset that has no upstream dependencies within the asset selection.
        The root asset can have downstream dependencies outside of the asset selection.
        """
        return RootAssetSelection(self)

    @public
    @deprecated
    def sources(self) -> "RootAssetSelection":
        """Given an asset selection, returns a new asset selection that contains all of the root
        assets within the original asset selection.

        A root asset is an asset that has no upstream dependencies within the asset selection.
        The root asset can have downstream dependencies outside of the asset selection.
        """
        deprecation_warning(
            "AssetSelection.sources",
            "2.0",
            "Use AssetSelection.roots instead.",
        )
        return self.roots()

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
        self, all_assets: Union[Iterable[Union[AssetsDefinition, SourceAsset]], AssetGraph]
    ) -> AbstractSet[AssetKey]:
        if isinstance(all_assets, AssetGraph):
            asset_graph = all_assets
        else:
            check.iterable_param(all_assets, "all_assets", (AssetsDefinition, SourceAsset))
            asset_graph = AssetGraph.from_assets(all_assets)

        resolved = self.resolve_inner(asset_graph)
        resolved_source_assets = asset_graph.source_asset_keys & resolved
        resolved_regular_assets = resolved - asset_graph.source_asset_keys
        check.invariant(
            not (len(resolved_source_assets) > 0 and len(resolved_regular_assets) > 0),
            (
                "Asset selection specified both regular assets and source assets. This is not"
                " currently supported. Selections must be all regular assets or all source assets."
            ),
        )
        return resolved

    @abstractmethod
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        raise NotImplementedError()

    @staticmethod
    def _selection_from_string(string: str) -> "AssetSelection":
        from dagster._core.definitions import AssetSelection

        if string == "*":
            return AssetSelection.all()

        parts = parse_clause(string)
        if not parts:
            check.failed(f"Invalid selection string: {string}")
        u, item, d = parts

        selection: AssetSelection = AssetSelection.keys(item)
        if u:
            selection = selection.upstream(u)
        if d:
            selection = selection.downstream(d)
        return selection

    @classmethod
    def from_coercible(cls, selection: CoercibleToAssetSelection) -> "AssetSelection":
        if isinstance(selection, str):
            return cls._selection_from_string(selection)
        elif isinstance(selection, AssetSelection):
            return selection
        elif isinstance(selection, list) and all(isinstance(el, str) for el in selection):
            return reduce(
                operator.or_, [cls._selection_from_string(cast(str, s)) for s in selection]
            )
        elif isinstance(selection, list) and all(
            isinstance(el, (AssetsDefinition, SourceAsset)) for el in selection
        ):
            return AssetSelection.keys(
                *(
                    key
                    for el in selection
                    for key in (
                        el.keys if isinstance(el, AssetsDefinition) else [cast(SourceAsset, el).key]
                    )
                )
            )
        elif isinstance(selection, list) and all(isinstance(el, AssetKey) for el in selection):
            return cls.keys(*cast(Sequence[AssetKey], selection))
        else:
            check.failed(
                "selection argument must be one of str, Sequence[str], Sequence[AssetKey],"
                " Sequence[AssetsDefinition], Sequence[SourceAsset], AssetSelection. Was"
                f" {type(selection)}."
            )


class AllAssetSelection(AssetSelection):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        return asset_graph.all_asset_keys


class AndAssetSelection(AssetSelection):
    def __init__(self, left: AssetSelection, right: AssetSelection):
        self._left = left
        self._right = right

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        return self._left.resolve_inner(asset_graph) & self._right.resolve_inner(asset_graph)


class SubAssetSelection(AssetSelection):
    def __init__(self, left: AssetSelection, right: AssetSelection):
        self._left = left
        self._right = right

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        return self._left.resolve_inner(asset_graph) - self._right.resolve_inner(asset_graph)


class SinkAssetSelection(AssetSelection):
    def __init__(self, child: AssetSelection):
        self._child = child

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        selection = self._child.resolve_inner(asset_graph)
        return fetch_sinks(asset_graph.asset_dep_graph, selection)


class RequiredNeighborsAssetSelection(AssetSelection):
    def __init__(self, child: AssetSelection):
        self._child = child

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        selection = self._child.resolve_inner(asset_graph)
        output = set(selection)
        for asset_key in selection:
            output.update(asset_graph.get_required_multi_asset_keys(asset_key))
        return output


class RootAssetSelection(AssetSelection):
    def __init__(self, child: AssetSelection):
        self._child = child

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        selection = self._child.resolve_inner(asset_graph)
        return fetch_sources(asset_graph.asset_dep_graph, selection)


class DownstreamAssetSelection(AssetSelection):
    def __init__(
        self,
        child: AssetSelection,
        *,
        depth: Optional[int] = None,
        include_self: Optional[bool] = True,
    ):
        self._child = child
        self.depth = depth
        self.include_self = include_self

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        selection = self._child.resolve_inner(asset_graph)
        return operator.sub(
            reduce(
                operator.or_,
                [
                    {asset_key}
                    | fetch_connected(
                        item=asset_key,
                        graph=asset_graph.asset_dep_graph,
                        direction="downstream",
                        depth=self.depth,
                    )
                    for asset_key in selection
                ],
            ),
            selection if not self.include_self else set(),
        )


class GroupsAssetSelection(AssetSelection):
    def __init__(self, *groups: str):
        self._groups = groups

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        return {
            asset_key
            for asset_key, group in asset_graph.group_names_by_key.items()
            if group in self._groups and asset_key not in asset_graph.source_asset_keys
        }


class KeysAssetSelection(AssetSelection):
    def __init__(self, *keys: AssetKey):
        self._keys = keys

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        specified_keys = set(self._keys)
        invalid_keys = {
            key
            for key in specified_keys
            if key not in asset_graph.all_asset_keys and key not in asset_graph.source_asset_keys
        }
        if invalid_keys:
            raise DagsterInvalidSubsetError(
                f"AssetKey(s) {invalid_keys} were selected, but no AssetsDefinition objects supply "
                "these keys. Make sure all keys are spelled correctly, and all AssetsDefinitions "
                "are correctly added to the `Definitions`."
            )
        return specified_keys


class OrAssetSelection(AssetSelection):
    def __init__(self, left: AssetSelection, right: AssetSelection):
        self._left = left
        self._right = right

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        return self._left.resolve_inner(asset_graph) | self._right.resolve_inner(asset_graph)


class UpstreamAssetSelection(AssetSelection):
    def __init__(
        self,
        child: AssetSelection,
        *,
        depth: Optional[int] = None,
        include_self: Optional[bool] = True,
    ):
        self._child = child
        self.depth = depth
        self.include_self = include_self

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        selection = self._child.resolve_inner(asset_graph)
        if len(selection) == 0:
            return selection

        all_upstream = operator.sub(
            reduce(
                operator.or_,
                [
                    {asset_key}
                    | fetch_connected(
                        item=asset_key,
                        graph=asset_graph.asset_dep_graph,
                        direction="upstream",
                        depth=self.depth,
                    )
                    for asset_key in selection
                ],
                set(),
            ),
            selection if not self.include_self else set(),
        )
        return {key for key in all_upstream if key not in asset_graph.source_asset_keys}
