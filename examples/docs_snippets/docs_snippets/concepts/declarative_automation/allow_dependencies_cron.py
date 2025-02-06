import dagster as dg

condition = dg.AutomationCondition.on_cron("@hourly").allow(
    dg.AssetSelection.groups("abc")
)
