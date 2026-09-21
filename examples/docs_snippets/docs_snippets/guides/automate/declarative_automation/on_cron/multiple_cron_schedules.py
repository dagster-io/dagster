import dagster as dg

NINE_AM_CRON = "0 9 * * *"

condition = dg.AutomationCondition.on_cron(NINE_AM_CRON).replace(
    old=dg.AutomationCondition.all_deps_updated_since_cron(NINE_AM_CRON),
    new=dg.AutomationCondition.all_deps_updated_since_cron("0 0 * * *"),
)
