import dagster as dg
from dagster import AssetExecutionContext


@dg.asset(check_specs=[dg.AssetCheckSpec(name="my_check", asset="my_asset")])
def my_asset(context: AssetExecutionContext):
    yield dg.Output("foo")
    yield dg.AssetCheckResult(passed=True)


def test_load():
    assets = dg.load_assets_from_current_module()

    assert len(assets) == 1
    assert assets[0].key == dg.AssetKey(["my_asset"])  # ty: ignore[unresolved-attribute]
    assert len(assets[0].check_specs) == 1  # ty: ignore[invalid-argument-type,unresolved-attribute]
    assert next(iter(assets[0].check_specs)).asset_key == dg.AssetKey(["my_asset"])  # ty: ignore[unresolved-attribute]


def test_materialize():
    result = dg.materialize(dg.load_assets_from_current_module())  # ty: ignore[invalid-argument-type]

    assert len(result.get_asset_materialization_events()) == 1
    assert result.get_asset_materialization_events()[0].asset_key == dg.AssetKey(["my_asset"])
    assert len(result.get_asset_check_evaluations()) == 1
    assert result.get_asset_check_evaluations()[0].asset_key == dg.AssetKey(["my_asset"])


def test_prefix_load():
    assets = dg.load_assets_from_current_module(key_prefix="foo")

    assert len(assets) == 1
    assert assets[0].key == dg.AssetKey(["foo", "my_asset"])  # ty: ignore[unresolved-attribute]
    assert len(assets[0].check_specs) == 1  # ty: ignore[invalid-argument-type,unresolved-attribute]
    assert next(iter(assets[0].check_specs)).asset_key == dg.AssetKey(["foo", "my_asset"])  # ty: ignore[unresolved-attribute]


def test_prefix_materialize():
    result = dg.materialize(dg.load_assets_from_current_module(key_prefix="foo"))  # ty: ignore[invalid-argument-type]

    assert len(result.get_asset_materialization_events()) == 1
    assert result.get_asset_materialization_events()[0].asset_key == dg.AssetKey(
        ["foo", "my_asset"]
    )
    assert len(result.get_asset_check_evaluations()) == 1
    assert result.get_asset_check_evaluations()[0].asset_key == dg.AssetKey(["foo", "my_asset"])
