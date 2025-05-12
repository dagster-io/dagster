import datetime

import dagster as dg

# no limit on how far back to check for missing partitions
all_partitions_condition = dg.AutomationCondition.on_missing().without(
    dg.AutomationCondition.in_latest_time_window()
)

# limit to the last 7 days
recent_partitions_condition = dg.AutomationCondition.on_missing().replace(
    dg.AutomationCondition.in_latest_time_window(),
    dg.AutomationCondition.in_latest_time_window(datetime.timedelta(days=7)),
)
