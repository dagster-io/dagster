import dagster as dg

daily_success_condition = dg.AutomationCondition.newly_updated().since(
    dg.AutomationCondition.on_cron("*/5 * * * *")
)

custom_condition = (
    dg.AutomationCondition.on_cron("*/5 * * * *")  # Runs every 5 minutes
    | (
        dg.AutomationCondition.any_deps_updated()  # When any dependency updates
        & daily_success_condition  # Only if asset was updated since daily cron
        & ~dg.AutomationCondition.any_deps_missing()  # But not if deps are missing
        & ~dg.AutomationCondition.any_deps_in_progress()  # And not if deps are in progress
    )
)


@dg.asset
def upstream_asset_1(): ...


@dg.asset
def upstream_asset_2(): ...


@dg.asset(
    automation_condition=custom_condition, deps=["upstream_asset_1", "upstream_asset_2"]
)
def automation_condition_combination(context: dg.AssetExecutionContext): ...
