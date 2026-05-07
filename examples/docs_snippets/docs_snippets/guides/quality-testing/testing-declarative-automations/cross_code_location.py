import dagster as dg

external_upstream = dg.AssetSpec(key="external_upstream")


@dg.asset(
    deps=[external_upstream],
    automation_condition=dg.AutomationCondition.eager(),
)
def my_asset(): ...


def test_cross_location_condition():
    instance = dg.DagsterInstance.ephemeral()

    result = dg.evaluate_automation_conditions(
        defs=[external_upstream, my_asset], instance=instance
    )
    assert result.total_requested == 0

    instance.report_runless_asset_event(
        dg.AssetMaterialization(asset_key="external_upstream")
    )

    result = dg.evaluate_automation_conditions(
        defs=[external_upstream, my_asset], instance=instance, cursor=result.cursor
    )
    assert result.total_requested == 1

    result = dg.evaluate_automation_conditions(
        defs=[external_upstream, my_asset], instance=instance, cursor=result.cursor
    )
    assert result.total_requested == 0
