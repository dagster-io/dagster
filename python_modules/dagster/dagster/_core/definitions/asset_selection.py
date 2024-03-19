import collections.abc
import operator
from abc import ABC, abstractmethod
from functools import reduce
from typing import AbstractSet, Iterable, Optional, Sequence, Union, cast

import pydantic
from pydantic import BaseModel
from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import deprecated, experimental, experimental_param, public
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.resolved_asset_deps import resolve_similar_asset_names
from dagster._core.errors import DagsterInvalidSubsetError
from dagster._core.selector.subset_selector import (
    fetch_connected,
    fetch_sinks,
    fetch_sources,
    parse_clause,
)
from dagster._core.storage.tags import TAG_NO_VALUE
from dagster._serdes.serdes import whitelist_for_serdes

from .asset_check_spec import AssetCheckKey
from .asset_key import (
    AssetKey,
    CoercibleToAssetKey,
    CoercibleToAssetKeyPrefix,
    key_prefix_from_coercible,
)
from .assets import AssetsDefinition
from .base_asset_graph import BaseAssetGraph
from .source_asset import SourceAsset

CoercibleToAssetSelection: TypeAlias = Union[
    str,
    Sequence[str],
    Sequence[AssetKey],
    Sequence[Union["AssetsDefinition", "SourceAsset"]],
    "AssetSelection",
]


