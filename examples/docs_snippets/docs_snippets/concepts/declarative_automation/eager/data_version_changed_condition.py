import dagster as dg

condition = dg.AutomationCondition.eager().replace(
    "any_deps_updated",
    dg.AutomationCondition.any_deps_updated().replace(
        "newly_updated", dg.AutomationCondition.data_version_changed()
    ),
)
