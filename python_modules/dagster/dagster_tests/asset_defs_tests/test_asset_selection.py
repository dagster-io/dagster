import operator
from collections.abc import Iterable
from functools import reduce
from inspect import isclass
from typing import AbstractSet, Union  # noqa: UP035

import dagster as dg
import pytest
from dagster._core.definitions import AssetSelection
from dagster._core.definitions.asset_selection import (
    AllAssetCheckSelection,
    AllSelection,
    AndAssetSelection,
    AssetCheckKeysSelection,
    AssetChecksForAssetKeysSelection,
    ChangedInBranchAssetSelection,
    CodeLocationAssetSelection,
    ColumnAssetSelection,
    ColumnTagAssetSelection,
    DagsterInvalidAssetSelectionError,
    DownstreamAssetSelection,
    GroupsAssetSelection,
    KeyPrefixesAssetSelection,
    KeysAssetSelection,
    KeyWildCardAssetSelection,
    OrAssetSelection,
    ParentSourcesAssetSelection,
    RequiredNeighborsAssetSelection,
    RootsAssetSelection,
    SinksAssetSelection,
    StatusAssetSelection,
    SubtractAssetSelection,
    TableNameAssetSelection,
    UpstreamAssetSelection,
)
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.selector.subset_selector import MAX_NUM
from dagster_shared.check import CheckError
from dagster_shared.serdes.serdes import _WHITELIST_MAP
from typing_extensions import TypeAlias

earth = dg.SourceAsset(["celestial", "earth"], group_name="planets")


@dg.asset(ins={"earth": dg.AssetIn(key=dg.AssetKey(["celestial", "earth"]))}, group_name="ladies")
def alice(earth):
    return "alice"


@dg.asset(group_name="gentlemen")
def bob(alice):
    return "bob"


@dg.asset(group_name="ladies")
def candace(alice):
    return "candace"


@dg.asset(group_name="gentlemen")
def danny(candace):
    return "danny"


@dg.asset(group_name="gentlemen")
def edgar(danny):
    return "edgar"


@dg.asset(group_name="ladies")
def fiona(danny):
    return "fiona"


@dg.asset(group_name="gentlemen")
def george(bob, fiona):
    return "george"


@dg.multi_asset(
    group_name="robots",
    outs={
        "rosie": dg.AssetOut(),
        "r2d2": dg.AssetOut(),
        "walle": dg.AssetOut(),
    },
)
def robots() -> tuple[str, str, str]:
    return "rosie", "r2d2", "walle"


@dg.multi_asset(
    group_name="aliens",
    outs={
        "zorg": dg.AssetOut(),
        "zapp": dg.AssetOut(),
        "zort": dg.AssetOut(),
    },
    can_subset=True,
)
def aliens() -> tuple[str, str, str]:
    return "zorg", "zapp", "zort"


@dg.asset(key_prefix="animals")
def zebra():
    return "zebra"


_AssetList: TypeAlias = Iterable[Union[dg.AssetsDefinition, dg.SourceAsset]]


@pytest.fixture
def all_assets() -> _AssetList:
    return [
        earth,
        alice,
        bob,
        candace,
        danny,
        edgar,
        fiona,
        george,
        robots,
        aliens,
        zebra,
    ]


def _asset_keys_of(assets_defs: _AssetList) -> AbstractSet[dg.AssetKey]:
    return reduce(
        operator.or_,
        [
            item.keys if isinstance(item, dg.AssetsDefinition) else {item.key}
            for item in assets_defs
        ],
        set(),
    )


def test_asset_selection_all(all_assets: _AssetList):
    sel = AssetSelection.all()
    assert sel.resolve(all_assets) == _asset_keys_of(all_assets) - {earth.key}

    sel_include_sources = AssetSelection.all(include_sources=True)
    assert sel_include_sources.resolve(all_assets) == _asset_keys_of(all_assets)


def test_asset_selection_and(all_assets: _AssetList):
    sel = AssetSelection.assets("alice", "bob") & AssetSelection.assets("bob", "candace")
    assert sel.resolve(all_assets) == _asset_keys_of({bob})


def test_asset_selection_downstream(all_assets: _AssetList):
    sel_depth_inf = AssetSelection.assets("candace").downstream()
    assert sel_depth_inf.resolve(all_assets) == _asset_keys_of(
        {candace, danny, edgar, fiona, george}
    )

    sel_depth_1 = AssetSelection.assets("candace").downstream(depth=1)
    assert sel_depth_1.resolve(all_assets) == _asset_keys_of({candace, danny})


def test_asset_selection_groups(all_assets: _AssetList):
    # does not include source assets by default
    sel = AssetSelection.groups("ladies", "planets")
    assert sel.resolve(all_assets) == _asset_keys_of({alice, candace, fiona})

    # includes source assets if flag set
    sel = AssetSelection.groups("planets", include_sources=True)
    assert sel.resolve(all_assets) == {earth.key}


