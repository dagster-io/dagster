from dagster import (
    AssetExecutionContext,
    AssetOut,
    HookContext,
    failure_hook,
    materialize,
    multi_asset,
    success_hook,
)


# Define hooks
@success_hook
def success_hook_fn(context: HookContext):
    context.log.info(f"Success hook triggered for {context.op.name}")


@failure_hook
def failure_hook_fn(context: HookContext):
    context.log.info(f"Failure hook triggered for {context.op.name}")


# Test function
def test_multi_asset_with_hooks():
    @multi_asset(
        outs={
            "asset1": AssetOut(),
            "asset2": AssetOut(),
        },
        hooks={success_hook_fn, failure_hook_fn},
    )
    def my_multi_asset(context: AssetExecutionContext):
        return 1, 2

    # Materialize the multi-asset and verify hooks
    result = materialize([my_multi_asset])
    assert result.success

    # Verify that the success hook was triggered
    hook_completed = [
        event.event_type
        for event in result.all_events
        if "HOOK_COMPLETED" == event.event_type_value
    ]
    assert len(hook_completed) == 1
    hook_skipped = [
        event.event_type for event in result.all_events if "HOOK_SKIPPED" == event.event_type_value
    ]
    assert len(hook_skipped) == 1


test_multi_asset_with_hooks()
