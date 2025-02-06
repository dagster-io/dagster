from datetime import timedelta

from dagster import AutomationCondition

five_days_ago_condition = AutomationCondition.in_latest_time_window(
    timedelta(days=5)
) & ~AutomationCondition.in_latest_time_window(timedelta(days=4))

condition = AutomationCondition.on_cron("@daily").replace(
    "in_latest_time_window", five_days_ago_condition
)