def test_asset_selection_keys(all_assets: _AssetList):
    sel = AssetSelection.keys(dg.AssetKey("alice"), dg.AssetKey("bob"))
    assert sel.resolve(all_assets) == _asset_keys_of({alice, bob})
    assert str(sel) == 'key:"alice" or key:"bob"'

    sel = AssetSelection.keys("alice", "bob")
    assert sel.resolve(all_assets) == _asset_keys_of({alice, bob})

    sel = AssetSelection.keys("alice", "bob", "carol", "dave")
    assert str(sel) == 'key:"alice" or key:"bob" or key:"carol" or key:"dave"'

    sel = AssetSelection.keys("animals/zebra")
    assert sel.resolve(all_assets) == _asset_keys_of({zebra})


def test_asset_selection_key_prefixes(all_assets: _AssetList):
    sel = AssetSelection.key_prefixes("animals")
    assert sel.resolve(all_assets) == _asset_keys_of({zebra})

    sel = AssetSelection.key_prefixes("plants")
    assert sel.resolve(all_assets) == _asset_keys_of(set())

    # does not include source assets by default
    sel = AssetSelection.key_prefixes("celestial")
    assert sel.resolve(all_assets) == set()

    # includes source assets if flag set
    sel = AssetSelection.key_prefixes("celestial", include_sources=True)
    assert sel.resolve(all_assets) == {earth.key}


def test_asset_selection_key_substring(all_assets: _AssetList):
    sel = AssetSelection.key_substring("alice")
    assert sel.resolve(all_assets) == _asset_keys_of({alice})

    sel = AssetSelection.key_substring("ls/ze")
    assert sel.resolve(all_assets) == _asset_keys_of({zebra})

    # does not include source assets by default
    sel = AssetSelection.key_substring("celestial")
    assert sel.resolve(all_assets) == set()

    # includes source assets if flag set
    sel = AssetSelection.key_substring("celestial/e", include_sources=True)
    assert sel.resolve(all_assets) == {earth.key}


def test_select_source_asset_keys():
    a = dg.SourceAsset("a")
    selection = AssetSelection.keys(a.key)
    assert selection.resolve([a]) == {a.key}


def test_asset_selection_assets(all_assets: _AssetList):
    sel = AssetSelection.assets(alice, bob)
    assert sel.resolve(all_assets) == _asset_keys_of({alice, bob})


def test_asset_selection_or(all_assets: _AssetList):
    sel = AssetSelection.assets("alice", "bob") | AssetSelection.assets("bob", "candace")
    assert sel.resolve(all_assets) == _asset_keys_of({alice, bob, candace})


def test_asset_selection_subtraction(all_assets: _AssetList):
    sel = AssetSelection.assets("alice", "bob") - AssetSelection.assets("bob", "candace")
    assert sel.resolve(all_assets) == _asset_keys_of({alice})

    sel = AssetSelection.groups("ladies") - AssetSelection.groups("gentlemen")
    assert sel.resolve(all_assets) == _asset_keys_of({alice, candace, fiona})

    sel = (AssetSelection.groups("ladies") | AssetSelection.assets("bob")) - AssetSelection.groups(
        "ladies"
    )
    assert sel.resolve(all_assets) == _asset_keys_of({bob})


def test_asset_selection_nothing(all_assets: _AssetList):
    sel = AssetSelection.assets()
    assert sel.resolve(all_assets) == set()

    sel = AssetSelection.groups("ladies") - AssetSelection.groups("ladies")
    assert sel.resolve(all_assets) == set()

    sel = AssetSelection.assets("alice", "bob") - AssetSelection.assets("alice", "bob")
    assert sel.resolve(all_assets) == set()


def test_asset_selection_sinks(all_assets: _AssetList):
    sel = AssetSelection.assets("alice", "bob").sinks()
    assert sel.resolve(all_assets) == _asset_keys_of({bob})

    sel = AssetSelection.all().sinks()
    assert sel.resolve(all_assets) == _asset_keys_of({edgar, george, robots, aliens, zebra})

    sel = AssetSelection.groups("ladies").sinks()
    # fiona is a sink because it has no downstream dependencies within the "ladies" group
    # candace is not a sink because it is an upstream dependency of fiona
    assert sel.resolve(all_assets) == _asset_keys_of({fiona})


def test_asset_selection_required_multi_asset_neighbors(all_assets: _AssetList):
    # no effect for single assets
    sel = AssetSelection.assets("george").required_multi_asset_neighbors()
    assert sel.resolve(all_assets) == _asset_keys_of({george})

    # robots must all be materialized together, so they are expanded
    # from required_multi_asset_neighbors
    sel = AssetSelection.assets("rosie").required_multi_asset_neighbors()
    assert sel.resolve(all_assets) == _asset_keys_of({robots})

    sel = AssetSelection.assets("alice", "bob", "walle").required_multi_asset_neighbors()
    assert sel.resolve(all_assets) == _asset_keys_of({alice, bob, robots})

    # aliens are subsettable, so no expansion from required_multi_asset_neighbors
    sel = AssetSelection.assets("zorg").required_multi_asset_neighbors()
    assert sel.resolve(all_assets) == {dg.AssetKey("zorg")}


def test_asset_selection_upstream(all_assets: _AssetList):
    sel_depth_inf = AssetSelection.assets("george").upstream()
    assert sel_depth_inf.resolve(all_assets) == _asset_keys_of(
        {alice, bob, candace, danny, fiona, george}
    )

    sel_depth_1 = AssetSelection.assets("george").upstream(depth=1)
    assert sel_depth_1.resolve(all_assets) == _asset_keys_of({bob, fiona, george})


