from dagster import (
    AssetCheckKey,
    AssetCheckResult,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    AssetSpec,
    MaterializeResult,
    multi_asset,
)


@multi_asset(
    specs=[
        AssetSpec("multi_asset_piece_1", group_name="asset_checks", skippable=True),
        AssetSpec("multi_asset_piece_2", group_name="asset_checks", skippable=True),
    ],
    check_specs=[AssetCheckSpec("my_check", asset="multi_asset_piece_1")],
    can_subset=True,
)
def multi_asset_1_and_2(context: AssetExecutionContext):
    if AssetKey("multi_asset_piece_1") in context.selected_asset_keys:
        yield MaterializeResult(asset_key="multi_asset_piece_1")
    # The check will only execute when multi_asset_piece_1 is materialized
    if (
        AssetCheckKey(AssetKey("multi_asset_piece_1"), "my_check")
        in context.selected_asset_check_keys
    ):
        yield AssetCheckResult(passed=True, metadata={"foo": "bar"})
    if AssetKey("multi_asset_piece_2") in context.selected_asset_keys:
        # No check on multi_asset_piece_2
        yield MaterializeResult(asset_key="multi_asset_piece_2")
