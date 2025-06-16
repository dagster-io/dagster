import dagster as dg

condition = dg.AutomationCondition.on_missing().replace(
    "handled",
    dg.AutomationCondition.newly_requested() | dg.AutomationCondition.newly_updated(),
)
