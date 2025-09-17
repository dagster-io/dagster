import collections.abc
import operator
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from functools import reduce
from typing import AbstractSet, Optional, Union, cast  # noqa: UP035

from dagster_shared.error import DagsterError
from dagster_shared.serdes import whitelist_for_serdes
from typing_extensions import TypeAlias, TypeGuard

import dagster._check as check
from dagster._annotations import beta_param, deprecated, public
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_key import (
    AssetKey,
    CoercibleToAssetKey,
    CoercibleToAssetKeyPrefix,
    asset_keys_from_defs_and_coercibles,
    key_prefix_from_coercible,
)
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph, BaseAssetNode
from dagster._core.definitions.resolved_asset_deps import resolve_similar_asset_names
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.errors import DagsterInvalidSubsetError
from dagster._core.selector.subset_selector import (
    fetch_connected,
    fetch_sinks,
    fetch_sources,
    parse_clause,
)
from dagster._core.storage.tags import KIND_PREFIX
from dagster._record import copy, record

CoercibleToAssetSelection: TypeAlias = Union[
    str,
    Sequence[str],
    Sequence[AssetKey],
    Sequence[Union["AssetsDefinition", "SourceAsset"]],
    "AssetSelection",
]


def is_coercible_to_asset_selection(
    obj: object,
) -> TypeGuard[CoercibleToAssetSelection]:
    # can coerce to (but is not already) an AssetSelection
    return isinstance(obj, str) or (
        isinstance(obj, Sequence)
        and all(isinstance(x, (str, AssetKey, AssetsDefinition, SourceAsset)) for x in obj)
    )


class DagsterInvalidAssetSelectionError(DagsterError):
    """An error raised when an invalid asset selection is provided."""

    pass


