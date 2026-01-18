from datetime import timedelta

import dagster as dg

five_days_ago_condition = dg.AutomationCondition.in_latest_time_window(
    timedelta(days=5)
) & ~dg.AutomationCondition.in_latest_time_window(timedelta(days=4))

condition = dg.AutomationCondition.on_cron("@daily").replace(
    "in_latest_time_window", five_days_ago_condition
)
