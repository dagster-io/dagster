import dagster as dg

condition = dg.AutomationCondition.on_cron("@hourly").ignore(
    dg.AssetSelection.assets("foo")
)
