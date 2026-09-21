import dagster as dg

condition = (
    dg.AutomationCondition.on_cron("@hourly")
    & dg.AutomationCondition.all_deps_blocking_checks_passed()
)
