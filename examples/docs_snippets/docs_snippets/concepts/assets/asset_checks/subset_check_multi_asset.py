import dagster as dg


@dg.multi_asset(
    specs=[
        dg.AssetSpec("multi_asset_piece_1", group_name="asset_checks", skippable=True),
        dg.AssetSpec("multi_asset_piece_2", group_name="asset_checks", skippable=True),
    ],
    check_specs=[dg.AssetCheckSpec("my_check", asset="multi_asset_piece_1")],
    can_subset=True,
)
def multi_asset_1_and_2(context: dg.AssetExecutionContext):
    if dg.AssetKey("multi_asset_piece_1") in context.selected_asset_keys:
        yield dg.MaterializeResult(asset_key="multi_asset_piece_1")
    # The check will only execute when multi_asset_piece_1 is materialized
    if (
        dg.AssetCheckKey(dg.AssetKey("multi_asset_piece_1"), "my_check")
        in context.selected_asset_check_keys
    ):
        yield dg.AssetCheckResult(passed=True, metadata={"foo": "bar"})
    if dg.AssetKey("multi_asset_piece_2") in context.selected_asset_keys:
        # No check on multi_asset_piece_2
        yield dg.MaterializeResult(asset_key="multi_asset_piece_2")
