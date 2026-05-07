import dagster as dg


@dg.asset(
    deps=["raw_data"],
    automation_condition=dg.AutomationCondition.eager(),
)
def downstream(): ...