def test_downstream_include_self(all_assets: _AssetList):
    selection = AssetSelection.assets("candace").downstream(include_self=False)
    assert selection.resolve(all_assets) == _asset_keys_of({danny, edgar, fiona, george})

    selection = AssetSelection.groups("gentlemen").downstream(include_self=False)
    assert selection.resolve(all_assets) == _asset_keys_of({fiona})

    selection = AssetSelection.groups("ladies").downstream(include_self=False)
    assert selection.resolve(all_assets) == _asset_keys_of({george, danny, bob, edgar})


def test_upstream_include_self(all_assets: _AssetList):
    selection = AssetSelection.assets("george").upstream(include_self=False)
    assert selection.resolve(all_assets) == _asset_keys_of({danny, fiona, alice, bob, candace})

    selection = AssetSelection.groups("gentlemen").upstream(include_self=False)
    assert selection.resolve(all_assets) == _asset_keys_of({fiona, alice, candace})

    selection = AssetSelection.groups("ladies").upstream(include_self=False)
    assert selection.resolve(all_assets) == _asset_keys_of({danny})


def test_asset_selection_source_assets(all_assets: _AssetList):
    selection = AssetSelection.assets("alice").upstream_source_assets()
    assert selection.resolve(all_assets) == {earth.key}

    selection = AssetSelection.assets("george").upstream_source_assets()
    assert selection.resolve(all_assets) == {earth.key}


def test_roots():
    @dg.asset
    def a():
        pass

    @dg.asset
    def b(a):
        pass

    @dg.asset
    def c(b):
        pass

    assert AssetSelection.assets("a", "b", "c").roots().resolve([a, b, c]) == {a.key}
    assert AssetSelection.assets("a", "c").roots().resolve([a, b, c]) == {a.key}
    assert AssetSelection.assets("b", "c").roots().resolve([a, b, c]) == {b.key}
    assert AssetSelection.assets("c").roots().resolve([a, b, c]) == {c.key}


def test_materializable() -> None:
    source_upstream = dg.SourceAsset("source_upstream")

    @dg.observable_source_asset
    def obs_source_upstream() -> None:
        pass

    @dg.asset
    def b(source_upstream, obs_source_upstream):
        pass

    @dg.asset
    def c(b):
        pass

    assert AssetSelection.assets("source_upstream", "obs_source_upstream", "b", "c").resolve(
        [
            source_upstream,
            obs_source_upstream,
            b,
            c,
        ]
    ) == {
        source_upstream.key,
        obs_source_upstream.key,
        b.key,
        c.key,
    }
    assert AssetSelection.assets(
        "source_upstream", "obs_source_upstream", "b", "c"
    ).materializable().resolve(
        [
            source_upstream,
            obs_source_upstream,
            b,
            c,
        ]
    ) == {
        b.key,
        c.key,
    }


def test_sources():
    @dg.asset
    def a():
        pass

    @dg.asset
    def b(a):
        pass

    @dg.asset
    def c(b):
        pass

    with pytest.warns(DeprecationWarning):
        assert AssetSelection.assets("a", "b", "c").sources().resolve([a, b, c]) == {a.key}


@pytest.mark.parametrize(
    "partitions_def,partition_mapping",
    [
        (
            dg.DailyPartitionsDefinition(start_date="2020-01-01"),
            dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
        ),
        (
            dg.MultiPartitionsDefinition(
                {
                    "time": dg.DailyPartitionsDefinition(start_date="2020-01-01"),
                    "abc": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                }
            ),
            dg.MultiPartitionMapping(
                {
                    "time": dg.DimensionPartitionMapping(
                        "time",
                        dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
                    ),
                    "abc": dg.DimensionPartitionMapping("abc", dg.IdentityPartitionMapping()),
                }
            ),
        ),
    ],
)
def test_self_dep(partitions_def, partition_mapping):
    @dg.asset(
        partitions_def=partitions_def,
        ins={"a": dg.AssetIn(partition_mapping=partition_mapping)},
    )
    def a(a): ...

    assert AssetSelection.assets("a").resolve([a]) == {a.key}
    assert AssetSelection.assets("a").upstream().resolve([a]) == {a.key}
    assert AssetSelection.assets("a").upstream(include_self=False).resolve([a]) == set()
    assert AssetSelection.assets("a").sources().resolve([a]) == {a.key}
    assert AssetSelection.assets("a").sinks().resolve([a]) == {a.key}


def test_from_coercible_multi_asset():
    @dg.multi_asset(outs={"asset1": dg.AssetOut(), "asset2": dg.AssetOut()})
    def my_multi_asset(): ...

    @dg.asset
    def other_asset(): ...

    assert (
        AssetSelection.from_coercible([my_multi_asset]).resolve([my_multi_asset, other_asset])
        == my_multi_asset.keys
    )


def test_from_coercible_tuple():
    @dg.asset
    def foo(): ...

    @dg.asset
    def bar(): ...

    assert AssetSelection.from_coercible((foo, bar)).resolve([foo, bar]) == {
        dg.AssetKey("foo"),
        dg.AssetKey("bar"),
    }