@public
class AssetSelection(ABC):
    """An AssetSelection defines a query over a set of assets and asset checks, normally all that are defined in a project.

    You can use the "|", "&", and "-" operators to create unions, intersections, and differences of selections, respectively.

    AssetSelections are typically used with :py:func:`define_asset_job`.

    By default, selecting assets will also select all of the asset checks that target those assets.

    Examples:
        .. code-block:: python

            # Select all assets in group "marketing":
            AssetSelection.groups("marketing")

            # Select all assets in group "marketing", as well as the asset with key "promotion":
            AssetSelection.groups("marketing") | AssetSelection.assets("promotion")

            # Select all assets in group "marketing" that are downstream of asset "leads":
            AssetSelection.groups("marketing") & AssetSelection.assets("leads").downstream()

            # Select a list of assets:
            AssetSelection.assets(*my_assets_list)

            # Select all assets except for those in group "marketing"
            AssetSelection.all() - AssetSelection.groups("marketing")

            # Select all assets which are materialized by the same op as "projections":
            AssetSelection.assets("projections").required_multi_asset_neighbors()

            # Select all assets in group "marketing" and exclude their asset checks:
            AssetSelection.groups("marketing") - AssetSelection.all_asset_checks()

            # Select all asset checks that target a list of assets:
            AssetSelection.checks_for_assets(*my_assets_list)

            # Select a specific asset check:
            AssetSelection.checks(my_asset_check)

    """

    @public
    @staticmethod
    @beta_param(param="include_sources")
    def all(include_sources: bool = False) -> "AllSelection":
        """Returns a selection that includes all assets and their asset checks.

        Args:
            include_sources (bool): If True, then include all external assets.
        """
        return AllSelection(include_sources=include_sources)

    @public
    @staticmethod
    def all_asset_checks() -> "AllAssetCheckSelection":
        """Returns a selection that includes all asset checks."""
        return AllAssetCheckSelection()

    @public
    @staticmethod
    def assets(
        *assets_defs: Union[AssetsDefinition, CoercibleToAssetKey],
    ) -> "KeysAssetSelection":
        """Returns a selection that includes all of the provided assets and asset checks that target
        them.

        Args:
            *assets_defs (Union[AssetsDefinition, str, Sequence[str], AssetKey]): The assets to
                select.

        Examples:
            .. code-block:: python

                AssetSelection.assets(AssetKey(["a"]))

                AssetSelection.assets("a")

                AssetSelection.assets(AssetKey(["a"]), AssetKey(["b"]))

                AssetSelection.assets("a", "b")

                @asset
                def asset1():
                    ...

                AssetSelection.assets(asset1)

                asset_key_list = [AssetKey(["a"]), AssetKey(["b"])]
                AssetSelection.assets(*asset_key_list)
        """
        return KeysAssetSelection(selected_keys=asset_keys_from_defs_and_coercibles(assets_defs))

    @public
    @staticmethod
    @deprecated(
        breaking_version="2.0",
        additional_warn_text="Use AssetSelection.assets instead.",
    )
    def keys(*asset_keys: CoercibleToAssetKey) -> "KeysAssetSelection":
        """Returns a selection that includes assets with any of the provided keys and all asset
        checks that target them.

        Deprecated: use AssetSelection.assets instead.

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
    @beta_param(param="include_sources")
    def key_prefixes(
        *key_prefixes: CoercibleToAssetKeyPrefix, include_sources: bool = False
    ) -> "KeyPrefixesAssetSelection":
        """Returns a selection that includes assets that match any of the provided key prefixes and all the asset checks that target them.

        Args:
            include_sources (bool): If True, then include external assets matching the key prefix(es)
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
            selected_key_prefixes=_asset_key_prefixes,
            include_sources=include_sources,
        )

    @staticmethod
    @beta_param(param="include_sources")
    def key_substring(
        key_substring: str, include_sources: bool = False
    ) -> "KeySubstringAssetSelection":
        """Returns a selection that includes assets whose string representation contains the provided substring and all the asset checks that target it.

        Args:
            include_sources (bool): If True, then include external assets matching the substring
                in the selection.

        Examples:
            .. code-block:: python
              # match any asset key containing "bc"
              # e.g. AssetKey(["a", "bcd"]) would match, but not AssetKey(["ab", "cd"]).
              AssetSelection.key_substring("bc")
              # match any asset key containing "b/c"
              # e.g. AssetKey(["ab", "cd"]) would match.
              AssetSelection.key_substring("b/c")
        """
        return KeySubstringAssetSelection(
            selected_key_substring=key_substring, include_sources=include_sources
        )

    @public
    @staticmethod
    @beta_param(param="include_sources")
    def groups(*group_strs, include_sources: bool = False) -> "GroupsAssetSelection":
        """Returns a selection that includes materializable assets that belong to any of the
        provided groups and all the asset checks that target them.

        Args:
            include_sources (bool): If True, then include external assets matching the group in the
                selection.
        """
        check.tuple_param(group_strs, "group_strs", of_type=str)
        return GroupsAssetSelection(
            selected_groups=list(group_strs), include_sources=include_sources
        )

    @public
    @staticmethod
    @beta_param(param="include_sources")
    def tag(key: str, value: str, include_sources: bool = False) -> "AssetSelection":
        """Returns a selection that includes materializable assets that have the provided tag, and
        all the asset checks that target them.


        Args:
            include_sources (bool): If True, then include external assets matching the group in the
                selection.
        """
        return TagAssetSelection(key=key, value=value, include_sources=include_sources)

    @staticmethod
    def kind(kind: Optional[str], include_sources: bool = False) -> "AssetSelection":
        """Returns a selection that includes materializable assets that have the provided kind, and
        all the asset checks that target them.

        Args:
            kind (str): The kind to select.
            include_sources (bool): If True, then include external assets matching the kind in the
                selection.
        """
        return KindAssetSelection(kind_str=kind, include_sources=include_sources)

    @staticmethod
    @beta_param(param="include_sources")
    def tag_string(string: str, include_sources: bool = False) -> "AssetSelection":
        """Returns a selection that includes materializable assets that have the provided tag, and
        all the asset checks that target them.


        Args:
            include_sources (bool): If True, then include external assets matching the group in the
                selection.
        """
        split_by_equals_segments = string.split("=")
        if len(split_by_equals_segments) == 1:
            return TagAssetSelection(key=string, value="", include_sources=include_sources)
        elif len(split_by_equals_segments) == 2:
            key, value = split_by_equals_segments
            return TagAssetSelection(key=key, value=value, include_sources=include_sources)
        else:
            check.failed(f"Invalid tag selection string: {string}. Must have no more than one '='.")

    @staticmethod
    def owner(owner: Optional[str]) -> "AssetSelection":
        """Returns a selection that includes assets that have the provided owner, and all the
        asset checks that target them.

        Args:
            owner (str): The owner to select.
        """
        return OwnerAssetSelection(selected_owner=owner)

    @public
    @staticmethod
    def checks_for_assets(
        *assets_defs: Union[AssetsDefinition, CoercibleToAssetKey],
    ) -> "AssetChecksForAssetKeysSelection":
        """Returns a selection with the asset checks that target the provided assets.

        Args:
            *assets_defs (Union[AssetsDefinition, str, Sequence[str], AssetKey]): The assets to
                select checks for.
        """
        return AssetChecksForAssetKeysSelection(
            selected_asset_keys=asset_keys_from_defs_and_coercibles(assets_defs)
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

        Because mixed selections of external and materializable assets are currently not supported,
        keys corresponding to external assets will not be included as upstream of regular assets.

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

        Because mixed selections of external and materializable assets are currently not supported,
        keys corresponding to external assets will not be included as roots. To select external assets,
        use the `upstream_source_assets` method.
        """
        return RootsAssetSelection(child=self)

    @public
    def materializable(self) -> "MaterializableAssetSelection":
        """Given an asset selection, returns a new asset selection that contains all of the assets
        that are materializable. Removes any assets which are not materializable.
        """
        return MaterializableAssetSelection(child=self)

    @public
    @deprecated(breaking_version="2.0", additional_warn_text="Use AssetSelection.roots instead.")
    def sources(self) -> "RootsAssetSelection":
        """Given an asset selection, returns a new asset selection that contains all of the root
        assets within the original asset selection. Includes the asset checks targeting the returned assets.

        A root asset is a materializable asset that has no upstream dependencies within the asset
        selection. The root asset can have downstream dependencies outside of the asset selection.

        Because mixed selections of external and materializable assets are currently not supported,
        keys corresponding to external assets will not be included as roots. To select external assets,
        use the `upstream_source_assets` method.
        """
        return self.roots()

    @public
    def upstream_source_assets(self) -> "ParentSourcesAssetSelection":
        """Given an asset selection, returns a new asset selection that contains all of the external
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
        self, asset_graph: BaseAssetGraph, allow_missing: bool = False
    ) -> AbstractSet[AssetCheckKey]:
        """We don't need this method currently, but it makes things consistent with resolve_inner. Currently
        we don't store checks in the RemoteAssetGraph, so we only support AssetGraph.
        """
        return self.resolve_checks_inner(asset_graph, allow_missing=allow_missing)

    def resolve_checks_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetCheckKey]:
        """By default, resolve to checks that target the selected assets. This is overriden for particular selections."""
        asset_keys = self.resolve(asset_graph)
        return {handle for handle in asset_graph.asset_check_keys if handle.asset_key in asset_keys}

    @classmethod
    @beta_param(param="include_sources")
    def from_string(cls, string: str, include_sources=False) -> "AssetSelection":
        from dagster._core.definitions.antlr_asset_selection.antlr_asset_selection import (
            AntlrAssetSelectionParser,
        )

        try:
            return AntlrAssetSelectionParser(string, include_sources).asset_selection
        except:
            pass
        if string == "*":
            return cls.all()

        parts = parse_clause(string)
        if parts is not None:
            key_selection = cls.assets(parts.item_name)
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

        raise DagsterInvalidAssetSelectionError(f"Invalid selection string: {string}")

    @classmethod
    def from_coercible(cls, selection: CoercibleToAssetSelection) -> "AssetSelection":
        if isinstance(selection, str):
            return cls.from_string(selection)
        elif isinstance(selection, AssetSelection):
            return selection
        elif isinstance(selection, collections.abc.Sequence) and all(
            isinstance(el, str) for el in selection
        ):
            return reduce(operator.or_, [cls.from_string(cast("str", s)) for s in selection])
        elif isinstance(selection, collections.abc.Sequence) and all(
            isinstance(el, (AssetsDefinition, SourceAsset)) for el in selection
        ):
            return AssetSelection.assets(
                *(
                    key
                    for el in selection
                    for key in (
                        el.keys
                        if isinstance(el, AssetsDefinition)
                        else [cast("SourceAsset", el).key]
                    )
                )
            )
        elif isinstance(selection, collections.abc.Sequence) and all(
            isinstance(el, AssetKey) for el in selection
        ):
            return cls.assets(*cast("Sequence[AssetKey]", selection))
        else:
            raise DagsterError(
                "selection argument must be one of str, Sequence[str], Sequence[AssetKey],"
                " Sequence[AssetsDefinition], Sequence[SourceAsset], AssetSelection. Was"
                f" {type(selection)}."
            )

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return KeysAssetSelection(selected_keys=list(self.resolve(asset_graph)))

    def needs_parentheses_when_operand(self) -> bool:
        """When generating a string representation of an asset selection and this asset selection
        is an operand in a larger expression, whether it needs to be surrounded by parentheses.
        """
        return False

    def operand_to_selection_str(self) -> str:
        """Returns a string representation of the selection when it is a child of a boolean expression,
        for example, in an `AndAssetSelection` or `OrAssetSelection`. The main difference from `to_selection_str`
        is that this method may include additional parentheses around the selection to ensure that the
        expression is parsed correctly.
        """
        return (
            f"({self.to_selection_str()})"
            if self.needs_parentheses_when_operand()
            else self.to_selection_str()
        )

    def to_selection_str(self) -> str:
        """Returns an Antlr string representation of the selection that can be parsed by `from_string`."""
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support conversion to a string."
        )

    def __str__(self) -> str:
        # Attempt to use the to-Antlr-selection-string method if it's implemented,
        # otherwise fall back to the default Python string representation
        try:
            return self.to_selection_str()
        except NotImplementedError:
            return super().__str__()


