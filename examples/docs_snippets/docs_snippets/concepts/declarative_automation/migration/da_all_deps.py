import dagster as dg


@dg.asset(
    deps=["asset_a", "asset_b"],
    automation_condition=dg.AutomationCondition.on_cron("0 * * * *"),
)
def downstream(): ...