def test_multi_operand_selection():
    foo = AssetSelection.assets("foo")
    bar = AssetSelection.assets("bar")
    baz = AssetSelection.assets("baz")

    assert foo & bar & baz == AndAssetSelection(operands=[foo, bar, baz])
    assert (foo & bar) & baz == AndAssetSelection(operands=[foo, bar, baz])
    assert foo & (bar & baz) == AndAssetSelection(operands=[foo, bar, baz])
    assert foo | bar | baz == OrAssetSelection(operands=[foo, bar, baz])
    assert (foo | bar) | baz == OrAssetSelection(operands=[foo, bar, baz])
    assert foo | (bar | baz) == OrAssetSelection(operands=[foo, bar, baz])

    assert (foo & bar) | baz == OrAssetSelection(
        operands=[AndAssetSelection(operands=[foo, bar]), baz]
    )
    assert foo & (bar | baz) == AndAssetSelection(
        operands=[foo, OrAssetSelection(operands=[bar, baz])]
    )
    assert (foo | bar) & baz == AndAssetSelection(
        operands=[OrAssetSelection(operands=[foo, bar]), baz]
    )
    assert foo | (bar & baz) == OrAssetSelection(
        operands=[foo, AndAssetSelection(operands=[bar, baz])]
    )


def test_asset_selection_type_checking():
    valid_asset_selection = AssetSelection.assets("foo")
    valid_asset_selection_sequence = [valid_asset_selection]
    valid_asset_key = dg.AssetKey("bar")
    valid_asset_key_sequence = [valid_asset_key]
    valid_string_sequence = ["string"]
    valid_string_sequence_sequence = [valid_string_sequence]
    valid_asset_check_key = dg.AssetCheckKey(asset_key=valid_asset_key, name="test_name")
    valid_asset_check_key_sequence = [valid_asset_check_key]

    invalid_argument = "invalid_argument"

    with pytest.raises(CheckError):
        AssetChecksForAssetKeysSelection(selected_asset_keys=invalid_argument)  # pyright: ignore[reportArgumentType]
    test = AssetChecksForAssetKeysSelection(selected_asset_keys=valid_asset_key_sequence)
    assert isinstance(test, AssetChecksForAssetKeysSelection)

    with pytest.raises(CheckError):
        AssetCheckKeysSelection(selected_asset_check_keys=invalid_argument)  # pyright: ignore[reportArgumentType]
    test = AssetCheckKeysSelection(selected_asset_check_keys=valid_asset_check_key_sequence)
    assert isinstance(test, AssetCheckKeysSelection)

    with pytest.raises(CheckError):
        AndAssetSelection(operands=invalid_argument)  # pyright: ignore[reportArgumentType]
    test = AndAssetSelection(operands=valid_asset_selection_sequence)
    assert isinstance(test, AndAssetSelection)

    with pytest.raises(CheckError):
        OrAssetSelection(operands=invalid_argument)  # pyright: ignore[reportArgumentType]
    test = OrAssetSelection(operands=valid_asset_selection_sequence)
    assert isinstance(test, OrAssetSelection)

    with pytest.raises(CheckError):
        SubtractAssetSelection(left=invalid_argument, right=invalid_argument)  # pyright: ignore[reportArgumentType]
    test = SubtractAssetSelection(left=valid_asset_selection, right=valid_asset_selection)
    assert isinstance(test, SubtractAssetSelection)

    with pytest.raises(CheckError):
        SinksAssetSelection(child=invalid_argument)  # pyright: ignore[reportArgumentType]
    test = SinksAssetSelection(child=valid_asset_selection)
    assert isinstance(test, SinksAssetSelection)

    with pytest.raises(CheckError):
        RequiredNeighborsAssetSelection(child=invalid_argument)  # pyright: ignore[reportArgumentType]
    test = RequiredNeighborsAssetSelection(child=valid_asset_selection)
    assert isinstance(test, RequiredNeighborsAssetSelection)

    with pytest.raises(CheckError):
        RootsAssetSelection(child=invalid_argument)  # pyright: ignore[reportArgumentType]
    test = RootsAssetSelection(child=valid_asset_selection)
    assert isinstance(test, RootsAssetSelection)

    with pytest.raises(CheckError):
        DownstreamAssetSelection(child=invalid_argument, depth=0, include_self=False)  # pyright: ignore[reportArgumentType]
    test = DownstreamAssetSelection(child=valid_asset_selection, depth=0, include_self=False)
    assert isinstance(test, DownstreamAssetSelection)

    test = GroupsAssetSelection(selected_groups=valid_string_sequence, include_sources=False)
    assert isinstance(test, GroupsAssetSelection)

    with pytest.raises(CheckError):
        KeysAssetSelection(selected_keys=invalid_argument)  # pyright: ignore[reportArgumentType]
    test = KeysAssetSelection(selected_keys=valid_asset_key_sequence)
    assert isinstance(test, KeysAssetSelection)

    with pytest.raises(CheckError):
        GroupsAssetSelection(selected_groups=invalid_argument, include_sources=False)

    with pytest.raises(CheckError):
        KeyPrefixesAssetSelection(selected_key_prefixes=invalid_argument, include_sources=False)

    test = KeyPrefixesAssetSelection(
        selected_key_prefixes=valid_string_sequence_sequence, include_sources=False
    )
    assert isinstance(test, KeyPrefixesAssetSelection)

    with pytest.raises(CheckError):
        UpstreamAssetSelection(child=invalid_argument, depth=0, include_self=False)  # pyright: ignore[reportArgumentType]
    test = UpstreamAssetSelection(child=valid_asset_selection, depth=0, include_self=False)
    assert isinstance(test, UpstreamAssetSelection)

    with pytest.raises(CheckError):
        ParentSourcesAssetSelection(child=invalid_argument)  # pyright: ignore[reportArgumentType]
    test = ParentSourcesAssetSelection(child=valid_asset_selection)
    assert isinstance(test, ParentSourcesAssetSelection)