@whitelist_for_serdes
@record
class AllSelection(AssetSelection):
    include_sources: Optional[bool] = None

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return (
            asset_graph.get_all_asset_keys()
            if self.include_sources
            else asset_graph.materializable_asset_keys
        )

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self

    def to_selection_str(self) -> str:
        return "*"


@whitelist_for_serdes
@record
class AllAssetCheckSelection(AssetSelection):
    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return set()

    def resolve_checks_inner(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, asset_graph: AssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetCheckKey]:
        return asset_graph.asset_check_keys

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self


@whitelist_for_serdes
@record
class AssetChecksForAssetKeysSelection(AssetSelection):
    selected_asset_keys: Sequence[AssetKey]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return set()

    def resolve_checks_inner(  # pyright: ignore[reportIncompatibleMethodOverride]
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
@record
class AssetCheckKeysSelection(AssetSelection):
    selected_asset_check_keys: Sequence[AssetCheckKey]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return set()

    def resolve_checks_inner(  # pyright: ignore[reportIncompatibleMethodOverride]
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


@record
class OperandListAssetSelection(AssetSelection):
    """Superclass for classes like `AndAssetSelection` and `OrAssetSelection` that operate on
    a list of sub-AssetSelections.
    """

    operands: Sequence[AssetSelection]

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return copy(
            self,
            operands=[
                operand.to_serializable_asset_selection(asset_graph) for operand in self.operands
            ],
        )

    def __eq__(self, other):
        if not isinstance(other, OperandListAssetSelection):
            return False

        num_operands = len(self.operands)
        return len(other.operands) == num_operands and all(
            self.operands[i] == other.operands[i] for i in range(num_operands)
        )

    def needs_parentheses_when_operand(self) -> bool:
        return True


@whitelist_for_serdes
class AndAssetSelection(OperandListAssetSelection):
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

    def resolve_checks_inner(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, asset_graph: AssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetCheckKey]:
        return reduce(
            operator.and_,
            (
                selection.resolve_checks_inner(asset_graph, allow_missing=allow_missing)
                for selection in self.operands
            ),
        )

    def to_selection_str(self) -> str:
        return " and ".join(f"{operand.operand_to_selection_str()}" for operand in self.operands)


@whitelist_for_serdes
class OrAssetSelection(OperandListAssetSelection):
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

    def resolve_checks_inner(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, asset_graph: AssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetCheckKey]:
        return reduce(
            operator.or_,
            (
                selection.resolve_checks_inner(asset_graph, allow_missing=allow_missing)
                for selection in self.operands
            ),
        )

    def to_selection_str(self) -> str:
        return " or ".join(f"{operand.operand_to_selection_str()}" for operand in self.operands)


@whitelist_for_serdes
@record
class SubtractAssetSelection(AssetSelection):
    left: AssetSelection
    right: AssetSelection

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return self.left.resolve_inner(
            asset_graph, allow_missing=allow_missing
        ) - self.right.resolve_inner(asset_graph, allow_missing=allow_missing)

    def resolve_checks_inner(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, asset_graph: AssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetCheckKey]:
        return self.left.resolve_checks_inner(
            asset_graph, allow_missing=allow_missing
        ) - self.right.resolve_checks_inner(asset_graph, allow_missing=allow_missing)

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return copy(
            self,
            left=self.left.to_serializable_asset_selection(asset_graph),
            right=self.right.to_serializable_asset_selection(asset_graph),
        )

    def needs_parentheses_when_operand(self) -> bool:
        return True

    def to_selection_str(self) -> str:
        if isinstance(self.left, AllSelection):
            return f"not {self.right.to_selection_str()}"
        return f"{self.left.operand_to_selection_str()} and not {self.right.operand_to_selection_str()}"


@record
class ChainedAssetSelection(AssetSelection):
    """Superclass for AssetSelection classes that contain a single child AssetSelection and are
    resolved by applying some operation to the result of resolving the child selection.
    """

    child: AssetSelection

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return copy(self, child=self.child.to_serializable_asset_selection(asset_graph))


@whitelist_for_serdes
class SinksAssetSelection(ChainedAssetSelection):
    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph, allow_missing=allow_missing)
        return fetch_sinks(asset_graph.asset_dep_graph, selection)

    def to_selection_str(self) -> str:
        return f"sinks({self.child.to_selection_str()})"


@whitelist_for_serdes
class RequiredNeighborsAssetSelection(ChainedAssetSelection):
    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph, allow_missing=allow_missing)
        output = set(selection)
        for asset_key in selection:
            output.update(asset_graph.get(asset_key).execution_set_asset_keys)
        return output


