import dagster as dg


@dg.asset_check(
    asset="upstream",
    automation_condition=dg.AutomationCondition.eager(),
)
def eager_asset_check() -> dg.AssetCheckResult: ...