def test_all_asset_selection_subclasses_serializable():
    from dagster._core.definitions import asset_selection as asset_selection_module

    asset_selection_subclasses = []
    for attr in dir(asset_selection_module):
        value = getattr(asset_selection_module, attr)
        if isclass(value) and issubclass(value, dg.AssetSelection):
            asset_selection_subclasses.append(value)

    assert len(asset_selection_subclasses) > 5

    for asset_selection_subclass in asset_selection_subclasses:
        if asset_selection_subclass not in [
            dg.AssetSelection,
            asset_selection_module.ChainedAssetSelection,
            asset_selection_module.OperandListAssetSelection,
        ]:
            assert asset_selection_subclass.__name__ in _WHITELIST_MAP.object_serializers


def test_to_serializable_asset_selection():
    class UnserializableAssetSelection(dg.AssetSelection):
        def resolve_inner(
            self, asset_graph: BaseAssetGraph, allow_missing: bool
        ) -> AbstractSet[dg.AssetKey]:
            return asset_graph.materializable_asset_keys - {dg.AssetKey("asset2")}

    @dg.asset
    def asset1(): ...

    @dg.asset
    def asset2(): ...

    @dg.asset_check(asset=asset1)  # pyright: ignore[reportArgumentType]
    def check1(): ...

    asset_graph = AssetGraph.from_assets([asset1, asset2, check1])

    def assert_serializable_same(asset_selection: AssetSelection) -> None:
        assert asset_selection.to_serializable_asset_selection(asset_graph) == asset_selection

    assert_serializable_same(AssetSelection.groups("a"))
    assert_serializable_same(AssetSelection.key_prefixes(["foo", "bar"]))
    assert_serializable_same(AssetSelection.all())
    assert_serializable_same(AssetSelection.all_asset_checks())
    assert_serializable_same(AssetSelection.assets("asset1"))
    assert_serializable_same(AssetSelection.checks_for_assets(asset1))
    assert_serializable_same(AssetSelection.checks(check1))

    assert_serializable_same(AssetSelection.sinks(AssetSelection.groups("a")))
    assert_serializable_same(AssetSelection.downstream(AssetSelection.groups("a"), depth=1))
    assert_serializable_same(AssetSelection.upstream(AssetSelection.groups("a"), depth=1))
    assert_serializable_same(
        AssetSelection.required_multi_asset_neighbors(AssetSelection.groups("a"))
    )
    assert_serializable_same(AssetSelection.roots(AssetSelection.groups("a")))
    assert_serializable_same(AssetSelection.sources(AssetSelection.groups("a")))
    assert_serializable_same(AssetSelection.upstream_source_assets(AssetSelection.groups("a")))

    assert_serializable_same(AssetSelection.groups("a") & AssetSelection.groups("b"))
    assert_serializable_same(AssetSelection.groups("a") | AssetSelection.groups("b"))
    assert_serializable_same(AssetSelection.groups("a") - AssetSelection.groups("b"))

    asset1_selection = AssetSelection.assets("asset1")
    assert (
        UnserializableAssetSelection().to_serializable_asset_selection(asset_graph)
        == asset1_selection
    )

    assert AssetSelection.sinks(UnserializableAssetSelection()).to_serializable_asset_selection(
        asset_graph
    ) == AssetSelection.sinks(asset1_selection)
    assert AssetSelection.downstream(
        UnserializableAssetSelection(), depth=1
    ).to_serializable_asset_selection(asset_graph) == AssetSelection.downstream(
        asset1_selection, depth=1
    )
    assert AssetSelection.upstream(
        UnserializableAssetSelection(), depth=1
    ).to_serializable_asset_selection(asset_graph) == AssetSelection.upstream(
        asset1_selection, depth=1
    )
    assert AssetSelection.required_multi_asset_neighbors(
        UnserializableAssetSelection()
    ).to_serializable_asset_selection(asset_graph) == AssetSelection.required_multi_asset_neighbors(
        asset1_selection
    )
    assert AssetSelection.roots(UnserializableAssetSelection()).to_serializable_asset_selection(
        asset_graph
    ) == AssetSelection.roots(asset1_selection)
    assert AssetSelection.sources(UnserializableAssetSelection()).to_serializable_asset_selection(
        asset_graph
    ) == AssetSelection.sources(asset1_selection)
    assert AssetSelection.upstream_source_assets(
        UnserializableAssetSelection()
    ).to_serializable_asset_selection(asset_graph) == AssetSelection.upstream_source_assets(
        asset1_selection
    )

    assert (
        UnserializableAssetSelection() & AssetSelection.groups("b")
    ).to_serializable_asset_selection(asset_graph) == (
        asset1_selection & AssetSelection.groups("b")
    )
    assert (
        UnserializableAssetSelection() | AssetSelection.groups("b")
    ).to_serializable_asset_selection(asset_graph) == (
        asset1_selection | AssetSelection.groups("b")
    )
    assert (
        UnserializableAssetSelection() - AssetSelection.groups("b")
    ).to_serializable_asset_selection(asset_graph) == (
        asset1_selection - AssetSelection.groups("b")
    )


