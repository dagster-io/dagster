from dagster import (
    AssetCheckKey,
    AssetCheckResult,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    AssetOut,
    Output,
    load_assets_from_current_module,
    materialize,
    multi_asset,
)


@multi_asset(
    outs={"my_asset": AssetOut()},
    check_specs=[AssetCheckSpec(name="my_check", asset="my_asset")],
)
def my_multi(context: AssetExecutionContext):
    assert context.selected_asset_keys == {AssetKey(["foo", "my_asset"])}
    assert context.selected_asset_check_keys == {
        AssetCheckKey(asset_key=AssetKey(["foo", "my_asset"]), name="my_check")
    }
    assert (
        context.assets_def.keys_by_output_name
        == context.assets_def.node_keys_by_output_name
        == {"my_asset": AssetKey(["foo", "my_asset"])}
    )
    assert (
        context.assets_def.check_specs_by_output_name
        == context.assets_def.node_check_specs_by_output_name
        == {
            "my_asset_my_check": AssetCheckSpec(
                name="my_check", asset=AssetKey(["foo", "my_asset"])
            )
        }
    )
    yield Output(1, output_name="my_asset")
    yield AssetCheckResult(passed=True)


def test_asset():
    materialize(load_assets_from_current_module(key_prefix="foo"))  # type: ignore
