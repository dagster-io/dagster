import dagster as dg

condition = dg.AutomationCondition.eager().without(
    dg.AutomationCondition.in_latest_time_window(),
)
