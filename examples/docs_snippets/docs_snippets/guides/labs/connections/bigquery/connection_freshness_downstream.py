import dagster as dg


@dg.asset(
    deps=[dg.AssetKey(["bigquery_analytics", "my-project", "raw", "events"])],
    automation_condition=dg.AutomationCondition.eager(),
)
def cleaned_events(): ...
