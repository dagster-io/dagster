import dagster as dg
import pytest
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.definitions.resolved_asset_deps import resolve_assets_def_deps
from dagster._core.errors import DagsterInvalidDefinitionError


def test_same_name_twice_and_downstream():
    @dg.asset(name="apple", key_prefix="a")
    def asset1(): ...

    @dg.asset(name="apple", key_prefix="b")
    def asset2(): ...

    @dg.asset(ins={"apple": dg.AssetIn(key_prefix="a")})
    def asset3(apple):
        del apple

    assets = [asset1, asset2, asset3]
    resolved_assets = resolve_assets_def_deps(assets)
    assert resolved_assets == assets


def test_multi_asset_group_name():
    @dg.asset(group_name="somegroup", key_prefix=["some", "path"])
    def upstream():
        pass

    @dg.multi_asset(group_name="somegroup", outs={"a": dg.AssetOut(), "b": dg.AssetOut()})
    def multi_downstream(upstream):
        pass

    assets = [upstream, multi_downstream]
    resolved_assets = resolve_assets_def_deps(assets)
    assert resolved_assets != assets

    for spec in resolved_assets[1].specs:
        deps = list(spec.deps)
        assert len(deps) == 1
        # should have been remapped
        assert deps[0].asset_key == dg.AssetKey(["some", "path", "upstream"])


def test_input_has_asset_key():
    @dg.asset(key_prefix="a")
    def asset1(): ...

    @dg.asset(deps=[dg.AssetKey(["b", "asset1"])])
    def asset2(): ...

    assets = [asset1, asset2]
    resolved_assets = resolve_assets_def_deps(assets)
    assert resolved_assets == assets


def test_upstream_same_name_as_asset():
    @dg.asset(deps=[dg.AssetKey("asset1")], key_prefix="b")
    def asset1(): ...

    assert resolve_assets_def_deps([asset1]) == [asset1]

    @dg.multi_asset(
        outs={"asset1": dg.AssetOut(key_prefix="b")}, deps=[dg.AssetKey(["a", "asset1"])]
    )
    def multi_asset1(): ...

    assert resolve_assets_def_deps([multi_asset1]) == [multi_asset1]


def test_table_name_match():
    @dg.asset(
        key=dg.AssetKey(["foo", "bar", "baz"]),
        metadata={**TableMetadataSet(table_name="foo.bar.baz")},
    )
    def asset1(): ...

    @dg.asset(
        deps=[dg.AssetDep("blah", metadata={**TableMetadataSet(table_name="foo.bar.baz")})],
    )
    def asset2(): ...

    assets = [asset1, asset2]
    resolved_assets = resolve_assets_def_deps(assets)
    assert resolved_assets != assets

    for spec in resolved_assets[1].specs:
        deps = list(spec.deps)
        assert len(deps) == 1
        # should have been remapped
        assert deps[0].asset_key == dg.AssetKey(["foo", "bar", "baz"])


def test_table_name_match_with_key_prefix():
    @dg.asset(
        key_prefix=["schema", "tables"],
        metadata={**TableMetadataSet(table_name="schema.tables.users")},
    )
    def users(): ...

    @dg.asset(
        deps=[
            dg.AssetDep("unknown", metadata={**TableMetadataSet(table_name="schema.tables.users")})
        ],
    )
    def downstream(unknown):
        del unknown

    assets = [users, downstream]
    resolved_assets = resolve_assets_def_deps(assets)
    assert resolved_assets != assets

    for spec in resolved_assets[1].specs:
        deps = list(spec.deps)
        assert len(deps) == 1
        assert deps[0].asset_key == dg.AssetKey(["schema", "tables", "users"])


def test_table_name_match_ambiguous_multiple_matches():
    @dg.asset(
        key=dg.AssetKey(["asset1"]),
        metadata={**TableMetadataSet(table_name="schema.table")},
    )
    def asset1(): ...

    @dg.asset(
        key=dg.AssetKey(["asset2"]),
        metadata={**TableMetadataSet(table_name="schema.table")},
    )
    def asset2(): ...

    @dg.asset(
        deps=[dg.AssetDep("unknown", metadata={**TableMetadataSet(table_name="schema.table")})],
    )
    def downstream():
        pass

    # there's ambiguity, so error
    assets = [asset1, asset2, downstream]
    with pytest.raises(DagsterInvalidDefinitionError):
        resolve_assets_def_deps(assets)


def test_table_name_match_multi_asset():
    @dg.asset(
        key=dg.AssetKey(["upstream"]),
        metadata={**TableMetadataSet(table_name="db.schema.upstream")},
    )
    def upstream(): ...

    @dg.multi_asset(
        outs={
            "output1": dg.AssetOut(metadata={**TableMetadataSet(table_name="db.schema.output1")}),
            "output2": dg.AssetOut(metadata={**TableMetadataSet(table_name="db.schema.output2")}),
        },
        deps=[
            dg.AssetDep("unknown", metadata={**TableMetadataSet(table_name="db.schema.upstream")})
        ],
    )
    def multi_downstream(unknown):
        del unknown
        return None, None

    assets = [upstream, multi_downstream]
    resolved_assets = resolve_assets_def_deps(assets)
    assert resolved_assets != assets

    for spec in resolved_assets[1].specs:
        deps = list(spec.deps)
        # Each output spec should have the dependency resolved
        matching_deps = [dep for dep in deps if dep.asset_key == dg.AssetKey(["upstream"])]
        assert len(matching_deps) == 1


def test_table_name_match_chain():
    @dg.asset(
        key=dg.AssetKey(["first"]),
        metadata={**TableMetadataSet(table_name="db.first")},
    )
    def first(): ...

    @dg.asset(
        deps=[dg.AssetDep("first_dep", metadata={**TableMetadataSet(table_name="db.first")})],
        metadata={**TableMetadataSet(table_name="db.second")},
    )
    def second(first_dep):
        del first_dep

    @dg.asset(
        deps=[dg.AssetDep("second_dep", metadata={**TableMetadataSet(table_name="db.second")})],
    )
    def third(second_dep):
        del second_dep

    assets = [first, second, third]
    resolved_assets = resolve_assets_def_deps(assets)
    assert resolved_assets != assets

    # Check second asset
    for spec in resolved_assets[1].specs:
        deps = list(spec.deps)
        assert len(deps) == 1
        assert deps[0].asset_key == dg.AssetKey(["first"])

    # Check third asset
    for spec in resolved_assets[2].specs:
        deps = list(spec.deps)
        assert len(deps) == 1
        assert deps[0].asset_key == dg.AssetKey(["second"])
