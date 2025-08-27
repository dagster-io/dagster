import dagster as dg
from dagster._core.definitions.resolved_asset_deps import resolve_assets_def_deps


def test_same_name_twice_and_downstream():
    @dg.asset(name="apple", key_prefix="a")
    def asset1(): ...

    @dg.asset(name="apple", key_prefix="b")
    def asset2(): ...

    @dg.asset(ins={"apple": dg.AssetIn(key_prefix="a")})
    def asset3(apple):
        del apple

    assert len(resolve_assets_def_deps([asset1, asset2, asset3], [])) == 0


def test_multi_asset_group_name():
    @dg.asset(group_name="somegroup", key_prefix=["some", "path"])
    def upstream():
        pass

    @dg.multi_asset(group_name="somegroup", outs={"a": dg.AssetOut(), "b": dg.AssetOut()})
    def multi_downstream(upstream):
        pass

    resolved = resolve_assets_def_deps([upstream, multi_downstream], [])
    assert len(resolved) == 1

    resolution = next(iter(resolved.values()))
    assert resolution == {dg.AssetKey(["upstream"]): dg.AssetKey(["some", "path", "upstream"])}


def test_input_has_asset_key():
    @dg.asset(key_prefix="a")
    def asset1(): ...

    @dg.asset(deps=[dg.AssetKey(["b", "asset1"])])
    def asset2(): ...

    assert len(resolve_assets_def_deps([asset1, asset2], [])) == 0


def test_upstream_same_name_as_asset():
    @dg.asset(deps=[dg.AssetKey("asset1")], key_prefix="b")
    def asset1(): ...

    assert len(resolve_assets_def_deps([asset1], [])) == 0

    @dg.multi_asset(
        outs={"asset1": dg.AssetOut(key_prefix="b")}, deps=[dg.AssetKey(["a", "asset1"])]
    )
    def multi_asset1(): ...

    assert len(resolve_assets_def_deps([multi_asset1], [])) == 0
