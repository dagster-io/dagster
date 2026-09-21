import dagster as dg

condition = (
    dg.AutomationCondition.eager()
    & dg.AutomationCondition.all_deps_blocking_checks_passed()
)
