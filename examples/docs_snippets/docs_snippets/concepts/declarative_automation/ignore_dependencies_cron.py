import dagster as dg

all_deps_except_foo_updated = dg.AutomationCondition.all_deps_updated_since_cron(
    "@hourly"
).ignore(dg.AssetSelection.assets("foo"))

condition = (
    dg.AutomationCondition.on_cron("@hourly").without(
        dg.AutomationCondition.all_deps_updated_since_cron("@hourly")
    )
) & all_deps_except_foo_updated
