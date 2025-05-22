import dagster as dg

# detects if the latest run of the target was executed via an automation condition
executed_via_condition = dg.AutomationCondition.executed_with_tags(
    tag_values={"dagster/from_automation_condition": "true"}
)

condition = dg.AutomationCondition.eager().replace(
    "newly_updated",
    dg.AutomationCondition.newly_updated() & executed_via_condition,
)
