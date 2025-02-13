import dagster as dg


@dg.asset(automation_condition=~dg.AutomationCondition.in_progress())
def always() -> None: ...


defs = dg.Definitions(assets=[always])
