import dagster as dg

eager_version_aware = dg.AutomationCondition.eager().replace(
    "newly_updated",
    dg.AutomationCondition.data_version_changed(),
)