@whitelist_for_serdes
class RootsAssetSelection(ChainedAssetSelection):
    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph, allow_missing=allow_missing)
        return fetch_sources(asset_graph, selection)

    def to_selection_str(self) -> str:
        return f"roots({self.child.to_selection_str()})"


@whitelist_for_serdes
class MaterializableAssetSelection(ChainedAssetSelection):
    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return {
            asset_key
            for asset_key in self.child.resolve_inner(asset_graph, allow_missing=allow_missing)
            if cast("BaseAssetNode", asset_graph.get(asset_key)).is_materializable
        }


@whitelist_for_serdes
@record
class DownstreamAssetSelection(ChainedAssetSelection):
    depth: Optional[int]
    include_self: bool

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph, allow_missing=allow_missing)
        return operator.sub(
            (
                selection
                | fetch_connected(
                    selection, asset_graph.asset_dep_graph, direction="downstream", depth=self.depth
                )
            ),
            selection if not self.include_self else set(),
        )

    def to_selection_str(self) -> str:
        if self.depth is None:
            base = f"{self.child.operand_to_selection_str()}+"
        elif self.depth == 0:
            base = self.child.operand_to_selection_str()
        else:
            base = f"{self.child.operand_to_selection_str()}{'+'}{self.depth}"

        if self.include_self:
            return base
        else:
            return f"{base} and not {self.child.operand_to_selection_str()}"


