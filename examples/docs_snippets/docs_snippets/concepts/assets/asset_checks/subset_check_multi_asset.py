from dagster import (
    AssetCheckKey,
    AssetCheckResult,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    AssetOut,
    Output,
    multi_asset,
)


@multi_asset(
    outs={
        "one": AssetOut(
            key="multi_asset_piece_1", group_name="asset_checks", is_required=False
        ),
        "two": AssetOut(
            key="multi_asset_piece_2", group_name="asset_checks", is_required=False
        ),
    },
    check_specs=[AssetCheckSpec("my_check", asset="multi_asset_piece_1")],
    can_subset=True,
)
def multi_asset_1_and_2(context: AssetExecutionContext):
    if AssetKey("multi_asset_piece_1") in context.selected_asset_keys:
        yield Output(1, output_name="one")
    if (
        AssetCheckKey(AssetKey("multi_asset_piece_1"), "my_check")
        in context.selected_asset_check_keys
    ):
        yield AssetCheckResult(passed=True, metadata={"foo": "bar"})
    if AssetKey("multi_asset_piece_2") in context.selected_asset_keys:
        yield Output(1, output_name="two")
