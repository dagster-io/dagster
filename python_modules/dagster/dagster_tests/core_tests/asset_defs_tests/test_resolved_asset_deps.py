from dagster import AssetIn, asset
from dagster._core.definitions.resolved_asset_deps import resolve_assets_def_deps


def test_same_name_twice_and_downstream():
    @asset(name="apple", key_prefix="a")
    def asset1():
        ...

    @asset(name="apple", key_prefix="b")
    def asset2():
        ...

    @asset(ins={"apple": AssetIn(key_prefix="a")})
    def asset3(apple):
        del apple

    assert len(resolve_assets_def_deps([asset1, asset2, asset3], [])) == 0