class AssetSelection(ABC, BaseModel, frozen=True):
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
    @experimental_param(param="include_sources")
    @staticmethod
    def all(include_sources: bool = False) -> "AllSelection":
        """Returns a selection that includes all assets and asset checks.

        Args:
            include_sources (bool): If True, then include all source assets.
        """
        return AllSelection(include_sources=include_sources)

    @public
    @staticmethod
    def all_asset_checks() -> "AllAssetCheckSelection":
        """Returns a selection that includes all asset checks."""
        return AllAssetCheckSelection()

    @public
    @staticmethod
    def assets(*assets_defs: AssetsDefinition) -> "KeysAssetSelection":
        """Returns a selection that includes all of the provided assets and asset checks that target them."""
        return KeysAssetSelection(
            selected_keys=[key for assets_def in assets_defs for key in assets_def.keys]
        )

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
        return KeysAssetSelection(selected_keys=_asset_keys)

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
        return KeyPrefixesAssetSelection(
            selected_key_prefixes=_asset_key_prefixes, include_sources=include_sources
        )

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
        return GroupsAssetSelection(selected_groups=group_strs, include_sources=include_sources)

    @public
    @staticmethod
    @experimental
    def tag(key: str, value: str, include_sources: bool = False) -> "AssetSelection":
        """Returns a selection that includes materializable assets that have the provided tag, and
        all the asset checks that target them.


        Args:
            include_sources (bool): If True, then include source assets matching the group in the
                selection.
        """
        return TagAssetSelection(key=key, value=value, include_sources=include_sources)

    @staticmethod
    def tag_string(string: str, include_sources: bool = False) -> "AssetSelection":
        """Returns a selection that includes materializable assets that have the provided tag, and
        all the asset checks that target them.


        Args:
            include_sources (bool): If True, then include source assets matching the group in the
                selection.
        """
        split_by_equals_segments = string.split("=")
        if len(split_by_equals_segments) == 1:
            return TagAssetSelection(
                key=string, value=TAG_NO_VALUE, include_sources=include_sources
            )
        elif len(split_by_equals_segments) == 2:
            key, value = split_by_equals_segments
            return TagAssetSelection(key=key, value=value, include_sources=include_sources)
        else:
            check.failed(f"Invalid tag selection string: {string}. Must have no more than one '='.")

    @public
    @staticmethod
    def checks_for_assets(*assets_defs: AssetsDefinition) -> "AssetChecksForAssetKeysSelection":
        """Returns a selection with the asset checks that target the provided assets."""
        return AssetChecksForAssetKeysSelection(
            selected_asset_keys=[key for assets_def in assets_defs for key in assets_def.keys]
        )

    @public
    @staticmethod
    def checks(
        *assets_defs_or_check_keys: Union[AssetsDefinition, AssetCheckKey],
    ) -> "AssetCheckKeysSelection":
        """Returns a selection that includes all of the provided asset checks or check keys."""
        assets_defs = [ad for ad in assets_defs_or_check_keys if isinstance(ad, AssetsDefinition)]
        check_keys = [key for key in assets_defs_or_check_keys if isinstance(key, AssetCheckKey)]
        return AssetCheckKeysSelection(
            selected_asset_check_keys=[
                *(key for ad in assets_defs for key in ad.check_keys),
                *check_keys,
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
        return DownstreamAssetSelection(child=self, depth=depth, include_self=include_self)

    @public
    def upstream(
        self, depth: Optional[int] = None, include_self: bool = True
    ) -> "UpstreamAssetSelection":
        """Returns a selection that includes all materializable assets that are upstream of any of
        the assets in this selection, selecting the assets in this selection by default. Includes
        the asset checks targeting the returned assets. Iterates through each asset in this
        selection and returns the union of all upstream assets.

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
        return UpstreamAssetSelection(child=self, depth=depth, include_self=include_self)

    @public
    def sinks(self) -> "SinksAssetSelection":
        """Given an asset selection, returns a new asset selection that contains all of the sink
        assets within the original asset selection. Includes the asset checks targeting the returned assets.

        A sink asset is an asset that has no downstream dependencies within the asset selection.
        The sink asset can have downstream dependencies outside of the asset selection.
        """
        return SinksAssetSelection(child=self)

    @public
    def required_multi_asset_neighbors(self) -> "RequiredNeighborsAssetSelection":
        """Given an asset selection in which some assets are output from a multi-asset compute op
        which cannot be subset, returns a new asset selection that contains all of the assets
        required to execute the original asset selection. Includes the asset checks targeting the returned assets.
        """
        return RequiredNeighborsAssetSelection(child=self)

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
        return RootsAssetSelection(child=self)

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
        return ParentSourcesAssetSelection(child=self)

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

        return OrAssetSelection(operands=operands)

    def __and__(self, other: "AssetSelection") -> "AndAssetSelection":
        check.inst_param(other, "other", AssetSelection)

        operands = []
        for selection in (self, other):
            if isinstance(selection, AndAssetSelection):
                operands.extend(selection.operands)
            else:
                operands.append(selection)

        return AndAssetSelection(operands=operands)

    def __bool__(self):
        # Ensure that even if a subclass is a NamedTuple with no fields, it is still truthy
        return True

    def __sub__(self, other: "AssetSelection") -> "SubtractAssetSelection":
        check.inst_param(other, "other", AssetSelection)
        return SubtractAssetSelection(left=self, right=other)

    def resolve(
        self,
        all_assets: Union[Iterable[Union[AssetsDefinition, SourceAsset]], BaseAssetGraph],
        allow_missing: bool = False,
    ) -> AbstractSet[AssetKey]:
        """Returns the set of asset keys in all_assets that match this selection.

        Args:
            allow_missing (bool): If False, will raise an error if any of the leaf selections in the
                asset selection target entities that don't exist in the set of provided assets.
        """
        if isinstance(all_assets, BaseAssetGraph):
            asset_graph = all_assets
        else:
            check.iterable_param(all_assets, "all_assets", (AssetsDefinition, SourceAsset))
            asset_graph = AssetGraph.from_assets(all_assets)

        return self.resolve_inner(asset_graph, allow_missing=allow_missing)

    @abstractmethod
    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        raise NotImplementedError()

    def resolve_checks(
        self, asset_graph: AssetGraph, allow_missing: bool = False
    ) -> AbstractSet[AssetCheckKey]:
        """We don't need this method currently, but it makes things consistent with resolve_inner. Currently
        we don't store checks in the RemoteAssetGraph, so we only support AssetGraph.
        """
        return self.resolve_checks_inner(asset_graph, allow_missing=allow_missing)

    def resolve_checks_inner(
        self, asset_graph: AssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetCheckKey]:
        """By default, resolve to checks that target the selected assets. This is overriden for particular selections."""
        asset_keys = self.resolve(asset_graph)
        return {handle for handle in asset_graph.asset_check_keys if handle.asset_key in asset_keys}

    @classmethod
    def from_string(cls, string: str) -> "AssetSelection":
        if string == "*":
            return cls.all()

        parts = parse_clause(string)
        if parts is not None:
            key_selection = cls.keys(parts.item_name)
            if parts.up_depth and parts.down_depth:
                selection = key_selection.upstream(parts.up_depth) | key_selection.downstream(
                    parts.down_depth
                )
            elif parts.up_depth:
                selection = key_selection.upstream(parts.up_depth)
            elif parts.down_depth:
                selection = key_selection.downstream(parts.down_depth)
            else:
                selection = key_selection
            return selection

        elif string.startswith("tag:"):
            tag_str = string[len("tag:") :]
            return cls.tag_string(tag_str)

        check.failed(f"Invalid selection string: {string}")

    @classmethod
    def from_coercible(cls, selection: CoercibleToAssetSelection) -> "AssetSelection":
        if isinstance(selection, str):
            return cls.from_string(selection)
        elif isinstance(selection, AssetSelection):
            return selection
        elif isinstance(selection, collections.abc.Sequence) and all(
            isinstance(el, str) for el in selection
        ):
            return reduce(operator.or_, [cls.from_string(cast(str, s)) for s in selection])
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

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return AssetSelection.keys(*self.resolve(asset_graph))

    def replace(self, **kwargs):
        if pydantic.__version__ >= "2":
            func = getattr(BaseModel, "model_copy")
        else:
            func = getattr(BaseModel, "copy")
        return func(self, update=kwargs)

    def needs_parentheses_when_operand(self) -> bool:
        """When generating a string representation of an asset selection and this asset selection
        is an operand in a larger expression, whether it needs to be surrounded by parentheses.
        """
        return False

    def operand__str__(self) -> str:
        return f"({self})" if self.needs_parentheses_when_operand() else str(self)


@whitelist_for_serdes
class AllSelection(AssetSelection, frozen=True):
    include_sources: Optional[bool] = None

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return (
            asset_graph.all_asset_keys
            if self.include_sources
            else asset_graph.materializable_asset_keys
        )

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self

    def __str__(self) -> str:
        return "all materializable assets" + (" and source assets" if self.include_sources else "")


@whitelist_for_serdes
class AllAssetCheckSelection(AssetSelection, frozen=True):
    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return set()

    def resolve_checks_inner(
        self, asset_graph: AssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetCheckKey]:
        return asset_graph.asset_check_keys

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self

    def __str__(self) -> str:
        return "all asset checks"


@whitelist_for_serdes
class AssetChecksForAssetKeysSelection(AssetSelection, frozen=True):
    selected_asset_keys: Sequence[AssetKey]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return set()

    def resolve_checks_inner(
        self, asset_graph: AssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetCheckKey]:
        return {
            handle
            for handle in asset_graph.asset_check_keys
            if handle.asset_key in self.selected_asset_keys
        }

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self


@whitelist_for_serdes
class AssetCheckKeysSelection(AssetSelection, frozen=True):
    selected_asset_check_keys: Sequence[AssetCheckKey]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return set()

    def resolve_checks_inner(
        self, asset_graph: AssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetCheckKey]:
        specified_keys = set(self.selected_asset_check_keys)
        missing_keys = {key for key in specified_keys if key not in asset_graph.asset_check_keys}

        if not allow_missing and missing_keys:
            raise DagsterInvalidSubsetError(
                f"AssetCheckKey(s) {[k.to_user_string() for k in missing_keys]} were selected, but "
                "no definitions supply these keys. Make sure all keys are spelled "
                "correctly, and all definitions are correctly added to the "
                f"`Definitions`."
            )
        return specified_keys & asset_graph.asset_check_keys

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self


@whitelist_for_serdes
class AndAssetSelection(
    AssetSelection,
    frozen=True,
    arbitrary_types_allowed=True,
):
    operands: Sequence[AssetSelection]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return reduce(
            operator.and_,
            (
                selection.resolve_inner(asset_graph, allow_missing=allow_missing)
                for selection in self.operands
            ),
        )

    def resolve_checks_inner(
        self, asset_graph: AssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetCheckKey]:
        return reduce(
            operator.and_,
            (
                selection.resolve_checks_inner(asset_graph, allow_missing=allow_missing)
                for selection in self.operands
            ),
        )

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self.replace(
            operands=[
                operand.to_serializable_asset_selection(asset_graph) for operand in self.operands
            ]
        )

    def needs_parentheses_when_operand(self) -> bool:
        return True

    def __str__(self) -> str:
        return " and ".join(operand.operand__str__() for operand in self.operands)


@whitelist_for_serdes
class OrAssetSelection(
    AssetSelection,
    frozen=True,
    arbitrary_types_allowed=True,
):
    operands: Sequence[AssetSelection]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return reduce(
            operator.or_,
            (
                selection.resolve_inner(asset_graph, allow_missing=allow_missing)
                for selection in self.operands
            ),
        )

    def resolve_checks_inner(
        self, asset_graph: AssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetCheckKey]:
        return reduce(
            operator.or_,
            (
                selection.resolve_checks_inner(asset_graph, allow_missing=allow_missing)
                for selection in self.operands
            ),
        )

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self.replace(
            operands=[
                operand.to_serializable_asset_selection(asset_graph) for operand in self.operands
            ]
        )

    def needs_parentheses_when_operand(self) -> bool:
        return True

    def __str__(self) -> str:
        return " or ".join(operand.operand__str__() for operand in self.operands)


@whitelist_for_serdes
class SubtractAssetSelection(
    AssetSelection,
    frozen=True,
    arbitrary_types_allowed=True,
):
    left: AssetSelection
    right: AssetSelection

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return self.left.resolve_inner(
            asset_graph, allow_missing=allow_missing
        ) - self.right.resolve_inner(asset_graph, allow_missing=allow_missing)

    def resolve_checks_inner(
        self, asset_graph: AssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetCheckKey]:
        return self.left.resolve_checks_inner(
            asset_graph, allow_missing=allow_missing
        ) - self.right.resolve_checks_inner(asset_graph, allow_missing=allow_missing)

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self.replace(
            left=self.left.to_serializable_asset_selection(asset_graph),
            right=self.right.to_serializable_asset_selection(asset_graph),
        )

    def needs_parentheses_when_operand(self) -> bool:
        return True

    def __str__(self) -> str:
        return f"{self.left.operand__str__()} - {self.right.operand__str__()}"


@whitelist_for_serdes
class SinksAssetSelection(
    AssetSelection,
    frozen=True,
    arbitrary_types_allowed=True,
):
    child: AssetSelection

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph, allow_missing=allow_missing)
        return fetch_sinks(asset_graph.asset_dep_graph, selection)

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self.replace(child=self.child.to_serializable_asset_selection(asset_graph))


@whitelist_for_serdes
class RequiredNeighborsAssetSelection(
    AssetSelection,
    frozen=True,
    arbitrary_types_allowed=True,
):
    child: AssetSelection

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph, allow_missing=allow_missing)
        output = set(selection)
        for asset_key in selection:
            output.update(asset_graph.get(asset_key).execution_set_asset_keys)
        return output

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self.replace(child=self.child.to_serializable_asset_selection(asset_graph))


@whitelist_for_serdes
class RootsAssetSelection(
    AssetSelection,
    frozen=True,
    arbitrary_types_allowed=True,
):
    child: AssetSelection

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph, allow_missing=allow_missing)
        return fetch_sources(asset_graph.asset_dep_graph, selection)

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self.replace(child=self.child.to_serializable_asset_selection(asset_graph))


@whitelist_for_serdes
class DownstreamAssetSelection(
    AssetSelection,
    frozen=True,
    arbitrary_types_allowed=True,
):
    child: AssetSelection
    depth: Optional[int]
    include_self: bool

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph, allow_missing=allow_missing)
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

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self.replace(child=self.child.to_serializable_asset_selection(asset_graph))


@whitelist_for_serdes
class GroupsAssetSelection(AssetSelection, frozen=True):
    selected_groups: Sequence[str]
    include_sources: bool

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        base_set = (
            asset_graph.all_asset_keys
            if self.include_sources
            else asset_graph.materializable_asset_keys
        )
        return {
            key
            for group in self.selected_groups
            for key in asset_graph.asset_keys_for_group(group)
            if key in base_set
        }

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self

    def __str__(self) -> str:
        if len(self.selected_groups) == 1:
            return f"group:{self.selected_groups[0]}"
        else:
            return f"group:({' or '.join(self.selected_groups)})"


@whitelist_for_serdes
class TagAssetSelection(AssetSelection, frozen=True):
    key: str
    value: str
    include_sources: bool

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        base_set = (
            asset_graph.all_asset_keys
            if self.include_sources
            else asset_graph.materializable_asset_keys
        )

        return {key for key in base_set if asset_graph.get(key).tags.get(self.key) == self.value}

    def __str__(self) -> str:
        return f"tag:{self.key}={self.value}"


@whitelist_for_serdes
class KeysAssetSelection(AssetSelection, frozen=True):
    selected_keys: Sequence[AssetKey]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        specified_keys = set(self.selected_keys)
        missing_keys = {key for key in specified_keys if key not in asset_graph.all_asset_keys}

        if not allow_missing:
            # Arbitrary limit to avoid huge error messages
            keys_to_suggest = list(missing_keys)[:4]
            suggestions = ""
            for invalid_key in keys_to_suggest:
                similar_names = resolve_similar_asset_names(invalid_key, asset_graph.all_asset_keys)
                if similar_names:
                    # Arbitrarily limit to 10 similar names to avoid a huge error message
                    subset_similar_names = similar_names[:10]
                    similar_to_string = ", ".join(
                        (similar.to_string() for similar in subset_similar_names)
                    )
                    suggestions += (
                        f"\n\nFor selected asset {invalid_key.to_string()}, did you mean one of "
                        f"the following?\n\t{similar_to_string}"
                    )

            if missing_keys:
                raise DagsterInvalidSubsetError(
                    f"AssetKey(s) {[k.to_user_string() for k in missing_keys]} were selected, but "
                    "no AssetsDefinition objects supply these keys. Make sure all keys are spelled "
                    "correctly, and all AssetsDefinitions are correctly added to the "
                    f"`Definitions`.{suggestions}"
                )

        return specified_keys - missing_keys

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self

    def needs_parentheses_when_operand(self) -> bool:
        return len(self.selected_keys) > 1

    def __str__(self) -> str:
        if len(self.selected_keys) <= 3:
            return f"{' or '.join(k.to_user_string() for k in self.selected_keys)}"
        else:
            return f"{len(self.selected_keys)} assets"


@whitelist_for_serdes
class KeyPrefixesAssetSelection(AssetSelection, frozen=True):
    selected_key_prefixes: Sequence[Sequence[str]]
    include_sources: bool

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
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

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self

    def __str__(self) -> str:
        key_prefix_strs = ["/".join(key_prefix) for key_prefix in self.selected_key_prefixes]
        if len(self.selected_key_prefixes) == 1:
            return f"key_prefix:{key_prefix_strs[0]}"
        else:
            return f"key_prefix:({' or '.join(key_prefix_strs)})"


def _fetch_all_upstream(
    selection: AbstractSet[AssetKey],
    asset_graph: BaseAssetGraph,
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
    frozen=True,
    arbitrary_types_allowed=True,
):
    child: AssetSelection
    depth: Optional[int]
    include_self: bool

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph, allow_missing=allow_missing)
        if len(selection) == 0:
            return selection
        all_upstream = _fetch_all_upstream(selection, asset_graph, self.depth, self.include_self)
        return {key for key in all_upstream if key in asset_graph.materializable_asset_keys}

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self.replace(child=self.child.to_serializable_asset_selection(asset_graph))

    def __str__(self) -> str:
        if self.depth is None:
            base = f"*({self.child})"
        elif self.depth == 0:
            base = str(self.child)
        else:
            base = f"{'+' * self.depth}({self.child})"

        if self.include_self:
            return base
        else:
            return f"{base} - ({self.child})"


@whitelist_for_serdes
class ParentSourcesAssetSelection(
    AssetSelection,
    frozen=True,
    arbitrary_types_allowed=True,
):
    child: AssetSelection

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph, allow_missing=allow_missing)
        if len(selection) == 0:
            return selection
        all_upstream = _fetch_all_upstream(selection, asset_graph)
        return {key for key in all_upstream if key in asset_graph.external_asset_keys}

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self.replace(child=self.child.to_serializable_asset_selection(asset_graph))
