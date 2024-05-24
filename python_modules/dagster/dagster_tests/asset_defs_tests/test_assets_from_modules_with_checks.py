from dagster import (
    AssetCheckResult,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    Output,
    asset,
    load_assets_from_current_module,
    materialize,
)


@asset(check_specs=[AssetCheckSpec(name="my_check", asset="my_asset")])
def my_asset(context: AssetExecutionContext):
    yield Output("foo")
    yield AssetCheckResult(passed=True)


def test_load():
    assets = load_assets_from_current_module()

    assert len(assets) == 1
    assert assets[0].key == AssetKey(["my_asset"])
    assert len(assets[0].check_specs) == 1
    assert next(iter(assets[0].check_specs)).asset_key == AssetKey(["my_asset"])


def test_materialize():
    result = materialize(load_assets_from_current_module())

    assert len(result.get_asset_materialization_events()) == 1
    assert result.get_asset_materialization_events()[0].asset_key == AssetKey(["my_asset"])
    assert len(result.get_asset_check_evaluations()) == 1
    assert result.get_asset_check_evaluations()[0].asset_key == AssetKey(["my_asset"])


def test_prefix_load():
    assets = load_assets_from_current_module(key_prefix="foo")

    assert len(assets) == 1
    assert assets[0].key == AssetKey(["foo", "my_asset"])
    assert len(assets[0].check_specs) == 1
    assert next(iter(assets[0].check_specs)).asset_key == AssetKey(["foo", "my_asset"])


def test_prefix_materialize():
    result = materialize(load_assets_from_current_module(key_prefix="foo"))

    assert len(result.get_asset_materialization_events()) == 1
    assert result.get_asset_materialization_events()[0].asset_key == AssetKey(["foo", "my_asset"])
    assert len(result.get_asset_check_evaluations()) == 1
    assert result.get_asset_check_evaluations()[0].asset_key == AssetKey(["foo", "my_asset"])
