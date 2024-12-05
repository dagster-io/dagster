from datetime import timedelta

from dagster import AutomationCondition

five_days_ago_condition = AutomationCondition.in_latest_time_window(
    timedelta(days=5)
) & ~AutomationCondition.in_latest_time_window(timedelta(days=4))

condition = five_days_ago_condition & AutomationCondition.eager().without(
    AutomationCondition.in_latest_time_window(),
)