@whitelist_for_serdes
@record
class GroupsAssetSelection(AssetSelection):
    selected_groups: Sequence[str]
    include_sources: bool

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return {
            key
            for group in self.selected_groups
            for key in asset_graph.asset_keys_for_group(
                group, require_materializable=not self.include_sources
            )
        }

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self

    def needs_parentheses_when_operand(self) -> bool:
        return len(self.selected_groups) > 1

    def to_selection_str(self) -> str:
        if len(self.selected_groups) == 0:
            return "group:<null>"
        return " or ".join(f'group:"{group}"' for group in self.selected_groups)


@whitelist_for_serdes
@record
class KindAssetSelection(AssetSelection):
    include_sources: bool
    kind_str: Optional[str]

    def resolve_inner(
        self,
        asset_graph: BaseAssetGraph,
        allow_missing: bool,
    ) -> AbstractSet[AssetKey]:
        base_set = (
            asset_graph.get_all_asset_keys()
            if self.include_sources
            else asset_graph.materializable_asset_keys
        )

        if self.kind_str is None:
            return {
                key
                for key in base_set
                if (
                    not any(
                        tag_key.startswith(KIND_PREFIX)
                        for tag_key in (asset_graph.get(key).tags or {})
                    )
                )
            }
        else:
            return {
                key
                for key in base_set
                if asset_graph.get(key).tags.get(f"{KIND_PREFIX}{self.kind_str}") is not None
            }

    def to_selection_str(self) -> str:
        if self.kind_str is None:
            return "kind:<null>"
        return f'kind:"{self.kind_str}"'


