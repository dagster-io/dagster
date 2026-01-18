import dagster as dg

condition = (
    dg.AutomationCondition.on_missing()
    & dg.AutomationCondition.all_deps_blocking_checks_passed()
)
