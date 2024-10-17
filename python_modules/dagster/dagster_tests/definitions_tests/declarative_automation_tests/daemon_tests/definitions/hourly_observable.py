import dagster as dg


@dg.observable_source_asset(automation_condition=dg.AutomationCondition.on_cron("@hourly"))
def obs() -> None: ...


@dg.asset(deps=[obs], automation_condition=dg.AutomationCondition.on_cron("@hourly"))
def mat() -> None: ...


defs = dg.Definitions(assets=[obs, mat])
