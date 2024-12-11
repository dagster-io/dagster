from dagster import AutomationCondition

condition = AutomationCondition.eager().without(
    AutomationCondition.in_latest_time_window(),
)
