import dagster as dg

daily_success_condition = dg.AutomationCondition.newly_updated().since(
    dg.AutomationCondition.on_cron("*/5 * * * *")
)

condition = (
    dg.AutomationCondition.on_cron("*/5 * * * *")  # Runs at 9 AM daily
    | (
        dg.AutomationCondition.any_deps_updated()  # When any dependency updates
        & daily_success_condition  # Only if asset was updated since daily cron
        # .since(dg.AutomationCondition.on_cron("* * * * *"))  # Only after the daily cron
        & ~dg.AutomationCondition.any_deps_missing()  # But not if deps are missing
        & ~dg.AutomationCondition.any_deps_in_progress()  # And not if deps are in progress
    )
)