def test_to_string_basic():
    assert str(AssetSelection.assets("foo")) == 'key:"foo"'
    assert str(AssetSelection.assets(dg.AssetKey(["foo", "bar"]))) == 'key:"foo/bar"'
    assert str(AssetSelection.assets("foo", "bar")) == 'key:"foo" or key:"bar"'
    assert (
        str(AssetSelection.assets(dg.AssetKey(["foo", "bar"]), dg.AssetKey("baz")))
        == 'key:"foo/bar" or key:"baz"'
    )

    assert str(AssetSelection.all()) == "*"

    assert str(AssetSelection.groups("marketing")) == 'group:"marketing"'
    assert (
        str(AssetSelection.groups("marketing", "finance")) == 'group:"marketing" or group:"finance"'
    )
    assert str(AssetSelection.groups()) == "group:<null>"
    assert str(AssetSelection.groups("")) == 'group:""'
    assert str(AssetSelection.kind(None)) == "kind:<null>"
    assert str(AssetSelection.kind("")) == 'kind:""'
    assert str(AssetSelection.tag("", "")) == 'tag:""'
    assert str(AssetSelection.owner(None)) == "owner:<null>"
    assert str(AssetSelection.owner("")) == 'owner:""'
    assert str(CodeLocationAssetSelection(selected_code_location=None)) == "code_location:<null>"
    assert str(ColumnAssetSelection(selected_column=None)) == "column:<null>"
    assert str(ColumnAssetSelection(selected_column="")) == 'column:""'
    assert str(ColumnTagAssetSelection(key="fake", value="")) == 'column_tag:"fake"'
    assert str(ColumnTagAssetSelection(key="", value="")) == 'column_tag:""'
    assert str(TableNameAssetSelection(selected_table_name=None)) == "table_name:<null>"
    assert str(TableNameAssetSelection(selected_table_name="")) == 'table_name:""'
    assert (
        str(ChangedInBranchAssetSelection(selected_changed_in_branch=None))
        == "changed_in_branch:<null>"
    )
    assert (
        str(ChangedInBranchAssetSelection(selected_changed_in_branch="")) == 'changed_in_branch:""'
    )
    assert AssetSelection.from_string("kind:dbt").to_selection_str() == 'kind:"dbt"'
    assert AssetSelection.from_string("owner:dbt").to_selection_str() == 'owner:"dbt"'
    assert AssetSelection.from_string("tag:foo=bar").to_selection_str() == 'tag:"foo"="bar"'
    assert AssetSelection.from_string("tag:foo").to_selection_str() == 'tag:"foo"'
    assert AssetSelection.from_string("key:prefix/thing").to_selection_str() == 'key:"prefix/thing"'
    assert (
        AssetSelection.from_string('key:"prefix/thing*"').to_selection_str()
        == 'key:"prefix/thing*"'
    )
    assert AssetSelection.from_string("column:foo").to_selection_str() == 'column:"foo"'

    with pytest.raises(DagsterInvalidAssetSelectionError):
        AssetSelection.from_string("kind: or *")


def test_to_string_binary_operators():
    foo_bar = AssetSelection.assets(dg.AssetKey(["foo", "bar"]))
    baz = AssetSelection.assets("baz")
    bork = AssetSelection.assets("bork")
    assert str(foo_bar | baz) == 'key:"foo/bar" or key:"baz"'
    assert str(foo_bar & baz) == 'key:"foo/bar" and key:"baz"'
    assert str(foo_bar - baz) == 'key:"foo/bar" and not key:"baz"'

    assert str(foo_bar | baz | bork) == 'key:"foo/bar" or key:"baz" or key:"bork"'
    assert str(foo_bar & baz & bork) == 'key:"foo/bar" and key:"baz" and key:"bork"'

    assert str((foo_bar | baz) | bork) == 'key:"foo/bar" or key:"baz" or key:"bork"'
    assert str(foo_bar | (baz | bork)) == 'key:"foo/bar" or key:"baz" or key:"bork"'
    assert str((foo_bar & baz) & bork) == 'key:"foo/bar" and key:"baz" and key:"bork"'
    assert str(foo_bar & (baz & bork)) == 'key:"foo/bar" and key:"baz" and key:"bork"'

    assert str(foo_bar | (baz & bork)) == 'key:"foo/bar" or (key:"baz" and key:"bork")'
    assert str(foo_bar & (baz | bork)) == 'key:"foo/bar" and (key:"baz" or key:"bork")'

    assert str(foo_bar - baz - bork) == '(key:"foo/bar" and not key:"baz") and not key:"bork"'
    assert str((foo_bar - baz) - bork) == '(key:"foo/bar" and not key:"baz") and not key:"bork"'
    assert str(foo_bar - (baz - bork)) == 'key:"foo/bar" and not (key:"baz" and not key:"bork")'

    assert (
        str(AssetSelection.assets("foo/bar", "baz") & AssetSelection.assets("bork"))
        == '(key:"foo/bar" or key:"baz") and key:"bork"'
    )
    assert (
        str(AssetSelection.assets("bork") & AssetSelection.assets("foo/bar", "baz"))
        == 'key:"bork" and (key:"foo/bar" or key:"baz")'
    )
    assert (
        str(AssetSelection.assets("foo/bar", "baz") | AssetSelection.assets("bork"))
        == '(key:"foo/bar" or key:"baz") or key:"bork"'
    )
    assert (
        str(AssetSelection.assets("bork") | AssetSelection.assets("foo/bar", "baz"))
        == 'key:"bork" or (key:"foo/bar" or key:"baz")'
    )

    assert (
        str(AssetSelection.groups("foo", "bar") & AssetSelection.groups("baz", "bork"))
        == '(group:"foo" or group:"bar") and (group:"baz" or group:"bork")'
    )