@whitelist_for_serdes
@record
class TagAssetSelection(AssetSelection):
    key: str
    value: str
    include_sources: bool

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        base_set = (
            asset_graph.get_all_asset_keys()
            if self.include_sources
            else asset_graph.materializable_asset_keys
        )

        return {key for key in base_set if asset_graph.get(key).tags.get(self.key) == self.value}

    def to_selection_str(self) -> str:
        if self.value:
            return f'tag:"{self.key}"="{self.value}"'
        else:
            return f'tag:"{self.key}"'


@whitelist_for_serdes
@record
class OwnerAssetSelection(AssetSelection):
    selected_owner: Optional[str]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        return {
            key
            for key in asset_graph.get_all_asset_keys()
            if self.selected_owner in asset_graph.get(key).owners
        }

    def to_selection_str(self) -> str:
        if self.selected_owner is None:
            return "owner:<null>"
        return f'owner:"{self.selected_owner}"'


@whitelist_for_serdes
@record
class CodeLocationAssetSelection(AssetSelection):
    """Used to represent a UI asset selection by project. This should not be resolved against
    an in-process asset graph.
    """

    selected_code_location: Optional[str]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        from dagster._core.definitions.assets.graph.remote_asset_graph import RemoteAssetGraph

        check.invariant(
            isinstance(asset_graph, RemoteAssetGraph),
            "code_location: cannot be used to select assets in user code.",
        )

        asset_graph = cast("RemoteAssetGraph", asset_graph)

        location_name = self.selected_code_location

        # If the code location is in the form of "repo_name@location_name", we need to
        # split the string and filter the asset keys based on the repository and location name.
        if location_name and "@" in location_name:
            asset_keys = set()
            location = location_name.split("@")[1]
            name = location_name.split("@")[0]
            for asset_key in asset_graph.remote_asset_nodes_by_key:
                repo_handle = (
                    asset_graph.get(asset_key)
                    .resolve_to_singular_repo_scoped_node()
                    .repository_handle
                )
                if repo_handle.location_name == location and repo_handle.repository_name == name:
                    asset_keys.add(asset_key)
            return asset_keys

        # Otherwise, filter only by location name
        return {
            key
            for key in asset_graph.remote_asset_nodes_by_key
            if (
                asset_graph.get(key)
                .resolve_to_singular_repo_scoped_node()
                .repository_handle.location_name
            )
            == self.selected_code_location
        }

    def to_selection_str(self) -> str:
        if self.selected_code_location is None:
            return "code_location:<null>"
        return f'code_location:"{self.selected_code_location}"'


@whitelist_for_serdes
@record
class ColumnAssetSelection(AssetSelection):
    """Used to represent a UI asset selection by column. This should not be resolved against
    an in-process asset graph.
    """

    selected_column: Optional[str]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        """This should not be invoked in user code."""
        raise NotImplementedError

    def to_selection_str(self) -> str:
        if self.selected_column is None:
            return "column:<null>"
        return f'column:"{self.selected_column}"'


@whitelist_for_serdes
@record
class TableNameAssetSelection(AssetSelection):
    """Used to represent a UI asset selection by table name. This should not be resolved against
    an in-process asset graph.
    """

    selected_table_name: Optional[str]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        """This should not be invoked in user code."""
        raise NotImplementedError

    def to_selection_str(self) -> str:
        if self.selected_table_name is None:
            return "table_name:<null>"
        return f'table_name:"{self.selected_table_name}"'


@whitelist_for_serdes
@record
class ColumnTagAssetSelection(AssetSelection):
    """Used to represent a UI asset selection by column tag. This should not be resolved against
    an in-process asset graph.
    """

    key: str
    value: str

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        """This should not be invoked in user code."""
        raise NotImplementedError

    def to_selection_str(self) -> str:
        if self.value:
            return f'column_tag:"{self.key}"="{self.value}"'
        else:
            return f'column_tag:"{self.key}"'


