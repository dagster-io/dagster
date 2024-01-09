import collections.abc
import operator
from abc import ABC, abstractmethod
from functools import reduce
from typing import AbstractSet, Iterable, NamedTuple, Optional, Sequence, Union, cast

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import deprecated, public
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.errors import DagsterInvalidSubsetError
from dagster._core.selector.subset_selector import (
    fetch_connected,
    fetch_sinks,
    fetch_sources,
    parse_clause,
)
from dagster._serdes.serdes import whitelist_for_serdes

from .asset_check_spec import AssetCheckKey
from .asset_graph import AssetGraph, InternalAssetGraph
from .assets import AssetsDefinition
from .events import (
    AssetKey,
    CoercibleToAssetKey,
    CoercibleToAssetKeyPrefix,
    key_prefix_from_coercible,
)
from .source_asset import SourceAsset

CoercibleToAssetSelection: TypeAlias = Union[
    str,
    Sequence[str],
    Sequence[AssetKey],
    Sequence[Union["AssetsDefinition", "SourceAsset"]],
    "AssetSelection",
]


class AssetSelection(ABC):
    """An AssetSelection defines a query over a set of assets and asset checks, normally all that are defined in a code location.

    You can use the "|", "&", and "-" operators to create unions, intersections, and differences of selections, respectively.

    AssetSelections are typically used with :py:func:`define_asset_job`.

    By default, selecting assets will also select all of the asset checks that target those assets.

    Examples:
        .. code-block:: python

            # Select all assets in group "marketing":
            AssetSelection.groups("marketing")

            # Select all assets in group "marketing", as well as the asset with key "promotion":
            AssetSelection.groups("marketing") | AssetSelection.keys("promotion")

            # Select all assets in group "marketing" that are downstream of asset "leads":
            AssetSelection.groups("marketing") & AssetSelection.keys("leads").downstream()

            # Select a list of assets:
            AssetSelection.assets(*my_assets_list)

            # Select all assets except for those in group "marketing"
            AssetSelection.all() - AssetSelection.groups("marketing")

            # Select all assets which are materialized by the same op as "projections":
            AssetSelection.keys("projections").required_multi_asset_neighbors()

            # Select all assets in group "marketing" and exclude their asset checks:
            AssetSelection.groups("marketing") - AssetSelection.all_asset_checks()

            # Select all asset checks that target a list of assets:
            AssetSelection.checks_for_assets(*my_assets_list)

            # Select a specific asset check:
            AssetSelection.checks(my_asset_check)

    """

    @public
    @staticmethod
    def all() -> "AllSelection":
        """Returns a selection that includes all assets and asset checks."""
        return AllSelection()

    @public
    @staticmethod
    def all_asset_checks() -> "AllAssetCheckSelection":
        """Returns a selection that includes all asset checks."""
        return AllAssetCheckSelection()

    @public
    @staticmethod
    def assets(*assets_defs: AssetsDefinition) -> "KeysAssetSelection":
        """Returns a selection that includes all of the provided assets and asset checks that target them."""
        return KeysAssetSelection([key for assets_def in assets_defs for key in assets_def.keys])

    @public
    @staticmethod
    def keys(*asset_keys: CoercibleToAssetKey) -> "KeysAssetSelection":
        """Returns a selection that includes assets with any of the provided keys and all asset checks that target them.

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
            AssetKey.from_user_string(key) if isinstance(key, str) else AssetKey.from_coercible(key)
            for key in asset_keys
        ]
        return KeysAssetSelection(_asset_keys)

    @public
    @staticmethod
    def key_prefixes(
        *key_prefixes: CoercibleToAssetKeyPrefix, include_sources: bool = False
    ) -> "KeyPrefixesAssetSelection":
        """Returns a selection that includes assets that match any of the provided key prefixes and all the asset checks that target them.

        Args:
            include_sources (bool): If True, then include source assets matching the key prefix(es)
                in the selection.

        Examples:
            .. code-block:: python

              # match any asset key where the first segment is equal to "a" or "b"
              # e.g. AssetKey(["a", "b", "c"]) would match, but AssetKey(["abc"]) would not.
              AssetSelection.key_prefixes("a", "b")

              # match any asset key where the first two segments are ["a", "b"] or ["a", "c"]
              AssetSelection.key_prefixes(["a", "b"], ["a", "c"])
        """
        _asset_key_prefixes = [key_prefix_from_coercible(key_prefix) for key_prefix in key_prefixes]
        return KeyPrefixesAssetSelection(_asset_key_prefixes, include_sources=include_sources)

    @public
    @staticmethod
    def groups(*group_strs, include_sources: bool = False) -> "GroupsAssetSelection":
        """Returns a selection that includes materializable assets that belong to any of the
        provided groups and all the asset checks that target them.

        Args:
            include_sources (bool): If True, then include source assets matching the group in the
                selection.
        """
        check.tuple_param(group_strs, "group_strs", of_type=str)
        return GroupsAssetSelection(group_strs, include_sources=include_sources)

    @public
    @staticmethod
    def checks_for_assets(*assets_defs: AssetsDefinition) -> "AssetChecksForAssetKeysSelection":
        """Returns a selection with the asset checks that target the provided assets."""
        return AssetChecksForAssetKeysSelection(
            [key for assets_def in assets_defs for key in assets_def.keys]
        )

    @public
    @staticmethod
    def checks(*asset_checks: AssetChecksDefinition) -> "AssetCheckKeysSelection":
        """Returns a selection that includes all of the provided asset checks."""
        return AssetCheckKeysSelection(
            [
                AssetCheckKey(asset_key=AssetKey.from_coercible(spec.asset_key), name=spec.name)
                for checks_def in asset_checks
                for spec in checks_def.specs
            ]
        )

    @public
    def downstream(
        self, depth: Optional[int] = None, include_self: bool = True
    ) -> "DownstreamAssetSelection":
        """Returns a selection that includes all assets that are downstream of any of the assets in
        this selection, selecting the assets in this selection by default. Includes the asset checks targeting the returned assets. Iterates through each
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
        """Returns a selection that includes all materializable assets that are upstream of any of
        the assets in this selection, selecting the assets in this selection by default. Includes the asset checks targeting the returned assets. Iterates
        through each asset in this selection and returns the union of all upstream assets.

        Because mixed selections of source and materializable assets are currently not supported,
        keys corresponding to `SourceAssets` will not be included as upstream of regular assets.

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
    def sinks(self) -> "SinksAssetSelection":
        """Given an asset selection, returns a new asset selection that contains all of the sink
        assets within the original asset selection. Includes the asset checks targeting the returned assets.

        A sink asset is an asset that has no downstream dependencies within the asset selection.
        The sink asset can have downstream dependencies outside of the asset selection.
        """
        return SinksAssetSelection(self)

    @public
    def required_multi_asset_neighbors(self) -> "RequiredNeighborsAssetSelection":
        """Given an asset selection in which some assets are output from a multi-asset compute op
        which cannot be subset, returns a new asset selection that contains all of the assets
        required to execute the original asset selection. Includes the asset checks targeting the returned assets.
        """
        return RequiredNeighborsAssetSelection(self)

    @public
    def roots(self) -> "RootsAssetSelection":
        """Given an asset selection, returns a new asset selection that contains all of the root
        assets within the original asset selection. Includes the asset checks targeting the returned assets.

        A root asset is an asset that has no upstream dependencies within the asset selection.
        The root asset can have downstream dependencies outside of the asset selection.

        Because mixed selections of source and materializable assets are currently not supported,
        keys corresponding to `SourceAssets` will not be included as roots. To select source assets,
        use the `upstream_source_assets` method.
        """
        return RootsAssetSelection(self)

    @public
    @deprecated(breaking_version="2.0", additional_warn_text="Use AssetSelection.roots instead.")
    def sources(self) -> "RootsAssetSelection":
        """Given an asset selection, returns a new asset selection that contains all of the root
        assets within the original asset selection. Includes the asset checks targeting the returned assets.

        A root asset is a materializable asset that has no upstream dependencies within the asset
        selection. The root asset can have downstream dependencies outside of the asset selection.

        Because mixed selections of source and materializable assets are currently not supported,
        keys corresponding to `SourceAssets` will not be included as roots. To select source assets,
        use the `upstream_source_assets` method.
        """
        return self.roots()

    @public
    def upstream_source_assets(self) -> "ParentSourcesAssetSelection":
        """Given an asset selection, returns a new asset selection that contains all of the source
        assets that are parents of assets in the original selection. Includes the asset checks
        targeting the returned assets.
        """
        return ParentSourcesAssetSelection(self)

    @public
    def without_checks(self) -> "AssetSelection":
        """Removes all asset checks in the selection."""
        return self - AssetSelection.all_asset_checks()

    def __or__(self, other: "AssetSelection") -> "OrAssetSelection":
        check.inst_param(other, "other", AssetSelection)

        operands = []
        for selection in (self, other):
            if isinstance(selection, OrAssetSelection):
                operands.extend(selection.operands)
            else:
                operands.append(selection)

        return OrAssetSelection(operands)

    def __and__(self, other: "AssetSelection") -> "AndAssetSelection":
        check.inst_param(other, "other", AssetSelection)

        operands = []
        for selection in (self, other):
            if isinstance(selection, AndAssetSelection):
                operands.extend(selection.operands)
            else:
                operands.append(selection)

        return AndAssetSelection(operands)

    def __sub__(self, other: "AssetSelection") -> "SubtractAssetSelection":
        check.inst_param(other, "other", AssetSelection)
        return SubtractAssetSelection(self, other)

    def resolve(
        self, all_assets: Union[Iterable[Union[AssetsDefinition, SourceAsset]], AssetGraph]
    ) -> AbstractSet[AssetKey]:
        if isinstance(all_assets, AssetGraph):
            asset_graph = all_assets
        else:
            check.iterable_param(all_assets, "all_assets", (AssetsDefinition, SourceAsset))
            asset_graph = AssetGraph.from_assets(all_assets)

        return self.resolve_inner(asset_graph)

    @abstractmethod
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        raise NotImplementedError()

    def resolve_checks(self, asset_graph: InternalAssetGraph) -> AbstractSet[AssetCheckKey]:
        """We don't need this method currently, but it makes things consistent with resolve_inner. Currently
        we don't store checks in the ExternalAssetGraph, so we only support InternalAssetGraph.
        """
        return self.resolve_checks_inner(asset_graph)

    def resolve_checks_inner(self, asset_graph: InternalAssetGraph) -> AbstractSet[AssetCheckKey]:
        """By default, resolve to checks that target the selected assets. This is overriden for particular selections."""
        asset_keys = self.resolve(asset_graph)
        return {handle for handle in asset_graph.asset_check_keys if handle.asset_key in asset_keys}

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
        elif isinstance(selection, collections.abc.Sequence) and all(
            isinstance(el, str) for el in selection
        ):
            return reduce(
                operator.or_, [cls._selection_from_string(cast(str, s)) for s in selection]
            )
        elif isinstance(selection, collections.abc.Sequence) and all(
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
        elif isinstance(selection, collections.abc.Sequence) and all(
            isinstance(el, AssetKey) for el in selection
        ):
            return cls.keys(*cast(Sequence[AssetKey], selection))
        else:
            check.failed(
                "selection argument must be one of str, Sequence[str], Sequence[AssetKey],"
                " Sequence[AssetsDefinition], Sequence[SourceAsset], AssetSelection. Was"
                f" {type(selection)}."
            )

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return AssetSelection.keys(*self.resolve(asset_graph))


@whitelist_for_serdes
class AllSelection(AssetSelection, NamedTuple("_AllSelection", [])):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        return asset_graph.materializable_asset_keys

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self

    def __str__(self) -> str:
        return "all materializable assets"


@whitelist_for_serdes
class AllAssetCheckSelection(AssetSelection, NamedTuple("_AllAssetChecksSelection", [])):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        return set()

    def resolve_checks_inner(self, asset_graph: InternalAssetGraph) -> AbstractSet[AssetCheckKey]:
        return asset_graph.asset_check_keys

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self

    def __str__(self) -> str:
        return "all asset checks"


@whitelist_for_serdes
class AssetChecksForAssetKeysSelection(
    NamedTuple("_AssetChecksForAssetKeysSelection", [("selected_asset_keys", Sequence[AssetKey])]),
    AssetSelection,
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        return set()

    def resolve_checks_inner(self, asset_graph: InternalAssetGraph) -> AbstractSet[AssetCheckKey]:
        return {
            handle
            for handle in asset_graph.asset_check_keys
            if handle.asset_key in self.selected_asset_keys
        }

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self


@whitelist_for_serdes
class AssetCheckKeysSelection(
    NamedTuple(
        "_AssetCheckKeysSelection", [("selected_asset_check_keys", Sequence[AssetCheckKey])]
    ),
    AssetSelection,
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        return set()

    def resolve_checks_inner(self, asset_graph: InternalAssetGraph) -> AbstractSet[AssetCheckKey]:
        return {
            handle
            for handle in asset_graph.asset_check_keys
            if handle in self.selected_asset_check_keys
        }

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self


@whitelist_for_serdes
class AndAssetSelection(
    AssetSelection,
    NamedTuple("_AndAssetSelection", [("operands", Sequence[AssetSelection])]),
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        return reduce(
            operator.and_, (selection.resolve_inner(asset_graph) for selection in self.operands)
        )

    def resolve_checks_inner(self, asset_graph: InternalAssetGraph) -> AbstractSet[AssetCheckKey]:
        return reduce(
            operator.and_,
            (selection.resolve_checks_inner(asset_graph) for selection in self.operands),
        )

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self._replace(
            operands=[
                operand.to_serializable_asset_selection(asset_graph) for operand in self.operands
            ]
        )


@whitelist_for_serdes
class OrAssetSelection(
    AssetSelection,
    NamedTuple("_OrAssetSelection", [("operands", Sequence[AssetSelection])]),
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        return reduce(
            operator.or_, (selection.resolve_inner(asset_graph) for selection in self.operands)
        )

    def resolve_checks_inner(self, asset_graph: InternalAssetGraph) -> AbstractSet[AssetCheckKey]:
        return reduce(
            operator.or_,
            (selection.resolve_checks_inner(asset_graph) for selection in self.operands),
        )

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self._replace(
            operands=[
                operand.to_serializable_asset_selection(asset_graph) for operand in self.operands
            ]
        )


@whitelist_for_serdes
class SubtractAssetSelection(
    AssetSelection,
    NamedTuple("_SubtractAssetSelection", [("left", AssetSelection), ("right", AssetSelection)]),
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        return self.left.resolve_inner(asset_graph) - self.right.resolve_inner(asset_graph)

    def resolve_checks_inner(self, asset_graph: InternalAssetGraph) -> AbstractSet[AssetCheckKey]:
        return self.left.resolve_checks_inner(asset_graph) - self.right.resolve_checks_inner(
            asset_graph
        )

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self._replace(
            left=self.left.to_serializable_asset_selection(asset_graph),
            right=self.right.to_serializable_asset_selection(asset_graph),
        )


@whitelist_for_serdes
class SinksAssetSelection(
    AssetSelection,
    NamedTuple("_SinksAssetSelection", [("child", AssetSelection)]),
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph)
        return fetch_sinks(asset_graph.asset_dep_graph, selection)

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self._replace(child=self.child.to_serializable_asset_selection(asset_graph))


@whitelist_for_serdes
class RequiredNeighborsAssetSelection(
    AssetSelection,
    NamedTuple("_RequiredNeighborsAssetSelection", [("child", AssetSelection)]),
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph)
        output = set(selection)
        for asset_key in selection:
            output.update(asset_graph.get_required_multi_asset_keys(asset_key))
        return output

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self._replace(child=self.child.to_serializable_asset_selection(asset_graph))


@whitelist_for_serdes
class RootsAssetSelection(
    AssetSelection,
    NamedTuple("_RootsAssetSelection", [("child", AssetSelection)]),
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph)
        return fetch_sources(asset_graph.asset_dep_graph, selection)

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self._replace(child=self.child.to_serializable_asset_selection(asset_graph))


@whitelist_for_serdes
class DownstreamAssetSelection(
    AssetSelection,
    NamedTuple(
        "_DownstreamAssetSelection",
        [
            ("child", AssetSelection),
            ("depth", Optional[int]),
            ("include_self", bool),
        ],
    ),
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph)
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

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self._replace(child=self.child.to_serializable_asset_selection(asset_graph))


@whitelist_for_serdes
class GroupsAssetSelection(
    NamedTuple(
        "_GroupsAssetSelection",
        [
            ("selected_groups", Sequence[str]),
            ("include_sources", bool),
        ],
    ),
    AssetSelection,
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        base_set = (
            asset_graph.all_asset_keys
            if self.include_sources
            else asset_graph.materializable_asset_keys
        )
        return {
            asset_key
            for asset_key, group in asset_graph.group_names_by_key.items()
            if group in self.selected_groups and asset_key in base_set
        }

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self

    def __str__(self) -> str:
        if len(self.selected_groups) == 1:
            return f"group:{self.selected_groups[0]}"
        else:
            return f"group:({' or '.join(self.selected_groups)})"


@whitelist_for_serdes
class KeysAssetSelection(
    NamedTuple("_KeysAssetSelection", [("selected_keys", Sequence[AssetKey])]),
    AssetSelection,
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        specified_keys = set(self.selected_keys)
        invalid_keys = {key for key in specified_keys if key not in asset_graph.all_asset_keys}
        if invalid_keys:
            raise DagsterInvalidSubsetError(
                f"AssetKey(s) {invalid_keys} were selected, but no AssetsDefinition objects supply "
                "these keys. Make sure all keys are spelled correctly, and all AssetsDefinitions "
                "are correctly added to the `Definitions`."
            )
        return specified_keys

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self

    def __str__(self) -> str:
        return f"{' or '.join(k.to_user_string() for k in self.selected_keys)}"


@whitelist_for_serdes
class KeyPrefixesAssetSelection(
    NamedTuple(
        "_KeyPrefixesAssetSelection",
        [("selected_key_prefixes", Sequence[Sequence[str]]), ("include_sources", bool)],
    ),
    AssetSelection,
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        base_set = (
            asset_graph.all_asset_keys
            if self.include_sources
            else asset_graph.materializable_asset_keys
        )
        return {
            key
            for key in base_set
            if any(key.has_prefix(prefix) for prefix in self.selected_key_prefixes)
        }

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self

    def __str__(self) -> str:
        key_prefix_strs = ["/".join(key_prefix) for key_prefix in self.selected_key_prefixes]
        if len(self.selected_key_prefixes) == 1:
            return f"key_prefix:{key_prefix_strs[0]}"
        else:
            return f"key_prefix:({' or '.join(key_prefix_strs)})"


def _fetch_all_upstream(
    selection: AbstractSet[AssetKey],
    asset_graph: AssetGraph,
    depth: Optional[int] = None,
    include_self: bool = True,
) -> AbstractSet[AssetKey]:
    return operator.sub(
        reduce(
            operator.or_,
            [
                {asset_key}
                | fetch_connected(
                    item=asset_key,
                    graph=asset_graph.asset_dep_graph,
                    direction="upstream",
                    depth=depth,
                )
                for asset_key in selection
            ],
            set(),
        ),
        selection if not include_self else set(),
    )


@whitelist_for_serdes
class UpstreamAssetSelection(
    AssetSelection,
    NamedTuple(
        "_UpstreamAssetSelection",
        [
            ("child", AssetSelection),
            ("depth", Optional[int]),
            ("include_self", bool),
        ],
    ),
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph)
        if len(selection) == 0:
            return selection
        all_upstream = _fetch_all_upstream(selection, asset_graph, self.depth, self.include_self)
        return {key for key in all_upstream if key not in asset_graph.source_asset_keys}

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self._replace(child=self.child.to_serializable_asset_selection(asset_graph))


@whitelist_for_serdes
class ParentSourcesAssetSelection(
    AssetSelection,
    NamedTuple("_ParentSourcesAssetSelection", [("child", AssetSelection)]),
):
    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph)
        if len(selection) == 0:
            return selection
        all_upstream = _fetch_all_upstream(selection, asset_graph)
        return {key for key in all_upstream if key in asset_graph.source_asset_keys}

    def to_serializable_asset_selection(self, asset_graph: AssetGraph) -> "AssetSelection":
        return self._replace(child=self.child.to_serializable_asset_selection(asset_graph))
