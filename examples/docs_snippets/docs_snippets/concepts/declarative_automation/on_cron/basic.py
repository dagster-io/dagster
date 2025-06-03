import dagster as dg


@dg.asset(
    deps=["upstream"],
    automation_condition=dg.AutomationCondition.on_cron("@hourly"),
)
def hourly_asset() -> None: ...