@whitelist_for_serdes
@record
class ChangedInBranchAssetSelection(AssetSelection):
    """Used to represent a UI asset selection by changed in branch metadata. This should not be resolved against
    an in-process asset graph.
    """

    selected_changed_in_branch: Optional[str]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        """This should not be invoked in user code."""
        raise NotImplementedError

    def to_selection_str(self) -> str:
        if self.selected_changed_in_branch is None:
            return "changed_in_branch:<null>"
        return f'changed_in_branch:"{self.selected_changed_in_branch}"'


@whitelist_for_serdes
@record
class StatusAssetSelection(AssetSelection):
    selected_status: Optional[str]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        """This should not be invoked in user code."""
        raise NotImplementedError

    def to_selection_str(self) -> str:
        if self.selected_status is None:
            return "status:<null>"
        return f'status:"{self.selected_status}"'


@whitelist_for_serdes
@record
class KeysAssetSelection(AssetSelection):
    selected_keys: Sequence[AssetKey]

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        specified_keys = set(self.selected_keys)
        missing_keys = {key for key in specified_keys if not asset_graph.has(key)}

        if not allow_missing:
            # Arbitrary limit to avoid huge error messages
            keys_to_suggest = list(missing_keys)[:4]
            suggestions = ""
            for invalid_key in keys_to_suggest:
                similar_names = resolve_similar_asset_names(
                    invalid_key, asset_graph.get_all_asset_keys()
                )
                if similar_names:
                    # Arbitrarily limit to 10 similar names to avoid a huge error message
                    subset_similar_names = similar_names[:10]
                    similar_to_string = ", ".join(
                        similar.to_string() for similar in subset_similar_names
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

    def to_selection_str(self) -> str:
        return " or ".join(f'key:"{x.to_user_string()}"' for x in self.selected_keys)


@whitelist_for_serdes
@record
class KeyPrefixesAssetSelection(AssetSelection):
    selected_key_prefixes: Sequence[Sequence[str]]
    include_sources: bool

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        base_set = (
            asset_graph.get_all_asset_keys()
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


@whitelist_for_serdes
@record
class KeySubstringAssetSelection(AssetSelection):
    selected_key_substring: str
    include_sources: bool

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        base_set = (
            asset_graph.get_all_asset_keys()
            if self.include_sources
            else asset_graph.materializable_asset_keys
        )
        return {key for key in base_set if self.selected_key_substring in key.to_user_string()}

    def to_serializable_asset_selection(self, asset_graph: BaseAssetGraph) -> "AssetSelection":
        return self

    def to_selection_str(self) -> str:
        return f'key_substring:"{self.selected_key_substring}"'


@whitelist_for_serdes
@record
class KeyWildCardAssetSelection(AssetSelection):
    selected_key_wildcard: str

    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        regex = re.compile("^" + re.escape(self.selected_key_wildcard).replace("\\*", ".*") + "$")
        return {
            key for key in asset_graph.get_all_asset_keys() if regex.match(key.to_user_string())
        }

    def to_selection_str(self) -> str:
        return f'key:"{self.selected_key_wildcard}"'


def _fetch_all_upstream(
    selection: AbstractSet[AssetKey],
    asset_graph: BaseAssetGraph,
    depth: Optional[int] = None,
    include_self: bool = True,
) -> AbstractSet[AssetKey]:
    return operator.sub(
        (
            selection
            | fetch_connected(
                selection, asset_graph.asset_dep_graph, direction="upstream", depth=depth
            )
        ),
        selection if not include_self else set(),
    )


@whitelist_for_serdes
@record
class UpstreamAssetSelection(ChainedAssetSelection):
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

    def to_selection_str(self) -> str:
        if self.depth is None:
            base = f"+{self.child.operand_to_selection_str()}"
        elif self.depth == 0:
            base = self.child.operand_to_selection_str()
        else:
            base = f"{self.depth}{'+'}{self.child.operand_to_selection_str()}"

        if self.include_self:
            return base
        else:
            return f"{base} and not {self.child.operand_to_selection_str()}"


@whitelist_for_serdes
class ParentSourcesAssetSelection(ChainedAssetSelection):
    def resolve_inner(
        self, asset_graph: BaseAssetGraph, allow_missing: bool
    ) -> AbstractSet[AssetKey]:
        selection = self.child.resolve_inner(asset_graph, allow_missing=allow_missing)
        if len(selection) == 0:
            return selection
        all_upstream = _fetch_all_upstream(selection, asset_graph)
        return {key for key in all_upstream if key in asset_graph.external_asset_keys}
