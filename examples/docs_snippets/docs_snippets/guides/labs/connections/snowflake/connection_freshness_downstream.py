import dagster as dg


@dg.asset(
    deps=[dg.AssetKey(["snowflake_analytics", "PROD", "RAW", "EVENTS"])],
    automation_condition=dg.AutomationCondition.eager(),
)
def cleaned_events(): ...
