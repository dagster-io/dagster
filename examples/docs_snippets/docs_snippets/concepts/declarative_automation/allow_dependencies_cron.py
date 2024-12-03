import dagster as dg

group_abc_updated = dg.AutomationCondition.all_deps_updated_since_cron("@hourly").allow(
    dg.AssetSelection.groups("abc")
)

condition = (
    dg.AutomationCondition.on_cron("@hourly").without(
        dg.AutomationCondition.all_deps_updated_since_cron("@hourly")
    )
) & group_abc_updated