def test_empty_namedtuple_truthy():
    # namedtuples with no fields are still truthy
    assert bool(AllAssetCheckSelection.all())


def test_deserialize_old_all_asset_selection():
    old_serialized_value = '{"__class__": "AllSelection"}'
    new_unserialized_value = dg.deserialize_value(old_serialized_value, AllSelection)
    assert not new_unserialized_value.include_sources


def test_from_string():
    assert AssetSelection.from_string("*") == AssetSelection.all(include_sources=False)
    assert AssetSelection.from_string("my_asset") == AssetSelection.assets("my_asset")
    assert AssetSelection.from_string("*my_asset") == AssetSelection.assets("my_asset").upstream(
        depth=MAX_NUM, include_self=True
    )
    assert AssetSelection.from_string("+my_asset") == AssetSelection.assets("my_asset").upstream(
        depth=1, include_self=True
    )
    assert AssetSelection.from_string("++my_asset") == AssetSelection.assets("my_asset").upstream(
        depth=2, include_self=True
    )
    assert AssetSelection.from_string("my_asset*") == AssetSelection.assets("my_asset").downstream(
        depth=MAX_NUM, include_self=True
    )
    assert AssetSelection.from_string("my_asset+") == AssetSelection.assets("my_asset").downstream(
        depth=1, include_self=True
    )
    assert AssetSelection.from_string("my_asset++") == AssetSelection.assets("my_asset").downstream(
        depth=2, include_self=True
    )
    assert AssetSelection.from_string("+my_asset+") == AssetSelection.assets("my_asset").downstream(
        depth=1, include_self=True
    ) | AssetSelection.assets("my_asset").upstream(depth=1, include_self=True)
    assert AssetSelection.from_string("*my_asset*") == AssetSelection.assets("my_asset").downstream(
        depth=MAX_NUM, include_self=True
    ) | AssetSelection.assets("my_asset").upstream(depth=MAX_NUM, include_self=True)
    assert AssetSelection.from_string("tag:foo=bar") == AssetSelection.tag("foo", "bar")
    assert AssetSelection.from_string("tag:foo") == AssetSelection.tag("foo", "")
    assert AssetSelection.from_string("key:prefix/thing") == KeyWildCardAssetSelection(
        selected_key_wildcard="prefix/thing"
    )
    assert AssetSelection.from_string('key:"prefix/thing*"') == KeyWildCardAssetSelection(
        selected_key_wildcard="prefix/thing*"
    )


def test_tag():
    @dg.multi_asset(
        specs=[
            dg.AssetSpec("asset1", tags={"foo": "fooval"}),
            dg.AssetSpec("asset2", tags={"foo": "fooval2"}),
            dg.AssetSpec("asset3", tags={"foo": "fooval", "bar": "barval"}),
            dg.AssetSpec("asset4", tags={"bar": "barval"}),
        ]
    )
    def assets(): ...

    assert AssetSelection.tag("foo", "fooval").resolve([assets]) == {
        dg.AssetKey(k) for k in ["asset1", "asset3"]
    }
    assert AssetSelection.tag("foo", "").resolve([assets]) == set()


def test_tag_string():
    @dg.multi_asset(
        specs=[
            dg.AssetSpec("asset1", tags={"foo": "fooval"}),
            dg.AssetSpec("asset2", tags={"foo": "fooval2"}),
            dg.AssetSpec("asset3", tags={"foo": "fooval", "bar": "barval"}),
            dg.AssetSpec("asset4", tags={"bar": "barval"}),
            dg.AssetSpec("asset5", tags={"baz": ""}),
            dg.AssetSpec("asset6", tags={"baz": "", "bar": "barval"}),
        ]
    )
    def assets(): ...

    assert AssetSelection.tag_string("foo=fooval").resolve([assets]) == {
        dg.AssetKey("asset1"),
        dg.AssetKey("asset3"),
    }
    assert AssetSelection.tag_string("foo").resolve([assets]) == set()
    assert AssetSelection.tag_string("baz").resolve([assets]) == {
        dg.AssetKey("asset5"),
        dg.AssetKey("asset6"),
    }


