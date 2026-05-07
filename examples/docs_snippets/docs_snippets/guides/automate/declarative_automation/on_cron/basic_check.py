import dagster as dg


@dg.asset_check(
    asset="upstream",
    automation_condition=dg.AutomationCondition.on_cron("@hourly"),
)
def on_cron_asset_check() -> dg.AssetCheckResult: ...
