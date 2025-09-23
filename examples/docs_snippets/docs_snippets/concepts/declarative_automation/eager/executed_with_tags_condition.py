import dagster as dg

# detects if any of the new updates of the target was executed via an automation condition
executed_via_condition = dg.AutomationCondition.any_new_update_has_run_tags(
    tag_values={"dagster/from_automation_condition": "true"}
)

condition = dg.AutomationCondition.eager().replace(
    "newly_updated",
    dg.AutomationCondition.newly_updated() & executed_via_condition,
)