def test_key_wildcard():
    @dg.multi_asset(
        specs=[
            dg.AssetSpec("asset1"),
            dg.AssetSpec("asset2"),
            dg.AssetSpec("asset3"),
            dg.AssetSpec("asset4"),
            dg.AssetSpec(["prefix", "asset1"]),
            dg.AssetSpec(["prefix", "asset2"]),
            dg.AssetSpec(["prefix", "asset3"]),
        ]
    )
    def assets(): ...

    assert KeyWildCardAssetSelection(selected_key_wildcard="asset").resolve([assets]) == set()

    assert KeyWildCardAssetSelection(selected_key_wildcard="asset1").resolve([assets]) == {
        dg.AssetKey("asset1"),
    }

    assert KeyWildCardAssetSelection(selected_key_wildcard="prefix/*").resolve([assets]) == {
        dg.AssetKey(["prefix", "asset1"]),
        dg.AssetKey(["prefix", "asset2"]),
        dg.AssetKey(["prefix", "asset3"]),
    }

    assert KeyWildCardAssetSelection(selected_key_wildcard="*/asset*").resolve([assets]) == {
        dg.AssetKey(["prefix", "asset1"]),
        dg.AssetKey(["prefix", "asset2"]),
        dg.AssetKey(["prefix", "asset3"]),
    }


def test_owner() -> None:
    @dg.multi_asset(
        specs=[
            dg.AssetSpec("asset1", owners=["owner1@owner.com"]),
            dg.AssetSpec("asset2", owners=["owner2@owner.com"]),
            dg.AssetSpec("asset3", owners=["owner1@owner.com"]),
            dg.AssetSpec("asset4", owners=["owner2@owner.com"]),
        ]
    )
    def assets(): ...

    assert AssetSelection.owner("owner1@owner.com").resolve([assets]) == {
        dg.AssetKey("asset1"),
        dg.AssetKey("asset3"),
    }


def test_kind() -> None:
    @dg.multi_asset(
        specs=[
            dg.AssetSpec("asset1", kinds={"my_kind"}),
            dg.AssetSpec("asset2", kinds={""}),
            dg.AssetSpec("asset3"),
        ]
    )
    def assets(): ...

    assert AssetSelection.kind("my_kind").resolve([assets]) == {
        dg.AssetKey("asset1"),
    }
    assert AssetSelection.kind("").resolve([assets]) == {
        dg.AssetKey("asset2"),
    }
    assert AssetSelection.kind(None).resolve([assets]) == {
        dg.AssetKey("asset3"),
    }


def test_code_location() -> None:
    @dg.asset
    def my_asset(): ...

    defs = dg.Definitions(assets=[my_asset])

    # Selection can be instantiated.
    selection = CodeLocationAssetSelection(selected_code_location="code_location1")

    # But not resolved.
    with pytest.raises(CheckError):
        selection.resolve([my_asset])

    # A RemoteRepositoryAssetGraph can resolve it though
    repo_handle = RepositoryHandle.for_test(
        location_name="code_location1",
        repository_name="bar_repo",
    )
    remote_repo = RemoteRepository(
        RepositorySnap.from_def(
            defs.get_repository_def(),
        ),
        repository_handle=repo_handle,
        auto_materialize_use_sensors=True,
    )

    assert selection.resolve_inner(
        remote_repo.asset_graph,
        allow_missing=False,
    ) == {dg.AssetKey("my_asset")}

    other_repo_handle = RepositoryHandle.for_test(
        location_name="code_location2",
        repository_name="bar_repo",
    )
    other_remote_repo = RemoteRepository(
        RepositorySnap.from_def(
            defs.get_repository_def(),
        ),
        repository_handle=other_repo_handle,
        auto_materialize_use_sensors=True,
    )

    assert (
        selection.resolve_inner(
            other_remote_repo.asset_graph,
            allow_missing=False,
        )
        == set()
    )

    selection = CodeLocationAssetSelection(selected_code_location="bar_repo@code_location1")
    assert selection.resolve_inner(
        remote_repo.asset_graph,
        allow_missing=False,
    ) == {dg.AssetKey("my_asset")}


def test_column() -> None:
    @dg.asset
    def my_asset(): ...

    # Selection can be instantiated.
    selection = ColumnAssetSelection(selected_column="column1")

    # But not resolved.
    with pytest.raises(NotImplementedError):
        selection.resolve([my_asset])


def test_status() -> None:
    @dg.asset
    def my_asset(): ...

    # Selection can be instantiated.
    selection = StatusAssetSelection(selected_status="healthy")

    # But not resolved.
    with pytest.raises(NotImplementedError):
        selection.resolve([my_asset])


def test_table_name() -> None:
    @dg.asset
    def my_asset(): ...

    # Selection can be instantiated.
    selection = TableNameAssetSelection(selected_table_name="table_name1")

    # But not resolved.
    with pytest.raises(NotImplementedError):
        selection.resolve([my_asset])


def test_column_tag() -> None:
    @dg.asset
    def my_asset(): ...

    # Selection can be instantiated.
    selection = ColumnTagAssetSelection(key="key1", value="value1")

    # But not resolved.
    with pytest.raises(NotImplementedError):
        selection.resolve([my_asset])


def test_changed_in_branch() -> None:
    @dg.asset
    def my_asset(): ...

    # Selection can be instantiated.
    selection = ChangedInBranchAssetSelection(selected_changed_in_branch="branch1")

    # But not resolved.
    with pytest.raises(NotImplementedError):
        selection.resolve([my_asset])
